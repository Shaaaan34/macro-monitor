#!/usr/bin/env python3
"""Single-command local entry point: fetch data, update history, write docs/index.html."""
from dotenv import load_dotenv

load_dotenv()

from src.dashboard import write_dashboard
from src.pipeline import run_pipeline

if __name__ == "__main__":
    result = run_pipeline()
    out_path = write_dashboard(result)
    print(f"Dashboard written to {out_path}")
    print(f"Indicators fetched: {len(result['cards'])}")
    print("What I could not verify:")
    for m in result["missing"]:
        print(f"  - {m}")
