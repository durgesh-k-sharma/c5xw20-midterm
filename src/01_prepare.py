"""Step 1: read raw data, clean, encode, size check, split. Writes outputs/*.

Run: uv run python src/01_prepare.py
"""
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from common import RAW, OUT, COLS, CAT, NUM, EDU_BAND, SEED

stats = {}

# ---------- read raw (no header in file; " ?" means missing) ----------
raw = pd.read_csv(RAW, header=None, names=COLS, skipinitialspace=True)
stats["raw_rows"], stats["raw_cols"] = raw.shape
stats["raw_cells"] = int(raw.shape[0] * raw.shape[1])
qmask = raw[CAT + ["income"]] == "?"
stats["raw_q_cells"] = int(qmask.values.sum())
stats["raw_q_by_col"] = {c: int(qmask[c].sum()) for c in qmask.columns if qmask[c].sum() > 0}
stats["raw_rows_with_q"] = int(qmask.any(axis=1).sum())
stats["raw_q_workclass_and_occupation"] = int(((raw.workclass == "?") & (raw.occupation == "?")).sum())
stats["raw_dups"] = int(raw.duplicated().sum())
stats["raw_dups_ignoring_fnlwgt"] = int(raw.drop(columns="fnlwgt").duplicated().sum())
stats["raw_income_gt50k_share"] = float((raw.income == ">50K").mean())
stats["edu_one_to_one"] = bool(raw.groupby("education")["education-num"].nunique().eq(1).all()
                               and raw.groupby("education-num")["education"].nunique().eq(1).all())

def iqr_out(s):
    q1, q3 = s.quantile([.25, .75]); i = q3 - q1
    return int(((s < q1 - 1.5 * i) | (s > q3 + 1.5 * i)).sum())

stats["raw_iqr_outliers"] = {c: iqr_out(raw[c]) for c in NUM}
stats["raw_top_age90"] = int((raw.age == 90).sum())
stats["raw_top_hours99"] = int((raw["hours-per-week"] == 99).sum())
stats["raw_top_gain99999"] = int((raw["capital-gain"] == 99999).sum())
stats["raw_gain_positive"] = int((raw["capital-gain"] > 0).sum())
stats["raw_loss_positive"] = int((raw["capital-loss"] > 0).sum())

# ---------- clean ----------
df = raw.replace("?", "Unknown").drop_duplicates().reset_index(drop=True)
df["income_high"] = (df.income == ">50K").astype(int)
df["female"] = (df.sex == "Female").astype(int)
df["edu_band"] = df.education.map(EDU_BAND)
assert df.edu_band.notna().all()
df["flag_gain_topcode"] = (df["capital-gain"] == 99999).astype(int)
df["flag_hours_topcode"] = (df["hours-per-week"] == 99).astype(int)
df["flag_age_topcode"] = (df.age == 90).astype(int)
df["unknown_any"] = (df[CAT] == "Unknown").any(axis=1).astype(int)

stats["clean_rows"] = len(df)
stats["clean_dups"] = int(df.duplicated(subset=COLS).sum())
stats["clean_unknown_cells"] = int((df[CAT] == "Unknown").values.sum())
stats["clean_unknown_by_col"] = {c: int((df[c] == "Unknown").sum()) for c in CAT if (df[c] == "Unknown").any()}
stats["clean_rows_with_unknown"] = int(df.unknown_any.sum())
stats["clean_iqr_outliers_kept"] = {c: iqr_out(df[c]) for c in NUM}
stats["levels"] = {c: int(df[c].nunique()) for c in CAT}

# ---------- encode + size check ----------
enc = pd.get_dummies(df[CAT], dtype="int8")
enc = pd.concat([df[NUM].reset_index(drop=True), enc], axis=1)
stats["n_onehot_cols"] = int(enc.shape[1] - len(NUM))
stats["n_features_encoded"] = int(enc.shape[1])
stats["encoded_rows"] = int(enc.shape[0])
stats["size_product"] = int(enc.shape[0] * enc.shape[1])
stats["size_ok"] = bool(stats["size_product"] >= 3_000_000)
stats["size_product_raw_after_dedup"] = int(len(df) * 15)
# the same count if we had dropped Unknown rows and `education` (for the report)
alt = df[df.unknown_any == 0]
alt_cols = sum(alt[c].nunique() for c in CAT if c != "education") + len(NUM)
stats["alt_drop_rows"] = int(len(alt)); stats["alt_cols"] = int(alt_cols)
stats["alt_product"] = int(len(alt) * alt_cols)

# ---------- split BEFORE any exploration ----------
idx_e, idx_c = train_test_split(df.index, test_size=0.5, stratify=df.income_high,
                                random_state=SEED, shuffle=True)
df["split"] = "explore"
df.loc[idx_c, "split"] = "confirm"
stats["split_seed"] = SEED
stats["n_explore"] = int((df.split == "explore").sum())
stats["n_confirm"] = int((df.split == "confirm").sum())
stats["rate_explore"] = float(df.loc[df.split == "explore", "income_high"].mean())
stats["rate_confirm"] = float(df.loc[df.split == "confirm", "income_high"].mean())

# ---------- data dictionary ----------
meaning = {
    "age": ("discrete", "years", "age of the person"),
    "workclass": ("nominal", "-", "type of employer"),
    "fnlwgt": ("continuous", "people", "census weight: people this row stands for"),
    "education": ("nominal", "-", "highest education level (16 levels)"),
    "education-num": ("discrete", "level 1-16", "ordinal code of `education`"),
    "marital-status": ("nominal", "-", "marital status"),
    "occupation": ("nominal", "-", "job type"),
    "relationship": ("nominal", "-", "role in the household"),
    "race": ("nominal", "-", "race"),
    "sex": ("nominal", "-", "sex (Female or Male)"),
    "capital-gain": ("continuous", "USD (1994)", "yearly capital gains"),
    "capital-loss": ("continuous", "USD (1994)", "yearly capital losses"),
    "hours-per-week": ("discrete", "hours", "usual working hours per week"),
    "native-country": ("nominal", "-", "country of birth"),
    "income": ("nominal", "-", "response: yearly income >50K or <=50K"),
}
rows = []
for c in COLS:
    s = raw[c]
    rng = f"{s.min()} to {s.max()}" if c in NUM else f"{s.nunique() - int((s == '?').any())} levels"
    miss = int((s == "?").sum())
    rows.append(dict(attribute=c, type=meaning[c][0], unit=meaning[c][1], range_or_levels=rng,
                     missing_raw=miss, missing_pct=round(100 * miss / len(raw), 2),
                     meaning=meaning[c][2]))
pd.DataFrame(rows).to_csv(OUT / "data_dictionary.csv", index=False)

df.to_parquet(OUT / "clean.parquet", index=False)
enc.to_parquet(OUT / "encoded_features.parquet", index=False)
(OUT / "prep_stats.json").write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
