# Runbook: reproduce the results

Use this when you want to rebuild the numbers, figures and PDF from the raw file, or when a run fails.
For what the project is, see the [README](../README.md).

## Prerequisites

| Need | Why | Check |
|---|---|---|
| `uv` | installs Python packages from `uv.lock` | `uv --version` |
| Python 3.12 or newer | `uv` fetches it if missing | `uv run python --version` |
| Internet, first run only | downloads packages | n/a |
| `latexmk` with pdfLaTeX (optional) | builds `report/main.pdf` | `latexmk -v` |

No account, key or data download is needed. The raw file is in `data/adult.data`.

## Procedure

```bash
bash run_all.sh
```

This runs, in order:

| Step | Script | What it does | Time |
|---|---|---|---|
| 0 | `uv sync` | install pinned packages | first run only |
| 1 | `01_prepare.py` | clean, encode, size check, split (seed 558) | about 21 seconds |
| 2 | `02_explore.py` | EDA on the exploration half | about 4 seconds |
| 3 | `03_tests.py` | four tests and comparison tests | about 12 to 17 seconds |
| 4 | `04_macros.py` | write `report/numbers.tex` | under 1 second |
| 5 | `latexmk` | build `report/main.pdf` | a few seconds |

The whole run took 54 seconds on our machine. Steps 1 to 3 write a log to `outputs/log_0N_*.txt`.

## Checks: did it work?

| Check | Expected |
|---|---|
| `outputs/prep_stats.json` → `size_product` | 3513996 |
| `outputs/prep_stats.json` → `n_explore`, `n_confirm` | 16268, 16269 |
| `outputs/test_results.json` → `t1.or_mh` | 0.253 (rounded) |
| `outputs/test_results.json` → `t2.D` | 3.79 (rounded) |
| `outputs/test_results.json` → `t4.V` | 0.172 (rounded) |
| `report/main.pdf` | 5 pages |
| `git status` after the run | clean, if nothing was changed |

Quick print of the numbers:

```bash
python3 - <<'PY'
import json
t = json.load(open("outputs/test_results.json"))
print("T1 OR", round(t["t1"]["or_mh"], 3), "| T2 D", round(t["t2"]["D"], 2),
      "| T3 HL", t["t3"]["hl"], "| T4 V", round(t["t4"]["V"], 3))
PY
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv not installed | install from https://docs.astral.sh/uv/ |
| `bash: run_all.sh: Permission denied` | no execute bit | run `bash run_all.sh` |
| `ModuleNotFoundError` | packages not installed | run `uv sync`, then use `uv run python ...` |
| Step 2 or 3 says `clean.parquet` is missing | step 1 did not run | run step 1 first |
| `latexmk: command not found` | no LaTeX | skip the PDF, or upload `main.tex`, `numbers.tex` and `figures/` to Overleaf |
| LaTeX error `Undefined control sequence` | `numbers.tex` is out of date | run `python src/04_macros.py` again, via `uv run` |
| Font warning about Carlito | font not installed | harmless; the template falls back to Helvetica |
| Numbers differ in far digits | different library build | expected; compare to the precision shown in the report |

## Rebuild only part of the project

```bash
cd src
uv run python 04_macros.py                         # refresh report numbers from the JSON files
cd ../report && cat preamble.tex body.tex > main.tex && latexmk -pdf main.tex
```

`report/main.tex` is generated. Edit `report/preamble.tex` or `report/body.tex`, not `main.tex`.

## Rollback

If a run left the outputs in a bad state and you have not committed:

```bash
git checkout -- outputs report
bash run_all.sh
```

## Safe-change rules

1. Never edit `PREREGISTRATION.md`.
2. If you change a test, a threshold or the split, record it in the deviations list in [`DECISIONS.md`](DECISIONS.md), and say it in the report's Limitations.
3. Never add code to `02_explore.py` that reads `split == "confirm"`.
4. Commit scripts and regenerated outputs together, so a reader can match results to code.

## Who to ask

| Topic | Person |
|---|---|
| Dataset, size check, repo, README | Aryan Bundela |
| Preparation and before/after numbers | Durgesh Kumar Sharma |
| EDA, problem statements, Test 1 | Shourya Sharma |
| Tests 2 to 4, limitations | Arpit Dabas |
