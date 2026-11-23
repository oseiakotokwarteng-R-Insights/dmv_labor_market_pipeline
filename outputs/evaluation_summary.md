# Pipeline evaluation results

Run on 2026-11-23 - Windows-11-10.0.26200-SP0, Python 3.14.5, pandas 3.0.5.

## Runs

| Scenario | Status | Seconds (total) | Rows inserted | Rows changed | Same data as cold run |
|---|---|---|---|---|---|
| Cold run (downloads files) | success | 204.01 | 16,232 | 0 | - |
| Repeat run, same database | success | 149.04 | 0 | 0 | True |
| Rebuild from scratch | success | 139.38 | 16,232 | 0 | True |

Rows in database: 16,232. Database size: 1.61 MB.

## Faults I injected on purpose

11 of 11 injected faults were caught by the check built for them. The unmodified data failed 0 checks.

| Injected fault | Expected check | Caught |
|---|---|---|
| Duplicate row | `no_duplicate_keys` | yes |
| Area code that doesn't exist | `valid_area_codes` | yes |
| Industry code that doesn't exist | `valid_industry_codes` | yes |
| Missing key field | `required_fields_not_null` | yes |
| Suppressed value stored as zero | `suppressed_values_are_null_not_zero` | yes |
| Negative employment | `no_negative_measures` | yes |
| A whole year missing | `all_years_present_with_enough_rows` | yes |
| One county missing in one year | `same_counties_in_every_year` | yes |
| County total tripled | `county_totals_agree_with_state_total` | yes |
| One sector inflated above county total | `sector_sum_not_above_county_total` | yes |
| Annual pay disagrees with weekly wage | `annual_pay_matches_weekly_wage` | yes |

## Things going wrong

| Scenario | Expected | Actual | Data left unchanged |
|---|---|---|---|
| Year that BLS hasn't published (2099) | failed | failed | True |
| Corrupted zip file | failed | failed | True |
| Validation error blocks the load | failed_validation | failed_validation | True |
