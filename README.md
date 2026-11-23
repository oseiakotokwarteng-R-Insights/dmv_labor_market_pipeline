# Regional Labor Market Data Pipeline (DC, Maryland, Virginia)

An automated, tested pipeline that turns the Bureau of Labor Statistics' **Quarterly Census of Employment and Wages (QCEW)** annual files into a clean, documented SQLite database for the DMV region (Washington DC, Maryland and Virginia), 2020 to 2024.

This is my capstone project for the MA in Social Data Science at Arizona State University. It's an engineering project: the point is the pipeline (how it collects, checks, stores and documents the data) and whether it's actually better than preparing the same data by hand. It is not an analysis of the regional economy.

## Why I built it

BLS publishes QCEW data for free, but "available" isn't the same as "ready to use." The annual national file has around 3.6 million rows per year. Excel can't open it, the codes need translating, hidden (suppressed) values show up as zeros, and the whole process has to be repeated every time BLS releases a new year. This pipeline does those steps the same way every time, checks its own work, and leaves a record of what it did.

It isn't another BLS download site or a dashboard. BLS already has tools for getting the data. What I'm testing is what *automating and documenting the whole preparation process* adds on top.

## What it produces

* `data/qcew_dmv.sqlite`: the database. About 16,000 rows of private-sector employment, establishments and wages for every DC/MD/VA county plus state totals, 2020-2024. Suppressed values are NULL (never zero) and flagged.
* `outputs/exports/*.csv`: the same data as spreadsheets-friendly files.
* `outputs/logs/` and `outputs/run_summary_*.json`: a record of every run.
* `outputs/evaluation_summary.md`: results of testing the pipeline (see below).
* `docs/data_dictionary.md`: what every table and field means.

## Quick start

You need Python 3.11 or newer.

```bash
pip install -r requirements.txt        # just pandas
python -m qcew_pipeline.run --export   # downloads about 375 MB from BLS, builds the database
```

The first run downloads five zip files (about 75 MB each) to `data/raw/` and takes a few minutes. Running it again reuses the downloaded files and finishes much faster. Files are not re-downloaded unless you delete them.

Useful options:

```bash
python -m qcew_pipeline.run --years 2023 2024     # only some years
python -m qcew_pipeline.check_updates             # has BLS published a newer year?
```

To keep the big downloads somewhere else, set `QCEW_RAW_DIR`. To put your own contact details in the request header BLS sees, set `QCEW_USER_AGENT`. Both are read from the environment so they never get committed.

### In GitHub Codespaces

Open the repository in a Codespace and run the same two commands in the terminal. I built and tested everything on my own Windows laptop and haven't run it inside a Codespace yet, so treat this as expected to work rather than confirmed.

## How it works

```
BLS files -> collect -> transform -> validate -> load -> SQLite -> CSV exports
                                        |
                                  any error: stop, record it, load nothing
```

1. **Collect** (`qcew_pipeline/collect.py`): downloads each year's zip with retries, records the source URL, retrieval time, size and SHA-256 fingerprint, and fetches BLS's own code/title lookup files.
2. **Transform** (`transform.py`): reads the big file in chunks, keeps only DC/MD/VA private-sector rows at the county-total, county-sector and state-total levels, renames columns, fixes types, and converts suppressed values to NULL.
3. **Validate** (`validate.py`): runs 16 checks (required fields, duplicate keys, valid codes, negative values, suppression handling, county counts, agreement with BLS's published state totals, and more). Errors stop the load. Warnings are recorded.
4. **Load** (`load.py`): upserts into SQLite in one transaction, so reruns can't create duplicates, and counts how many existing rows changed (so a BLS revision would be visible).

The diagram and a table of decisions are in [`docs/architecture.md`](docs/architecture.md). Every setting (years, states, tolerances, paths) is in [`config.toml`](config.toml).

## Testing

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

23 automated tests cover filtering, the suppression rule, every validation check (each one is tested by breaking the data in exactly the way it's meant to catch), idempotent loading, and revision counting. They use small made-up data so they run in seconds. GitHub Actions runs them on every push (`.github/workflows/pipeline.yml`) and also checks monthly whether BLS has published a new year.

## Evaluating the pipeline

```bash
python evaluation/run_evaluation.py
```

This runs the pipeline against the real BLS files three ways (cold start, repeat, rebuild from scratch), injects 11 deliberate faults into a copy of the real data to see which are caught, and simulates three failure scenarios (a year BLS hasn't published, a corrupted download, a failed validation). Results are written to `outputs/evaluation_results.json` and `outputs/evaluation_summary.md`, and walked through in [`notebooks/pipeline_walkthrough.ipynb`](notebooks/pipeline_walkthrough.ipynb).

The second part of the evaluation is a manual-versus-automated comparison on the same data. The rules are in [`docs/manual_workflow_protocol.md`](docs/manual_workflow_protocol.md) and the timing log is `evaluation/manual_workflow_log.csv`.

## Repository map

```
config.toml                 settings
qcew_pipeline/              the pipeline code (collect, transform, validate, load, export, run)
sql/schema.sql              database design
sql/example_queries.sql     example questions to ask the database
tests/                      automated tests
evaluation/                 evaluation scripts and the manual-workflow log
notebooks/                  walkthrough notebook with results
docs/                       data dictionary, architecture, manual-workflow protocol
data/qcew_dmv.sqlite        the finished database
outputs/                    logs, run summaries, validation and evaluation results, CSV exports
draft/                      the capstone draft document
.github/workflows/          GitHub Actions
```

## Where the project stands

**Working and tested:** the full pipeline (collect, transform, validate, load, export), 16 validation checks, 23 automated tests, GitHub Actions workflow, data dictionary, architecture documentation, and the pipeline-side evaluation.

**Still in progress:** the manual-workflow half of the comparison (the protocol is written; the timed manual runs are not done yet), and I haven't yet seen the GitHub Actions workflow run on GitHub itself or run the project in a Codespace.

## Limits to keep in mind

* One data source (QCEW). I deliberately kept it to one to keep the project doable, so this shows pipeline engineering on a single source rather than integration across sources.
* Private sector only. Government employment is covered and paid differently.
* QCEW counts jobs at employers by where the employer is located. It says nothing about individual workers, where they live or why anything changed.
* Some county-sector values are hidden by BLS. They're stored as NULL, which means sector sums for small counties are lower bounds.
* Timings come from one Windows laptop on one connection. They're useful for comparing workflows, not as benchmarks.

## Data source

Bureau of Labor Statistics, Quarterly Census of Employment and Wages, annual single-file downloads and code/title files, <https://www.bls.gov/cew/>. These are U.S. government public data and contain no personal information. The numbers in the database are BLS's published values; the pipeline only filters, relabels and checks them.
