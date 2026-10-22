"""Step 2: EDA on the EXPLORATION half only. The confirmation half is never read here.

Run: uv run python 02_explore.py
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.stats.contingency_tables import StratifiedTable
from common import OUT, FIG, SEED

df_all = pd.read_parquet(OUT / "clean.parquet")
df = df_all[df_all.split == "explore"].copy()
del df_all                      # make sure nothing below can touch the confirmation half
assert (df.split == "explore").all()

plt.rcParams.update({"font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7,
                     "legend.fontsize": 6.5, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 150})
W, M = "#D55E00", "#0072B2"
S = {"n": len(df)}

# ---------- basic questions (obvious ones) ----------
S["rate_women"] = float(df.loc[df.female == 1, "income_high"].mean())
S["rate_men"] = float(df.loc[df.female == 0, "income_high"].mean())
S["n_women"] = int(df.female.sum()); S["n_men"] = int((1 - df.female).sum())
S["corr_age_income"] = float(df.age.corr(df.income_high))
S["corr_edunum_income"] = float(df["education-num"].corr(df.income_high))
S["rate_by_band"] = df.groupby("edu_band").income_high.mean().round(4).to_dict()

# ---------- Fig 1: income by sex x education band ----------
g = df.groupby(["edu_band", "sex"]).income_high.agg(["mean", "size"]).reset_index()
bands = sorted(df.edu_band.unique())
fig, ax = plt.subplots(figsize=(3.3, 1.95))
x = np.arange(len(bands)); w = 0.38
for k, (sx, col) in enumerate([("Female", W), ("Male", M)]):
    v = [g[(g.edu_band == b) & (g.sex == sx)]["mean"].iloc[0] * 100 for b in bands]
    ax.bar(x + (k - .5) * w, v, w, color=col, label="Women" if sx == "Female" else "Men")
    for xi, vi in zip(x + (k - .5) * w, v):
        ax.text(xi, vi + 1, f"{vi:.0f}", ha="center", fontsize=5.5)
ax.set_xticks(x); ax.set_xticklabels([b[2:] for b in bands])
ax.set_ylabel("Income >50K (%)"); ax.legend(frameon=False, loc="upper left")
fig.tight_layout(pad=0.3); fig.savefig(FIG / "fig_income_band.pdf"); plt.close(fig)
S["band_rates"] = {f"{r.edu_band}|{r.sex}": [round(float(r['mean']), 4), int(r['size'])] for _, r in g.iterrows()}
S["band_gap_pts"] = {b: round(100 * (g[(g.edu_band == b) & (g.sex == "Male")]["mean"].iloc[0]
                    - g[(g.edu_band == b) & (g.sex == "Female")]["mean"].iloc[0]), 1) for b in bands}

# ---------- Fig 2: hours by sex (ECDF: round-number heaping makes histograms spiky) ----------
fig, ax = plt.subplots(figsize=(3.3, 1.8))
for sx, col, lab in [("Female", W, "Women"), ("Male", M, "Men")]:
    h = np.sort(df.loc[df.sex == sx, "hours-per-week"].to_numpy())
    ax.step(h, np.arange(1, len(h) + 1) / len(h), where="post", color=col, lw=1.1, label=lab)
ax.axvline(40, color="grey", lw=.6, ls=":")
ax.set_xlim(0, 100); ax.set_xlabel("Hours per week"); ax.set_ylabel("Share working up to x hours")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout(pad=0.3); fig.savefig(FIG / "fig_hours.pdf"); plt.close(fig)
for sx in ["Female", "Male"]:
    h = df.loc[df.sex == sx, "hours-per-week"]
    S[f"hours_{sx}"] = {"mean": round(float(h.mean()), 2), "median": float(h.median()),
                        "sd": round(float(h.std()), 2), "share40": round(float((h == 40).mean()), 4),
                        "share_lt40": round(float((h < 40).mean()), 4), "share_gt40": round(float((h > 40).mean()), 4),
                        "skew": round(float(h.skew()), 2)}

# ---------- Fig 3: capital gain on log scale ----------
pos = df.loc[df["capital-gain"] > 0, "capital-gain"]
fig, ax = plt.subplots(figsize=(3.3, 1.8))
ax.hist(np.log10(pos[pos < 99999]), bins=40, color="#555555")
ax.axvline(np.log10(99999), color="#CC0000", lw=1)
ax.text(np.log10(99999) - 0.05, ax.get_ylim()[1] * .85, f"99,999: {int((pos == 99999).sum())} rows",
        color="#CC0000", ha="right", fontsize=6)
ax.set_xlabel("capital gain, log10 USD (rows with a gain)"); ax.set_ylabel("Rows")
fig.tight_layout(pad=0.3); fig.savefig(FIG / "fig_gain.pdf"); plt.close(fig)
S["gain_pos_share"] = round(float((df["capital-gain"] > 0).mean()), 4)
S["gain_pos_n"] = int((df["capital-gain"] > 0).sum())
S["gain_99999_n"] = int((df["capital-gain"] == 99999).sum())
S["gain_99999_income_high"] = round(float(df.loc[df["capital-gain"] == 99999, "income_high"].mean()), 4)
S["gain_skew"] = round(float(df["capital-gain"].skew()), 1)
S["gain_zero_hours_median"] = float(df.loc[df["capital-gain"] == 0, "hours-per-week"].median())
S["gain_pos_hours_median"] = float(df.loc[df["capital-gain"] > 0, "hours-per-week"].median())
S["gain_zero_hours_mean"] = round(float(df.loc[df["capital-gain"] == 0, "hours-per-week"].mean()), 2)
S["gain_pos_hours_mean"] = round(float(df.loc[df["capital-gain"] > 0, "hours-per-week"].mean()), 2)

# ---------- Fig 4: Unknown values ----------
cols = ["workclass", "occupation", "native-country"]
unk = {c: int((df[c] == "Unknown").sum()) for c in cols}
fig, ax = plt.subplots(figsize=(3.3, 1.35))
ax.barh(cols[::-1], [100 * unk[c] / len(df) for c in cols[::-1]], color="#555555")
for i, c in enumerate(cols[::-1]):
    ax.text(100 * unk[c] / len(df) + .1, i, f"{unk[c]}", va="center", fontsize=6)
ax.set_xlabel("Unknown (%)"); ax.set_xlim(0, 7)
fig.tight_layout(pad=0.3); fig.savefig(FIG / "fig_unknown.pdf"); plt.close(fig)
S["unknown_counts"] = unk
S["unknown_wc_and_occ"] = int(((df.workclass == "Unknown") & (df.occupation == "Unknown")).sum())
S["unknown_wc_income"] = round(float(df.loc[df.workclass == "Unknown", "income_high"].mean()), 4)
S["known_wc_income"] = round(float(df.loc[df.workclass != "Unknown", "income_high"].mean()), 4)
S["unknown_wc_age_median"] = float(df.loc[df.workclass == "Unknown", "age"].median())
S["known_wc_age_median"] = float(df.loc[df.workclass != "Unknown", "age"].median())

# ---------- feasibility checks for the four problem statements (exploration half only) ----------
# P1: how sparse are the occupation x band strata?
d1 = df[df.occupation != "Unknown"]
cell = d1.groupby(["occupation", "edu_band", "female"]).size().unstack(fill_value=0)
both = cell[(cell.get(0, 0) > 0) & (cell.get(1, 0) > 0)]
S["p1_rows"] = len(d1); S["p1_strata_all"] = int(len(cell)); S["p1_strata_both_sexes"] = int(len(both))
S["p1_rows_kept"] = int(both.sum().sum())
tabs = []
for (o, b), _ in both.iterrows():
    s = d1[(d1.occupation == o) & (d1.edu_band == b)]
    t = pd.crosstab(s.female, s.income_high).reindex(index=[1, 0], columns=[1, 0], fill_value=0)
    tabs.append(t.values)
st = StratifiedTable(tabs)
S["p1_explore_or_mh"] = round(float(st.oddsratio_pooled), 3)
S["p1_explore_crude_or"] = round(float((d1.female.eq(1) & d1.income_high.eq(1)).sum() * (d1.female.eq(0) & d1.income_high.eq(0)).sum()
                                 / ((d1.female.eq(1) & d1.income_high.eq(0)).sum() * (d1.female.eq(0) & d1.income_high.eq(1)).sum())), 3)
# P2: sizes of the four cells
d2 = df[df["marital-status"].isin(["Married-civ-spouse", "Never-married"])]
S["p2_cell_n"] = {f"{a}|{b}": int(n) for (a, b), n in d2.groupby(["marital-status", "sex"]).size().items()}
S["p2_cell_mean_hours"] = {f"{a}|{b}": round(float(v), 2) for (a, b), v in d2.groupby(["marital-status", "sex"])["hours-per-week"].mean().items()}
# P4: workclass levels
S["p4_workclass_n"] = df.workclass.value_counts().to_dict()
S["p4_workclass_rate"] = df.groupby("workclass").income_high.mean().round(3).to_dict()
(OUT / "explore_stats.json").write_text(json.dumps(S, indent=2))
print(json.dumps(S, indent=2))
