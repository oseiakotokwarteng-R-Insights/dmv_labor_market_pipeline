# Manual workflow protocol (Method A)

This is how I'll prepare the same data by hand, so the comparison with the pipeline is fair. I'm writing the rules down **before** I do it so I don't change them after seeing the pipeline's numbers.

## Why a sample and not the full dataset

The national annual file has about 3.6 million rows per year, and Excel stops at 1,048,576 rows, so the file can't just be opened and filtered. Doing the full job by hand (158 counties, 5 years, about 20 sectors each) isn't realistic either. So the manual run covers a defined **sample slice**, and I report the time per county-year so the scale-up is visible but clearly labelled as an estimate, not a measurement.

## The sample slice

* Areas: District of Columbia (11001), Arlington County VA (51013), Montgomery County MD (24031)
* Years: 2023 and 2024
* Rows wanted: private sector (ownership 5); the county total (industry 10) and every two-digit NAICS sector
* Fields wanted: area code, area name, year, industry code and title, employment, average weekly wage, and whether the value was suppressed

## What I'm allowed to use

BLS's own website tools and downloads, plus Excel or Google Sheets. No Python, no SQL, no scripts.

## Rules for timing

1. Start a stopwatch before each step in `evaluation/manual_workflow_log.csv`, stop it when the step is done, and write down the minutes.
2. Count every distinct action (a download, a filter, a copy-paste, a lookup) in `actions`.
3. Write down every problem I hit (file too big, wrong code, confusing column) in `problems`.
4. Do not fix anything silently. If I find a mistake and redo work, log the redo as its own row.
5. Do the whole thing twice, a few days apart if I can. Run 1 is "first execution" and run 2 is "repeat execution". Compare run 2's output with run 1's to measure repeatability.

## Steps to log

| Step | What it covers |
|---|---|
| find_source | Working out where on BLS's site the right files/tools are |
| download | Getting the data for the sample slice |
| filter | Cutting it down to the sample areas, years, ownership and industries |
| label | Adding area names and industry titles from the BLS code lists |
| clean | Handling suppressed values, fixing types, standardizing column names |
| check | Any checking I do for duplicates, missing rows, or agreement with BLS totals |
| assemble | Putting it all into one table |

## Output

Save the final hand-built table as `evaluation/manual_output_run1.csv` (and `manual_output_run2.csv`) with these columns exactly:

`area_fips, year, industry_code, employment, avg_weekly_wage`

(leave a value empty if BLS didn't publish it.) Then run:

```bash
python evaluation/compare_manual.py
```

That compares my hand-built table with the pipeline's database, row by row, and writes `outputs/manual_vs_pipeline.md`.

## What the comparison will and won't say

It is one controlled example of one task. It can show differences in time, steps, mistakes caught, and repeatability for this slice. It can't show that automation is always better, and it doesn't cover the time it took me to build the pipeline, which I'll report separately.
