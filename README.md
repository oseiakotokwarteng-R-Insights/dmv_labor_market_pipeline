# Regional Labor Market Data Pipeline (DC, Maryland, Virginia)

This project grabs job and wage numbers from the Bureau of Labor Statistics (BLS), cleans them up, checks them, and saves them in one small database. It covers Washington DC, Maryland and Virginia (the DMV) for the years 2020 to 2024.

The numbers come from a BLS program called the Quarterly Census of Employment and Wages, or QCEW for short. It counts jobs and wages at businesses, county by county.

I built this to answer one question: is it actually better to do this kind of data prep with an automated, checked process than to do it by hand? I'm not studying the regional economy here. The pipeline is the point.

## Why I built it

BLS gives this data away for free, but free doesn't mean easy. Each year's file has about 3.6 million rows, which is too big for Excel to open. The area and industry codes need to be translated into names. Some numbers are hidden for privacy and show up as zeros even though they aren't really zero. And when BLS puts out a new year, you have to do it all again.

So I wrote a program that does these steps the same way every time, checks its own work, and keeps notes on what it did. It's not another BLS download site and it's not a dashboard. BLS already has plenty of ways to download data. I wanted to see what you gain by automating the whole prep process and writing it all down.

## What you get

- `data/qcew_dmv.sqlite` is the database. It holds about 16,000 rows covering private-sector jobs, number of businesses and wages for every county in DC, Maryland and Virginia, plus state totals. When BLS hides a number, the database leaves it blank and marks it as hidden. It never fills in a zero.
- `outputs/exports/` has the same data as CSV files you can open in Excel.
- `outputs/logs/` has a log of each run, so you can see what happened.
- `outputs/evaluation_summary.md` shows how I tested the program.
- `docs/data_dictionary.md` explains every table and column in plain words.

## Try it yourself

You'll need Python 3.11 or newer. Then run these two commands:

```bash
pip install -r requirements.txt
```

```bash
python -m qcew_pipeline.run --export
```

The first one installs pandas, which is the only extra thing the program needs. The second one downloads five files from BLS (about 390 MB all together) and builds the database. That takes a few minutes the first time. If you run it again later, it won't download the files a second time, so it's quicker, but it still takes a minute or two to read through them.

The finished database is already in this repository. So if you run the program right after downloading the project, you'll see a line like `0 inserted, 0 changed, 16,232 unchanged`. That's what you want to see. It means the program rebuilt the same numbers that were already saved.

Two other things you can do:

```bash
python -m qcew_pipeline.run --years 2023 2024
```

That runs only the years you list.

```bash
python -m qcew_pipeline.check_updates
```

That asks BLS whether a newer year has been published.

If you'd like the big downloads to go somewhere other than the project folder, set `QCEW_RAW_DIR` to the folder you want. BLS also likes automated programs to say who they are, so you can set `QCEW_USER_AGENT` to your own contact details. Both settings stay on your computer and never get saved into the project.

### Running it in Google Colab

I built this on my Windows laptop, and then I ran it in Google Colab from a fresh copy to make sure it works somewhere else. It does. In a Colab notebook, paste these into two separate cells:

```python
!git clone https://github.com/oseiakotokwarteng-R-Insights/dmv_labor_market_pipeline.git
%cd dmv_labor_market_pipeline
```

```python
!pip install -r requirements.txt
!python -m qcew_pipeline.run --export
```

### GitHub Codespaces

It should work the same way there, but I haven't tried it yet.

## How it works

The program does four things, one after the other:

1. **Collect.** It downloads each year's file from BLS and tries again if a download fails. It writes down where each file came from, when it was downloaded, and how big it was. It also saves a short code that's unique to each file (a SHA-256 hash), so anyone can check that they have the exact same file. It also downloads BLS's own lists that translate area and industry codes into names.
2. **Transform.** The files are huge, so it reads them a piece at a time and keeps only what I need: DC, Maryland and Virginia, private-sector businesses, at the county and state level. It renames the columns, fixes the number formats, and blanks out the hidden values.
3. **Validate.** It runs 16 checks on the result. Some look for problems like missing information, duplicate rows, codes that don't exist, and negative numbers. Others make sure hidden values didn't sneak through as zeros, that each state has the right number of counties, and that the county numbers add up to the state totals BLS published. If a check finds a real error, the whole run stops and nothing gets saved. Smaller issues get written down as warnings.
4. **Load.** It saves the data into the database all at once. Running it twice won't create duplicates. It also counts how many saved numbers changed, so if BLS ever revises old data, you'd see it instead of it happening quietly.

There's a diagram and a list of the choices I made in [`docs/architecture.md`](docs/architecture.md). All the settings, like which years and states to use, are in [`config.toml`](config.toml), so you don't have to touch the code to change them.

## Testing

