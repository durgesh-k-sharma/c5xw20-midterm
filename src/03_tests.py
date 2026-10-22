"""Step 3: the four pre-registered tests on the CONFIRMATION half (see PREREGISTRATION.md).

Run: uv run python 03_tests.py
"""
import json
import subprocess
import warnings
import numpy as np
import pandas as pd
import scipy.stats as ss
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import OUT, FIG, SEED, ROOT

rng = np.random.default_rng(SEED)
df_all = pd.read_parquet(OUT / "clean.parquet")
CF = df_all[df_all.split == "confirm"].copy()
del df_all
R = {"n_confirm": len(CF)}
R["prereg_commit"] = subprocess.run(["git", "log", "-1", "--format=%h %ad", "--date=iso", "--", "PREREGISTRATION.md"],
                                    cwd=ROOT, capture_output=True, text=True).stdout.strip()

def verdict(lo, hi, thr_lo, thr_hi):
    """matters: whole CI beyond the threshold. does not matter: whole CI inside the small zone."""
    if thr_hi is None:                       # one-sided threshold (odds ratio: matters if below thr_lo)
        return "matters" if hi < thr_lo else ("does not matter" if lo > thr_lo else "inconclusive")
    if lo > thr_hi or hi < thr_lo:
        return "matters"
    if lo > thr_lo and hi < thr_hi:
        return "does not matter"
    return "inconclusive"

# =============================== TEST 1: CMH ===============================
d1 = CF[CF.occupation != "Unknown"].copy()
R["t1_rows_known_occ"] = len(d1)
R["t1_rows_unknown_occ_dropped"] = int(len(CF) - len(d1))
d1["stratum"] = d1.occupation + " | " + d1.edu_band
tabs, keep, strata_all = [], [], d1.stratum.unique()
for s_, g in d1.groupby("stratum"):
    if g.female.nunique() < 2:
        continue
    t = pd.crosstab(g.female, g.income_high).reindex(index=[1, 0], columns=[1, 0], fill_value=0).values
    tabs.append(t); keep.append(s_)
d1k = d1[d1.stratum.isin(keep)].copy()
R["t1_strata_all"] = int(len(strata_all)); R["t1_strata_used"] = len(keep)
R["t1_rows_used"] = len(d1k); R["t1_rows_lost_one_sex_strata"] = int(len(d1) - len(d1k))
R["t1_n_women"] = int(d1k.female.sum()); R["t1_n_men"] = int((1 - d1k.female).sum())
R["t1_rate_women"] = float(d1k.loc[d1k.female == 1, "income_high"].mean())
R["t1_rate_men"] = float(d1k.loc[d1k.female == 0, "income_high"].mean())
# CMH by hand: a = women high, rows = (women, men), cols = (high, low)
a = np.array([t[0, 0] for t in tabs], float)
r1 = np.array([t[0].sum() for t in tabs], float); r2 = np.array([t[1].sum() for t in tabs], float)
c1 = np.array([t[:, 0].sum() for t in tabs], float); c2 = np.array([t[:, 1].sum() for t in tabs], float)
n = r1 + r2
E = r1 * c1 / n
V = r1 * r2 * c1 * c2 / (n ** 2 * (n - 1))
cmh = (a - E).sum() ** 2 / V.sum()
z = np.sign((a - E).sum()) * np.sqrt(cmh)
st = StratifiedTable(tabs)
ci = st.oddsratio_pooled_confint(alpha=0.05)
chk = st.test_null_odds(correction=False)
assert abs(chk.statistic - cmh) < 1e-6, (chk.statistic, cmh)
p1 = float(ss.norm.cdf(z))                           # one-sided, H1: OR < 1
R["t1"] = dict(or_mh=float(st.oddsratio_pooled), ci_lo=float(ci[0]), ci_hi=float(ci[1]),
               chi2=float(cmh), df=1, z=float(z), p_one_sided=p1,
               rr_pooled=float(st.riskratio_pooled))
ok = (r1 > 0) & (r2 > 0) & (c1 > 0) & (c2 > 0)          # Breslow-Day needs every margin > 0
st_ok = StratifiedTable([t for t, v in zip(tabs, ok) if v])
bd = st_ok.test_equal_odds(adjust=True)
R["t1"]["breslow_day_tarone"] = dict(stat=float(bd.statistic), df=int(ok.sum()) - 1, p=float(bd.pvalue),
                                     strata=int(ok.sum()), or_mh_these_strata=float(st_ok.oddsratio_pooled))
