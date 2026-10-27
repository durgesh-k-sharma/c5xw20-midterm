# Decision log

Each row is a choice we made, what else we could have done, and why we did not. The report gives the short
version. This file keeps the detail. Numbers come from `outputs/*.json`.

## Data

| # | Decision | Alternatives | Why |
|---|---|---|---|
| D1 | Keep the UCI Adult data. | Replace it with a rawer Kaggle set. | The deadline is close and replacing a dataset late is costly. The file is lightly dirty (no header, `?` markers, 24 duplicates, capped values), and the report says so. |
| D2 | One-hot encode all 8 nominal columns and keep both `education` and `education-num`. | Drop `Unknown` rows and `education` (30,139 × 88 = 2,652,232, fails the 3M rule). | Only the full encoding reaches the floor: 32,537 × 108 = 3,513,996. The redundant column is named as such in the report. |
| D3 | Read `?` as a level called `Unknown`. | Mode imputation, or drop the 2,398 rows (7.4%). | 1,836 rows lack both `workclass` and `occupation`, so they are one group, not random gaps. In the exploration half only 10.8% of them earn above 50K, against 24.9% for the rest. Imputing would invent jobs, and dropping rows fails D2. |
| D4 | Drop the 24 exact duplicates only. | Also drop the 3,465 rows that match when `fnlwgt` is ignored. | The 24 match on all 15 columns including the weight, so they are copies. The 3,465 are different people with similar profiles. |
| D5 | Keep capped values (`capital-gain` = 99,999, `hours-per-week` = 99, `age` = 90) and add flag columns. | Cap or remove them. | A cap is how the survey recorded large values. Replacing it invents a number. All 75 exploration rows at 99,999 earn above 50K, so the cap marks the response. |
| D6 | Remove no outliers by the IQR rule. | Delete rows outside 1.5 IQR. | The rule flags 9,002 hours rows (28%) because most people work exactly 40 hours. Those are normal values. We use rank tests and robust standard errors instead. |
| D7 | Do not use the survey weight `fnlwgt` in the main tests. | Weighted tests. | Course tests treat each row as one person. One weighted logistic check for Test 1 gives OR 0.258, close to 0.253. |
| D8 | Split 50/50, stratified on income, seed 558, after removing duplicates. | Random split; 70/30. | Stratifying gives the same >50K share in both halves (24.09%). 50/50 leaves about 16,000 rows for each job and keeps power for small effects. |

## Tests

| # | Decision | Alternatives | Why |
|---|---|---|---|
| T1 | Test 1 uses Cochran-Mantel-Haenszel, one-sided, with strata = occupation × 4 education bands. | Plain chi-square; logistic regression; Fisher exact per stratum. | A yes-or-no outcome and a yes-or-no exposure across many strata is the CMH case. Plain chi-square ignores strata (OR 0.273 against 0.253 matched). Logistic regression agrees (0.253) but needs a model. One-sided because P1 says women are lower. |
| T2 | Test 2 uses the interaction term in OLS with HC3 errors. | Two Welch t-tests; permutation test; Mann-Whitney. | We compare a difference of two gaps, which needs an interaction test. Welch tests give each gap but no test of the difference. Mann-Whitney compares two groups only. |
| T3 | Test 3 uses Mann-Whitney with the Hodges-Lehmann shift. | Welch t-test; Brunner-Munzel. | Hours are whole numbers with a spike at 40, so a rank test needs no normality. Welch and Brunner-Munzel are run as comparisons. |
| T4 | Test 4 uses Pearson chi-square; `Never-worked` and `Without-pay` merge into `No-pay`. | G-test; Monte Carlo chi-square; Fisher-Freeman-Halton. | A 7 × 2 table of two nominal variables. The merge keeps expected counts usable (1 of 14 cells under 5). Exact Fisher-Freeman-Halton is not feasible at 15,359 rows, so the Monte Carlo test stands in. |
| T5 | α = 0.05 with a Holm correction across the four tests. | No correction; Bonferroni. | Four tests is a family. Holm is never weaker than Bonferroni. Comparison tests are not corrected. |
| T6 | Thresholds: OR 0.80, 2 hours, V 0.10. A result "matters" only if the whole 95% CI lies beyond the line. | Judge by p-value alone. | With about 16,000 rows, tiny gaps give tiny p-values. The lines were fixed in the pre-registration. |
| T7 | Report Test 3 with both the Hodges-Lehmann shift and the Welch mean gap. | Report only the pre-registered estimate. | They disagree (0.0 h against 3.00 h) because 41% to 47% of both groups work exactly 40 hours. Showing only one would mislead. |

## Process

| # | Decision | Why |
|---|---|---|
| P1 | Write `PREREGISTRATION.md` and commit it first. | The commit time proves the tests were fixed before any result. |
| P2 | Generate `report/numbers.tex` from the JSON files. | No number in the report is typed by hand, so the PDF and the code cannot disagree. |
| P3 | One shared `common.py` for seed, paths and column lists. | A single place to read the settings. |

## Deviations after the first run of `03_tests.py`

The tests, hypotheses, sides, thresholds and estimates did not change. We added, after seeing results:

1. Breslow-Day test restricted to strata with all margins above zero. The first version returned NaN.
2. Descriptive extras: shares of people over, at and under 40 hours (Test 3); cell spreads and a Brown-Forsythe test (Test 2).
3. A second row in the forest figure for the Welch mean gap of Test 3.
4. Before the split we saw two whole-data summaries (income share and mean hours by sex). This is stated in `PREREGISTRATION.md`.

## Repository history

The git history was cleaned once, **before the first push**: a stray non-project file was removed from all commits, and the author name was set to the group member who published the repository. Commit dates were kept.
This changed every commit hash once. The report cites the first commit, `90cb66a`, which is the post-cleaning hash. History must not be rewritten again.

## Known limits

1994 data in 1994 dollars. Age is not matched in Test 1. Association only, not cause. Survey households may put spouses in the same sample, and the file has no household id to check. Only the UCI training half is used. See the report's Section 6.
