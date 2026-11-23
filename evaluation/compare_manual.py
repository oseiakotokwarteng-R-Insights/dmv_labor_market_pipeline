"""Compares my hand-built table with what the pipeline put in the database.

I fill in evaluation/manual_workflow_log.csv and save my hand-made tables as
evaluation/manual_output_run1.csv (and run2). This script then answers:

  - How long did the manual workflow take, step by step?
  - Does my manual table match the pipeline's numbers, row by row?
  - Did my first and second manual runs agree with each other?

    python evaluation/compare_manual.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qcew_pipeline import load  # noqa: E402
from qcew_pipeline.config import load_config  # noqa: E402

HERE = Path(__file__).resolve().parent
COLUMNS = ["area_fips", "year", "industry_code", "employment", "avg_weekly_wage"]
KEY = ["area_fips", "year", "industry_code"]


def read_manual(path):
    return pd.read_csv(path, dtype={"area_fips": str, "industry_code": str})[COLUMNS]


def database_slice(cfg, manual):
    conn = load.connect(cfg["paths"]["db_path"])
    try:
        db = pd.read_sql_query(
            "SELECT area_fips, year, industry_code, employment, avg_weekly_wage "
            "FROM qcew_annual WHERE agglvl_code IN ('71','74')", conn)
    finally:
        conn.close()
    # Only look at the areas and years I actually did by hand.
    db = db[db["area_fips"].isin(manual["area_fips"].unique()) & db["year"].isin(manual["year"].unique())]
    return db


def compare(manual, db):
    merged = manual.merge(db, on=KEY, how="outer", suffixes=("_manual", "_pipeline"), indicator=True)
    both = merged[merged["_merge"] == "both"]

    def same(a, b):
        return (a == b) | (a.isna() & b.isna())

    mismatched = both[~(same(both["employment_manual"], both["employment_pipeline"])
                        & same(both["avg_weekly_wage_manual"], both["avg_weekly_wage_pipeline"]))]
    return {
        "rows_in_pipeline_slice": len(db),
        "rows_in_manual_table": len(manual),
        "rows_only_in_manual": int((merged["_merge"] == "left_only").sum()),
        "rows_only_in_pipeline": int((merged["_merge"] == "right_only").sum()),
        "rows_matching_exactly": len(both) - len(mismatched),
        "rows_with_different_values": len(mismatched),
    }, mismatched


def main():
    cfg = load_config()
    log = pd.read_csv(HERE / "manual_workflow_log.csv")
    lines = ["# Manual workflow vs pipeline", ""]

    filled = log.dropna(subset=["minutes"])
    if filled.empty:
        print("The timing log is still empty. Fill in evaluation/manual_workflow_log.csv first.")
        return 1

    lines += ["## Time and effort (manual)", "", filled.to_markdown(index=False), ""]
    totals = filled.groupby("run")[["minutes", "actions"]].sum()
    lines += ["Totals per run:", "", totals.to_markdown(), ""]

    outputs = {}
    for run in (1, 2):
        p = HERE / f"manual_output_run{run}.csv"
        if p.exists():
            outputs[run] = read_manual(p)

    for run, manual in outputs.items():
        summary, bad = compare(manual, database_slice(cfg, manual))
        lines += [f"## Manual run {run} against the pipeline database", ""]
        lines += [f"* {k.replace('_', ' ')}: {v}" for k, v in summary.items()] + [""]
        if len(bad):
            lines += ["Rows that differ:", "", bad.head(25).to_markdown(index=False), ""]

    if 1 in outputs and 2 in outputs:
        summary, _ = compare(outputs[1], outputs[2])
        lines += ["## Repeatability of the manual workflow (run 1 vs run 2)", ""]
        lines += [f"* {k.replace('_', ' ')}: {v}" for k, v in summary.items()] + [""]

    out = Path(cfg["paths"]["output_dir"]) / "manual_vs_pipeline.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