```bash
pip install -r requirements-dev.txt
```

```bash
python -m pytest -q
```

There are 23 automated tests. They check things like the filtering, the rule about hidden values, saving without duplicates, and counting changed numbers. Each of the 16 checks has its own test, where I break the data on purpose in exactly the way that check is supposed to catch. The tests use a small amount of made-up data, so they finish in a few seconds.

GitHub also runs these tests by itself every time I upload changes (the setup is in `.github/workflows/pipeline.yml`). The first time it ran, everything passed in about 40 seconds. That same setup is also meant to check once a month for new BLS data, and to run the full program when I start it by hand. I haven't seen those two parts run on GitHub yet.

## How I tested the whole thing

```bash
python evaluation/run_evaluation.py
```

This script runs the program on the real BLS files three ways: starting from nothing, running it again on the same database, and rebuilding the database from scratch. Then it takes a copy of the real data and breaks it in 11 different ways, to see whether the checks notice. Last, it sets up three things going wrong: asking for a year BLS hasn't published, a damaged download, and data that fails the checks. In every case the existing data stayed untouched.

The results are saved in `outputs/evaluation_results.json` and `outputs/evaluation_summary.md`. I also walk through them in [`notebooks/pipeline_walkthrough.ipynb`](notebooks/pipeline_walkthrough.ipynb).

### Does it work on other computers?

I ran everything in three places, and it worked each time:

| Where | What I ran | What happened |
|---|---|---|
| My Windows laptop | The program, all 23 tests, the full evaluation | Everything passed. Starting from nothing took about 204 seconds, a repeat run 149, and a rebuild 139. |
| GitHub (Linux) | All 23 tests | Passed in 41 seconds. |
| Google Colab (Linux) | The program, all 23 tests, the full evaluation, the update check, the example database questions | Everything passed. Starting from nothing took about 236 seconds, a repeat run 79, and a rebuild 75. |

The Colab run downloaded fresh files from BLS and built its own database. Its final result matched my laptop's exactly. I check this with a short code computed from all the data (it starts with `46a4ac415135b5f2`). The 2024 file's code matched too. So two different computers got the same file from BLS and ended up with the same numbers. The times jump around from one machine and one run to the next, so I wouldn't read much into the differences.

### Manual versus automated

The other half of my testing compares doing the work by hand against running the program. I've written the rules for the by-hand version in [`docs/manual_workflow_protocol.md`](docs/manual_workflow_protocol.md), and the timing sheet is `evaluation/manual_workflow_log.csv`. I haven't done the by-hand runs yet.

## Where things are

```
config.toml                 settings
qcew_pipeline/              the program (collect, transform, validate, load, export, run)
sql/schema.sql              how the database is laid out
sql/example_queries.sql     example questions to ask it
tests/                      automated tests
evaluation/                 testing scripts and the manual-work timing sheet
notebooks/                  walkthrough notebook with results
docs/                       data dictionary, architecture, manual-work rules
data/qcew_dmv.sqlite        the finished database
outputs/                    logs, test results, CSV exports
draft/                      the written draft of the project
.github/workflows/          the setup GitHub uses to run tests
```

## Where the project stands

Everything in the program itself is built and tested: collecting, cleaning, checking, saving and exporting, plus the 16 checks, the 23 tests, the monthly update check, and the example database questions. It all runs on my laptop and in Colab, and the tests pass on GitHub.

Still to do:

- The by-hand half of the comparison. The rules are written, but I haven't timed myself doing it yet.
- Seeing the monthly update check and the by-hand run work on GitHub. So far only the test run has happened there. I also haven't tried a Codespace.
- Adding 2025. The update check says BLS has already published that year. It should only mean changing the list of years in `config.toml`, but I haven't tried it.

## Things to keep in mind

- **Only one data source.** Everything comes from QCEW. I kept it to one source so the project stays manageable. That means it shows how to build a pipeline, not how to combine several sources.
- **Private sector only.** Government jobs are counted and paid differently, so I left them out.
- **It counts jobs, not people.** The numbers tell you how many jobs businesses in a county have. They can't tell you where workers live, who they are, or why a number went up or down.
- **Some numbers are hidden.** BLS hides some county-by-industry numbers to protect individual employers. I leave those blank instead of guessing. So if you add up the industries for a small county, the total will come out lower than the real one.
- **The timings are rough.** They come from my laptop and a Colab machine, using whatever internet each one had. Reading the files took anywhere from about 75 to 140 seconds. They're useful for comparing, but they aren't official speed tests.

## Where the data comes from

The Bureau of Labor Statistics, Quarterly Census of Employment and Wages: the yearly download files and the code lists, from <https://www.bls.gov/cew/>. This is public government data and has no personal information in it. The numbers in my database are the ones BLS published. All I do is filter them, add names to the codes, and check them.
