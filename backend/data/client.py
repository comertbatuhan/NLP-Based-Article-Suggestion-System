# data/client.py
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter, Retry

from .config import settings


class OpenAlexError(RuntimeError):
    pass


class OpenAlexClient:
    """
    HTTP client for OpenAlex with:
      - sensible timeouts
      - retry w/ exponential backoff for 429/5xx
      - tiny helper for GETing JSON

    Usage:
        client = OpenAlexClient()
        data = client.get_json("works", {"search": "nlp", "per-page": 50})
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_s: Optional[int] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
    ) -> None:
        self.base_url = (base_url or str(settings.base_url)).rstrip("/")
        self.timeout_s = timeout_s or settings.timeout_s
        self.session = requests.Session()

        # Robust retry policy
        retry = Retry(
            total=max_retries or settings.max_retries,
            connect=max_retries or settings.max_retries,
            read=max_retries or settings.max_retries,
            backoff_factor=backoff_factor or settings.backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = dict(params or {})

        # Respect documented page size limits (1-200)
        if "per-page" in params:
            try:
                v = int(params["per-page"])
                if v < 1 or v > 200:
                    params["per-page"] = min(200, max(1, v))
            except Exception:
                params["per-page"] = settings.per_page

        url = self._url(path)
        resp = self.session.get(url, params=params, timeout=self.timeout_s)

        # Manual handling for 429 after retries exhausted: brief sleep + one last try
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "1"))
            time.sleep(min(5, max(1, retry_after)))
            resp = self.session.get(url, params=params, timeout=self.timeout_s)

        if not resp.ok:
            raise OpenAlexError(
                f"OpenAlex error {resp.status_code} for {url} with params {params}:\n{resp.text[:500]}"
            )
        try:
            return resp.json()
        except ValueError as e:
            raise OpenAlexError(f"Failed to decode JSON from OpenAlex: {e}") from e
