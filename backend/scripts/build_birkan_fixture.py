from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]  # backend/
RAW_PATH = ROOT / "scripts" / "birkan_raw.txt"
OUT_PATH = ROOT / "app" / "tests" / "fixtures" / "birkan_papers.json"


RE_BLOCK_SPLIT = re.compile(r"\n-{10,}\n")
RE_INDEX_TITLE = re.compile(r"^\s*(\d+)\.\s*(.+?)\s*$", re.MULTILINE)
RE_QUERY = re.compile(r"^\s*Query:\s*(.+?)\s*$", re.MULTILINE)
RE_YEAR = re.compile(r"^\s*Year:\s*(\d{4})\b", re.MULTILINE)
RE_KEYWORDS = re.compile(r"^\s*Keywords:\s*(.+?)\s*$", re.MULTILINE)
RE_LABEL = re.compile(r"^\s*Label:\s*(.+?)\s*$", re.MULTILINE)

# Abstract başlangıcı: "Abstract:" veya "Abstract—" veya "Abstract " ile başlayan satır
RE_ABS_START = re.compile(r"^\s*Abstract(?:\s*[:—-]\s*|\s+)(.*)\s*$", re.MULTILINE)
RE_STOP = re.compile(r"^\s*(Keywords:|Topics:|Concepts:|Label:|Note:)\s*", re.MULTILINE)


def _clean(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\r", "")
    # hocanın textinde geçen html entity kalıntıları
    s = s.replace("&#13;", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _extract_abstract(block: str) -> str:
    """
    Abstract'ı şu şekilde alıyoruz:
    - Abstract satırını bul
    - aynı satırın devamı varsa al
    - sonraki satırlardan Keywords/Topics/Concepts/Label/Note gelene kadar biriktir
    """
    m = RE_ABS_START.search(block)
    if not m:
        return ""

    start_pos = m.end()
    first_line_tail = m.group(1).strip()

    rest = block[start_pos:]
    stop_m = RE_STOP.search(rest)
    if stop_m:
        rest = rest[: stop_m.start()]

    # Abstract: satırındaki tail + rest
    combined = (first_line_tail + "\n" + rest).strip()
    return _clean(combined)


def _labels_to_list(label_line: str) -> List[str]:
    parts = [p.strip() for p in label_line.split(",")]
    return [p for p in parts if p]


def parse_block(block: str) -> Optional[Dict]:
    idx_m = RE_INDEX_TITLE.search(block)
    if not idx_m:
        return None

    index = int(idx_m.group(1))
    title = _clean(idx_m.group(2))

    query_m = RE_QUERY.search(block)
    query = _clean(query_m.group(1)) if query_m else ""

    year_m = RE_YEAR.search(block)
    publication_year = int(year_m.group(1)) if year_m else None

    kw_m = RE_KEYWORDS.search(block)
    keywords = _clean(kw_m.group(1)) if kw_m else ""

    abs_text = _extract_abstract(block)

    label_m = RE_LABEL.search(block)
    labels = _labels_to_list(label_m.group(1)) if label_m else []

    # id: stable ve unique
    pid = f"birkan:{index:02d}"

    return {
        "id": pid,
        "index": index,
        "title": title,
        "query": query,
        "publication_year": publication_year,
        "abstract": abs_text,
        "keywords": keywords,
        "labels": labels,
    }


def main():
    if not RAW_PATH.exists():
        raise SystemExit(f"Missing raw file: {RAW_PATH}")

    raw = RAW_PATH.read_text(encoding="utf-8")
    blocks = [b.strip() for b in RE_BLOCK_SPLIT.split(raw) if b.strip()]

    papers: List[Dict] = []
    for b in blocks:
        p = parse_block(b)
        if p:
            papers.append(p)

    papers = sorted(papers, key=lambda x: x["index"])

    # sanity check: abstract boş olanları raporla
    empties = [p for p in papers if not p.get("abstract")]
    if empties:
        print(f"[WARN] {len(empties)} papers have empty abstract:")
        for p in empties[:10]:
            print(f"  - {p['id']} {p['title'][:80]}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {len(papers)} papers to {OUT_PATH}")


if __name__ == "__main__":
    main()