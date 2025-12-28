# backend/app/tests/conftest.py
import csv
from pathlib import Path

def pytest_sessionfinish(session, exitstatus):
    try:
        from .test_rerank_endpoints import RESULT_ROWS
    except Exception:
        return

    if not RESULT_ROWS:
        return

    out = Path(__file__).parent / "rerank_results.csv"
    cols = ["model","variant","group","query_id","k","hit_in_top_k", "missing_in_top_k", "p_at_k","threshold","pass"]

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in RESULT_ROWS:
            w.writerow(r)

    print(f"\n[OK] Wrote rerank results CSV to: {out}\n")