# strata-specific ORs: how many point the same way?
sor = [(t[0, 0] * t[1, 1]) / (t[0, 1] * t[1, 0]) if t[0, 1] * t[1, 0] > 0 else np.nan for t in tabs]
sor = np.array(sor, float)
R["t1"]["strata_or_defined"] = int(np.isfinite(sor).sum())
R["t1"]["strata_or_below_1"] = int((sor[np.isfinite(sor)] < 1).sum())
# comparator 1: plain chi-square on the collapsed table
crude = pd.crosstab(d1k.female, d1k.income_high).reindex(index=[1, 0], columns=[1, 0]).values
chi_c = ss.chi2_contingency(crude, correction=False)
or_c = crude[0, 0] * crude[1, 1] / (crude[0, 1] * crude[1, 0])
se_c = np.sqrt((1 / crude).sum())
R["t1"]["crude"] = dict(chi2=float(chi_c[0]), df=int(chi_c[2]), p_two_sided=float(chi_c[1]), or_crude=float(or_c),
                        ci_lo=float(np.exp(np.log(or_c) - 1.96 * se_c)), ci_hi=float(np.exp(np.log(or_c) + 1.96 * se_c)))
# comparator 2: logistic regression with stratum dummies (drop strata with constant outcome)
var = d1k.groupby("stratum").income_high.nunique()
d1l = d1k[d1k.stratum.isin(var[var > 1].index)].copy()
d1l["stratum"] = d1l.stratum.astype("category")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m = smf.glm("income_high ~ female + C(stratum)", data=d1l, family=sm.families.Binomial()).fit()
    w = d1l.fnlwgt / d1l.fnlwgt.mean()
    mw = smf.glm("income_high ~ female + C(stratum)", data=d1l, family=sm.families.Binomial(),
                 freq_weights=w).fit(cov_type="HC1")
def lr(mod):
    b, se = mod.params["female"], mod.bse["female"]
    return dict(or_=float(np.exp(b)), ci_lo=float(np.exp(b - 1.96 * se)), ci_hi=float(np.exp(b + 1.96 * se)),
                z=float(b / se), p_one_sided=float(ss.norm.cdf(b / se)))
R["t1"]["logit"] = lr(m); R["t1"]["logit"]["rows"] = len(d1l); R["t1"]["logit"]["strata"] = int(d1l.stratum.nunique())
R["t1"]["logit_weighted"] = lr(mw)
R["t1"]["verdict"] = verdict(ci[0], ci[1], 0.80, None)

# =============================== TEST 2: interaction ===============================
d2 = CF[CF["marital-status"].isin(["Married-civ-spouse", "Never-married"])].copy()
d2["male"] = 1 - d2.female
d2["married"] = (d2["marital-status"] == "Married-civ-spouse").astype(int)
d2["h"] = d2["hours-per-week"].astype(float)
R["t2_n"] = len(d2)
R["t2_cells"] = {f"{int(k[0])}{int(k[1])}": int(v) for k, v in d2.groupby(["married", "male"]).size().items()}
ols = smf.ols("h ~ male * married", data=d2).fit(cov_type="HC3", use_t=True)
olsc = smf.ols("h ~ male * married", data=d2).fit()
ct = ols.conf_int().loc["male:married"]
gap = lambda g: g[g.male == 1].h.mean() - g[g.male == 0].h.mean()
gm, gn = gap(d2[d2.married == 1]), gap(d2[d2.married == 0])
D = gm - gn
assert abs(D - ols.params["male:married"]) < 1e-8
R["t2"] = dict(D=float(D), ci_lo=float(ct[0]), ci_hi=float(ct[1]), t=float(ols.tvalues["male:married"]),
               df=int(ols.df_resid), p=float(ols.pvalues["male:married"]), gap_married=float(gm), gap_never=float(gn))
R["t2"]["means"] = {f"{int(k[0])}{int(k[1])}": float(v) for k, v in d2.groupby(["married", "male"]).h.mean().items()}
cells = [d2[(d2.married == a) & (d2.male == b)].h for a in (0, 1) for b in (0, 1)]
R["t2"]["cell_sd"] = [float(c_.std(ddof=1)) for c_ in cells]
bf = ss.levene(*cells, center="median")
R["t2"]["brown_forsythe"] = dict(stat=float(bf.statistic), p=float(bf.pvalue))
R["t2"]["se_D"] = float(ols.bse["male:married"])
R["t2"]["classic_ols"] = dict(t=float(olsc.tvalues["male:married"]), df=int(olsc.df_resid), p=float(olsc.pvalues["male:married"]))
# permutation test: shuffle sex within marital group
h = d2.h.to_numpy(); mar = d2.married.to_numpy(); sx = d2.male.to_numpy()
idx = {g: np.where(mar == g)[0] for g in (0, 1)}
def stat(sxv):
    out = []
    for g in (1, 0):
        i = idx[g]; s = sxv[i]; hh = h[i]
        out.append(hh[s == 1].mean() - hh[s == 0].mean())
    return out[0] - out[1]
