# Pre-registration (written before any exploration or test)

Group C5XW20. Dataset: Adult (UCI / Kaggle `mlbysoham/adult-dataset`), train file only.

Everything below is fixed before `01_prepare.py`, `02_explore.py` and `03_tests.py` were written or run.
The git commit time of this file shows the order.

## Disclosure
Before the split existed, we looked at three whole-data summaries (all 32,561 rows):
the share of >50K by sex (10.9% women, 30.6% men), mean hours per week by sex (36.4 women, 42.4 men),
and counts of "?" and duplicates. These are the "obvious questions". Our four tests were
written after that, and we did not look at any other summary by group.

## Data steps
1. Add column names. Strip spaces. Read " ?" as the level `Unknown`.
2. Remove the 24 exact duplicate rows.
3. Split 50/50, stratified on `income`, `random_state=558`. Exploration half: EDA only.
   Confirmation half: tests only.
4. Education bands: below HS graduate (Preschool to 12th), HS graduate, some college or associate
   (Some-college, Assoc-acdm, Assoc-voc), Bachelors or higher (Bachelors, Masters, Prof-school, Doctorate).

## Common rules
- Significance level alpha = 0.05 for each test. Holm correction across the four p-values.
  The decision uses the Holm-adjusted p-value.
- Confidence intervals are 95%, two-sided, not adjusted.
- "Matters": the whole 95% CI lies beyond the smallest difference that matters.
  "Does not matter": the whole CI lies on the small side of it. Otherwise: "inconclusive".
- All random steps use seed 558.
- Main tests are unweighted. `fnlwgt` is used only in one check for Test 1.

## Test 1 (primary, P1)
Rows: confirmation half, `occupation` not Unknown. Strata: occupation x education band.
Strata with no men or no women are dropped (the number of rows lost is reported).
- Outcome: income >50K. Exposure: sex. Odds ratio OR = odds(women) / odds(men), common across strata.
- H0: OR >= 1. H1: OR < 1. One-sided. alpha = 0.05.
- Test: Cochran-Mantel-Haenszel (no continuity correction), d.f. = 1.
- Estimate: Mantel-Haenszel common OR with Robins-Breslow-Greenland 95% CI.
- Smallest difference that matters: OR = 0.80 (women have 20% lower odds).
- Compared with: plain chi-square on the collapsed table, logistic regression with stratum dummies
  (strata with constant outcome are dropped, because they carry no information on the sex effect
  and cause separation), and Breslow-Day test of equal ORs across strata.
- Check, not a test: weighted logistic regression with `fnlwgt` weights and robust errors.

## Test 2 (P2)
Rows: confirmation half, sex in {Female, Male}, marital status in {Married-civ-spouse, Never-married}.
- Gap g = mean hours of men minus mean hours of women in marital group g.
  D = gap(Married-civ-spouse) - gap(Never-married).
- H0: D = 0. H1: D != 0. Two-sided. alpha = 0.05.
- Test: OLS `hours ~ male * married`, t-test on the interaction term, HC3 robust errors.
- Smallest difference that matters: |D| = 2 hours per week.
- Compared with: permutation test of D (10,000 shuffles of sex within marital group),
  classical (non-robust) OLS t-test, two separate Welch t-tests (one gap per group, no test of D).

## Test 3 (P3)
Rows: whole confirmation half. Groups: capital gain > 0 versus capital gain = 0.
- H0: the two hours distributions are equal (no shift). H1: they differ. Two-sided. alpha = 0.05.
- Test: Mann-Whitney U (asymptotic, tie correction).
- Estimate: Hodges-Lehmann shift (median of all pairwise differences), bootstrap percentile 95% CI
  (2,000 resamples). Raw medians are also shown.
- Smallest difference that matters: 2 hours per week.
- Compared with: Welch t-test on the means, Brunner-Munzel test.

## Test 4 (P4)
Rows: confirmation half, `workclass` not Unknown. `Never-worked` and `Without-pay` merge into `No-pay`.
- H0: income (>50K or not) is independent of workclass. H1: not independent. Two-sided. alpha = 0.05.
- Test: Pearson chi-square test of independence.
- Estimate: Cramer's V, bootstrap percentile 95% CI (2,000 resamples).
- Smallest difference that matters: V = 0.10.
- Compared with: G-test (likelihood ratio), Monte Carlo chi-square (10,000 permutations),
  Fisher-Freeman-Halton exact test (not feasible at this n, so the Monte Carlo test stands in for it).

## Known limits we state in advance
1994 data in 1994 dollars. Age is not matched in Test 1. Association, not causation.
Train half of the UCI data only. Top-coded values kept.
