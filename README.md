# C5XW20: Midterm project (CSE558 Data Science, Monsoon 2026)

Question: does the gender gap in high income (>50K) survive matching on occupation and education?
Data: 1994 US census "Adult" data (UCI), train file, from Kaggle `mlbysoham/adult-dataset`.

Team: Aryan Bundela (2023141), Durgesh Kumar Sharma (2023214), Shourya Sharma (2020129), Arpit Dabas (2023131).

## Run it
```bash
bash run_all.sh        # about one minute; needs uv (and latexmk for the PDF)
```
Python 3.12, packages pinned in `pyproject.toml` and `uv.lock`. Every random step uses seed 558.
A TA running `run_all.sh` gets the same numbers (we checked: the three JSON files are byte-identical on a second run).

## Files
| Path | What it is |
|---|---|
| `PREREGISTRATION.md` | hypotheses, tests, thresholds, split. Committed first (see `git log`) |
| `data/adult.data` | raw file as downloaded (3.9 MB, CC BY 4.0, source: UCI Adult) |
| `src/01_prepare.py` | names, `?` to `Unknown`, drop 24 duplicates, one-hot, size check, 50/50 split (seed 558) |
| `src/02_explore.py` | EDA figures and numbers. Reads the exploration half only |
| `src/03_tests.py` | the four tests on the confirmation half, plus the comparison tests |
| `src/04_macros.py` | turns the JSON results into `report/numbers.tex` (no number is typed by hand) |
| `outputs/` | `clean.parquet`, `encoded_features.parquet`, `data_dictionary.csv`, `prep_stats.json`, `explore_stats.json`, `test_results.json`, figures |
| `report/main.tex`, `report/main.pdf` | the report (5 pages, template of the course) |

## Key numbers
- Size check: 32,537 rows x 108 columns = 3,513,996 (needs 3,000,000).
- Split: 16,268 exploration, 16,269 confirmation, seed 558, same >50K share (24.09%) in both.
- Test 1 (primary): CMH odds ratio 0.253 (0.227 to 0.283), one-sided p = 6.7e-143.
- Test 2: difference of hour gaps 3.79 h (2.70 to 4.88). Test 3: Hodges-Lehmann shift 0.0 h but mean gap 3.00 h. Test 4: Cramer's V 0.172.

## Changes made after the first run of `03_tests.py`
The tests, hypotheses, sides, thresholds and estimates were not changed. We did add, after seeing results:
1. Breslow-Day test restricted to strata with all margins above zero (the first version returned NaN).
2. Descriptive extras: share of people over, at and under 40 hours (Test 3); cell spreads and a Brown-Forsythe test (Test 2).
3. A second row in the summary figure for the Welch mean gap of Test 3, next to the pre-registered Hodges-Lehmann estimate.
4. Before the split we saw two whole-data summaries (income share and mean hours by sex). This is listed in `PREREGISTRATION.md`.

## To do before submission
- Put the real GitHub link in `report/body.tex` (red text near the top), then run `bash run_all.sh`.
- Check the contribution table in the report.