B = 10_000; perm = np.empty(B)
for b in range(B):
    s2 = sx.copy()
    for g in (0, 1):
        s2[idx[g]] = rng.permutation(sx[idx[g]])
    perm[b] = stat(s2)
R["t2"]["perm"] = dict(B=B, p=float((1 + (np.abs(perm) >= abs(D) - 1e-12).sum()) / (B + 1)), null_sd=float(perm.std()))
# two Welch tests, one per group, and a Wald z on the difference of the two gaps
wel = {}
for g, name in [(1, "married"), (0, "never")]:
    x = d2[(d2.married == g) & (d2.male == 1)].h; y = d2[(d2.married == g) & (d2.male == 0)].h
    r = ss.ttest_ind(x, y, equal_var=False); cI = r.confidence_interval()
    se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
    wel[name] = dict(gap=float(x.mean() - y.mean()), ci_lo=float(cI.low), ci_hi=float(cI.high), t=float(r.statistic),
                     df=float(r.df), p=float(r.pvalue), se=float(se))
zD = (wel["married"]["gap"] - wel["never"]["gap"]) / np.hypot(wel["married"]["se"], wel["never"]["se"])
wel["wald_z_on_D"] = dict(z=float(zD), p=float(2 * ss.norm.sf(abs(zD))))
R["t2"]["welch"] = wel
R["t2"]["verdict"] = verdict(ct[0], ct[1], -2.0, 2.0)

# =============================== TEST 3: Mann-Whitney ===============================
x = CF.loc[CF["capital-gain"] > 0, "hours-per-week"].to_numpy()
y = CF.loc[CF["capital-gain"] == 0, "hours-per-week"].to_numpy()
mw_ = ss.mannwhitneyu(x, y, alternative="two-sided", method="asymptotic", use_continuity=True)
N = len(x) + len(y)
_, tc = np.unique(np.concatenate([x, y]), return_counts=True)
sigma = np.sqrt(len(x) * len(y) / 12 * ((N + 1) - (tc ** 3 - tc).sum() / (N * (N - 1))))
zU = (mw_.statistic - len(x) * len(y) / 2 - 0.5 * np.sign(mw_.statistic - len(x) * len(y) / 2)) / sigma
def hl(hx, hy):
    """Hodges-Lehmann shift from integer histograms: median of all pairwise differences x - y."""
    diff = np.convolve(hx, hy[::-1])                      # index k <-> difference k - (len(hy)-1)
    vals = np.arange(len(diff)) - (len(hy) - 1)
    cum = np.cumsum(diff); tot = cum[-1]
    lo = vals[np.searchsorted(cum, (tot + 1) // 2)]
    hi = vals[np.searchsorted(cum, tot // 2 + 1)]
    return (lo + hi) / 2
hx = np.bincount(x, minlength=100).astype(float); hy = np.bincount(y, minlength=100).astype(float)
hl_est = hl(hx, hy)
boots = []
for _ in range(2000):
    bx = rng.multinomial(len(x), hx / hx.sum()).astype(float)
    by = rng.multinomial(len(y), hy / hy.sum()).astype(float)
    boots.append(hl(bx, by))
hl_ci = np.percentile(boots, [2.5, 97.5])
wt = ss.ttest_ind(x, y, equal_var=False); wci = wt.confidence_interval()
bm = ss.brunnermunzel(x, y)
R["t3"] = dict(n_gain=len(x), n_nogain=len(y), U=float(mw_.statistic), z=float(zU), p=float(mw_.pvalue),
               prob_superiority=float(mw_.statistic / (len(x) * len(y))), hl=float(hl_est),
               ci_lo=float(hl_ci[0]), ci_hi=float(hl_ci[1]),
               median_gain=float(np.median(x)), median_nogain=float(np.median(y)),
               mean_gain=float(x.mean()), mean_nogain=float(y.mean()),
               welch=dict(diff=float(x.mean() - y.mean()), ci_lo=float(wci.low), ci_hi=float(wci.high),
                          t=float(wt.statistic), df=float(wt.df), p=float(wt.pvalue)),
               brunner_munzel=dict(stat=float(bm.statistic), p=float(bm.pvalue)))
R["t3"]["verdict"] = verdict(hl_ci[0], hl_ci[1], -2.0, 2.0)
R["t3"]["welch_verdict"] = verdict(wci.low, wci.high, -2.0, 2.0)   # comparator, not the pre-registered verdict
R["t3"]["share_exactly_40"] = dict(gain=float((x == 40).mean()), nogain=float((y == 40).mean()))
R["t3"]["share_over_40"] = dict(gain=float((x > 40).mean()), nogain=float((y > 40).mean()))   # descriptive, not pre-registered
R["t3"]["share_under_40"] = dict(gain=float((x < 40).mean()), nogain=float((y < 40).mean()))

# =============================== TEST 4: chi-square ===============================
d4 = CF[CF.workclass != "Unknown"].copy()
R["t4_rows_unknown_dropped"] = int(len(CF) - len(d4))
d4["wc"] = d4.workclass.replace({"Never-worked": "No-pay", "Without-pay": "No-pay"})
R["t4_n_nopay"] = int((d4.wc == "No-pay").sum())
tab = pd.crosstab(d4.wc, d4.income_high)
chi = ss.chi2_contingency(tab.values, correction=False)
Eexp = chi[3]
nn = tab.values.sum(); k = min(tab.shape) - 1
Vc = float(np.sqrt(chi[0] / (nn * k)))
code = pd.factorize(d4.wc)[0]; yv = d4.income_high.to_numpy(); L = code.max() + 1
def cv(cc, yy):
    t = np.bincount(cc * 2 + yy, minlength=L * 2).reshape(L, 2).astype(float)
    e = np.outer(t.sum(1), t.sum(0)) / t.sum()
    return np.sqrt(((t - e) ** 2 / e).sum() / (t.sum() * 1)), ((t - e) ** 2 / e).sum()
bv = []
for _ in range(2000):
    ii = rng.integers(0, nn, nn); bv.append(cv(code[ii], yv[ii])[0])
vci = np.percentile(bv, [2.5, 97.5])
G = ss.chi2_contingency(tab.values, correction=False, lambda_="log-likelihood")
Bm = 10_000; ge = 0
for _ in range(Bm):
    ge += cv(code, rng.permutation(yv))[1] >= chi[0] - 1e-9
R["t4"] = dict(n=int(nn), levels=int(tab.shape[0]), chi2=float(chi[0]), df=int(chi[2]), p=float(chi[1]), V=Vc,
               ci_lo=float(vci[0]), ci_hi=float(vci[1]),
               g=dict(stat=float(G[0]), df=int(G[2]), p=float(G[1])),
               montecarlo=dict(B=Bm, p=float((1 + ge) / (Bm + 1))),
               cochran=dict(min_expected=float(Eexp.min()), cells=int(Eexp.size),
                            cells_below5=int((Eexp < 5).sum()), cells_below1=int((Eexp < 1).sum())),
               rates={k_: round(float(v), 4) for k_, v in d4.groupby("wc").income_high.mean().items()},
               counts={k_: int(v) for k_, v in d4.wc.value_counts().items()})
R["t4"]["verdict"] = verdict(vci[0], vci[1], 0.10, 0.10) if False else (
    "matters" if vci[0] >= 0.10 else ("does not matter" if vci[1] < 0.10 else "inconclusive"))

# =============================== Holm ===============================
praw = [R["t1"]["p_one_sided"], R["t2"]["p"], R["t3"]["p"], R["t4"]["p"]]
rej, padj, _, _ = multipletests(praw, alpha=0.05, method="holm")
for i, key in enumerate(["t1", "t2", "t3", "t4"]):
    R[key]["p_holm"] = float(padj[i]); R[key]["reject_holm"] = bool(rej[i])

# =============================== summary figure ===============================
def lg(o): return np.log(o) / np.log(0.80)
rows = [("T1 odds ratio (women/men)", lg(R["t1"]["or_mh"]), lg(R["t1"]["ci_hi"]), lg(R["t1"]["ci_lo"])),
        ("T2 gap difference (h)", R["t2"]["D"] / 2, R["t2"]["ci_lo"] / 2, R["t2"]["ci_hi"] / 2),
        ("T3 shift in hours (HL)", R["t3"]["hl"] / 2, R["t3"]["ci_lo"] / 2, R["t3"]["ci_hi"] / 2),
        ("T3 mean diff (Welch)", R["t3"]["welch"]["diff"] / 2, R["t3"]["welch"]["ci_lo"] / 2, R["t3"]["welch"]["ci_hi"] / 2),
        ("T4 Cramer's V", Vc / 0.10, vci[0] / 0.10, vci[1] / 0.10)]
fig, ax = plt.subplots(figsize=(3.3, 1.7))
plt.rcParams.update({"font.size": 6.5})
ax.axvspan(-1, 1, color="#dddddd", lw=0)
for i, (lab, e, lo, hi) in enumerate(rows[::-1]):
    ax.plot([lo, hi], [i, i], color="#222222", lw=1.2); ax.plot(e, i, "o", color="#0072B2", ms=3.5)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=6)
ax.axvline(0, color="grey", lw=.5); ax.set_xlabel("estimate / smallest difference that matters", fontsize=6.5)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(pad=0.3); fig.savefig(FIG / "fig_forest.pdf"); plt.close(fig)
R["forest_rows"] = [(r[0], float(r[1]), float(r[2]), float(r[3])) for r in rows]

(OUT / "test_results.json").write_text(json.dumps(R, indent=2, default=float))
print(json.dumps(R, indent=2, default=float))
