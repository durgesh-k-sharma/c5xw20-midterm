"""Step 4: turn the JSON outputs into LaTeX macros, so no number in the report is typed by hand.

Run: uv run python 04_macros.py   (writes report/numbers.tex)
"""
import json
from common import OUT, ROOT

P = json.load(open(OUT / "prep_stats.json"))
X = json.load(open(OUT / "explore_stats.json"))
T = json.load(open(OUT / "test_results.json"))
lines = []

def put(name, text):
    lines.append("\\newcommand{\\%s}{%s}" % (name, text))

def i(n):                       # 32561 -> 32{,}561
    return f"{int(round(n)):,}".replace(",", "{,}")

def f(x, d=2):                  # float with d decimals; real minus sign in math mode
    s = f"{x:.{d}f}"
    return "\\ensuremath{-}" + s[1:] if s.startswith("-") else s

def pc(x, d=1):                 # share -> percent string
    return f(100 * x, d)

def pv(p):                      # p-value
    if p < 1e-4:
        m, e = f"{p:.1e}".split("e")
        return f"\\ensuremath{{{m}\\times10^{{{int(e)}}}}}"
    return f"{p:.4f}" if p < 0.01 else f"{p:.3f}"

def lt(p, B):                   # Monte Carlo p-value: the smallest possible value is 1/(B+1)
    return "\\ensuremath{<10^{-4}}"

# ---------------- preparation ----------------
for k, v in dict(RawRows=P["raw_rows"], RawCols=P["raw_cols"], RawCells=P["raw_cells"], RawDups=P["raw_dups"],
                 RawDupsNoW=P["raw_dups_ignoring_fnlwgt"], RawQCells=P["raw_q_cells"], RawQRows=P["raw_rows_with_q"],
                 RawQWC=P["raw_q_by_col"]["workclass"], RawQOcc=P["raw_q_by_col"]["occupation"],
                 RawQNat=P["raw_q_by_col"]["native-country"], RawQBoth=P["raw_q_workclass_and_occupation"],
                 CleanRows=P["clean_rows"], CleanCols=P["n_features_encoded"], CleanCells=P["size_product"],
                 OneHot=P["n_onehot_cols"], CleanUnkCells=P["clean_unknown_cells"], CleanUnkRows=P["clean_rows_with_unknown"],
                 AltRows=P["alt_drop_rows"], AltCols=P["alt_cols"], AltCells=P["alt_product"],
                 TopAge=P["raw_top_age90"], TopHours=P["raw_top_hours99"], TopGain=P["raw_top_gain99999"],
                 GainPos=P["raw_gain_positive"], LossPos=P["raw_loss_positive"],
                 IqrHours=P["clean_iqr_outliers_kept"]["hours-per-week"], IqrGain=P["clean_iqr_outliers_kept"]["capital-gain"],
                 IqrFnl=P["clean_iqr_outliers_kept"]["fnlwgt"], IqrAge=P["clean_iqr_outliers_kept"]["age"],
                 NExplore=P["n_explore"], NConfirm=P["n_confirm"], SizeFloor=3000000).items():
    put(k, i(v))
put("SplitSeed", str(P["split_seed"]))
put("RateExplore", pc(P["rate_explore"], 2)); put("RateConfirm", pc(P["rate_confirm"], 2))
put("RawHighShare", pc(P["raw_income_gt50k_share"], 1))
put("RowsLostPct", pc(1 - P["clean_rows"] / P["raw_rows"], 2))
put("UnkRowsPct", pc(P["clean_rows_with_unknown"] / P["clean_rows"], 1))
put("AltDropPct", pc(1 - P["alt_drop_rows"] / P["clean_rows"], 1))
put("IqrHoursPct", pc(P["clean_iqr_outliers_kept"]["hours-per-week"] / P["clean_rows"], 0))
put("TrainShare", pc(P["raw_rows"] / 48842, 1))

# ---------------- exploration ----------------
put("ExpN", i(X["n"])); put("ExpRateW", pc(X["rate_women"])); put("ExpRateM", pc(X["rate_men"]))
put("ExpNW", i(X["n_women"])); put("ExpNM", i(X["n_men"]))
put("ExpCorrAge", f(X["corr_age_income"], 2)); put("ExpCorrEdu", f(X["corr_edunum_income"], 2))
bands = ["1 Below HS", "2 HS grad", "3 Some college", "4 Bachelors+"]
for nm, b in zip(["BandOne", "BandTwo", "BandThree", "BandFour"], bands):
    put(nm + "Gap", f(X["band_gap_pts"][b], 1))
    put(nm + "Rate", pc(X["rate_by_band"][b], 1))
put("ExpHoursW", f(X["hours_Female"]["mean"], 1)); put("ExpHoursM", f(X["hours_Male"]["mean"], 1))
put("ExpUnderW", pc(X["hours_Female"]["share_lt40"])); put("ExpUnderM", pc(X["hours_Male"]["share_lt40"]))
put("ExpOverW", pc(X["hours_Female"]["share_gt40"])); put("ExpOverM", pc(X["hours_Male"]["share_gt40"]))
put("ExpFortyW", pc(X["hours_Female"]["share40"], 0)); put("ExpFortyM", pc(X["hours_Male"]["share40"], 0))
put("ExpGainShare", pc(X["gain_pos_share"])); put("ExpGainN", i(X["gain_pos_n"]))
put("ExpTopN", i(X["gain_99999_n"])); put("ExpTopHigh", pc(X["gain_99999_income_high"], 0))
put("ExpGainSkew", f(X["gain_skew"], 1))
put("ExpUnkWC", i(X["unknown_counts"]["workclass"])); put("ExpUnkOcc", i(X["unknown_counts"]["occupation"]))
put("ExpUnkNat", i(X["unknown_counts"]["native-country"])); put("ExpUnkBoth", i(X["unknown_wc_and_occ"]))
put("ExpUnkPct", pc(X["unknown_wc_and_occ"] / X["n"]))
put("ExpUnkHigh", pc(X["unknown_wc_income"])); put("ExpKnownHigh", pc(X["known_wc_income"]))
put("ExpOneStrata", i(X["p1_strata_all"])); put("ExpOneBoth", i(X["p1_strata_both_sexes"]))
put("ExpOneOR", f(X["p1_explore_or_mh"], 2)); put("ExpOneCrude", f(X["p1_explore_crude_or"], 2))

# ---------------- tests ----------------
t1, t2, t3, t4 = T["t1"], T["t2"], T["t3"], T["t4"]
put("NConfirmUsed", i(T["n_confirm"])); put("PreregCommit", T["prereg_commit"].split()[0])
put("TOneRowsUnk", i(T["t1_rows_unknown_occ_dropped"])); put("TOneRows", i(T["t1_rows_used"]))
put("TOneStrataAll", i(T["t1_strata_all"])); put("TOneStrata", i(T["t1_strata_used"]))
put("TOneLostRows", i(T["t1_rows_lost_one_sex_strata"]))
put("TOneNW", i(T["t1_n_women"])); put("TOneNM", i(T["t1_n_men"]))
put("TOneRateW", pc(T["t1_rate_women"])); put("TOneRateM", pc(T["t1_rate_men"]))
put("TOneOR", f(t1["or_mh"], 3)); put("TOneLo", f(t1["ci_lo"], 3)); put("TOneHi", f(t1["ci_hi"], 3))
put("TOneChi", f(t1["chi2"], 1)); put("TOneZ", f(t1["z"], 1)); put("TOneP", pv(t1["p_one_sided"]))
put("TOneHolm", pv(t1["p_holm"]))
put("TOneRR", f(t1["rr_pooled"], 2))
put("TOneCrudeChi", f(t1["crude"]["chi2"], 1)); put("TOneCrudeP", pv(t1["crude"]["p_two_sided"]))
put("TOneCrudeOR", f(t1["crude"]["or_crude"], 3)); put("TOneCrudeLo", f(t1["crude"]["ci_lo"], 3)); put("TOneCrudeHi", f(t1["crude"]["ci_hi"], 3))
put("TOneLogOR", f(t1["logit"]["or_"], 3)); put("TOneLogLo", f(t1["logit"]["ci_lo"], 3)); put("TOneLogHi", f(t1["logit"]["ci_hi"], 3))
put("TOneLogZ", f(t1["logit"]["z"], 1)); put("TOneLogRows", i(t1["logit"]["rows"])); put("TOneLogStrata", i(t1["logit"]["strata"]))
put("TOneWOR", f(t1["logit_weighted"]["or_"], 3)); put("TOneWLo", f(t1["logit_weighted"]["ci_lo"], 3)); put("TOneWHi", f(t1["logit_weighted"]["ci_hi"], 3))
bd = t1["breslow_day_tarone"]
put("TOneBD", f(bd["stat"], 1)); put("TOneBDdf", i(bd["df"])); put("TOneBDp", pv(bd["p"]))
put("TOneDefined", i(t1["strata_or_defined"])); put("TOneBelow", i(t1["strata_or_below_1"]))
put("TTwoN", i(T["t2_n"]))
put("TTwoD", f(t2["D"], 2)); put("TTwoLo", f(t2["ci_lo"], 2)); put("TTwoHi", f(t2["ci_hi"], 2))
put("TTwoT", f(t2["t"], 2)); put("TTwoDf", i(t2["df"])); put("TTwoP", pv(t2["p"])); put("TTwoHolm", pv(t2["p_holm"]))
put("TTwoSdMin", f(min(t2["cell_sd"]), 1)); put("TTwoSdMax", f(max(t2["cell_sd"]), 1))
put("TTwoBFp", pv(t2["brown_forsythe"]["p"])); put("TTwoBF", f(t2["brown_forsythe"]["stat"], 1))
put("TTwoSE", f(t2["se_D"], 2)); put("TTwoMDE", f(2.8 * t2["se_D"], 1))
put("TTwoMeanNW", f(t2["means"]["00"], 1)); put("TTwoMeanNM", f(t2["means"]["01"], 1))
put("TTwoMeanMW", f(t2["means"]["10"], 1)); put("TTwoMeanMM", f(t2["means"]["11"], 1))
put("TTwoGapM", f(t2["gap_married"], 2)); put("TTwoGapN", f(t2["gap_never"], 2))
put("TTwoClassT", f(t2["classic_ols"]["t"], 2)); put("TTwoClassP", pv(t2["classic_ols"]["p"]))
put("TTwoPermP", lt(t2["perm"]["p"], t2["perm"]["B"])); put("TTwoPermSD", f(t2["perm"]["null_sd"], 2))
w = t2["welch"]
put("TTwoWmGap", f(w["married"]["gap"], 2)); put("TTwoWmLo", f(w["married"]["ci_lo"], 2)); put("TTwoWmHi", f(w["married"]["ci_hi"], 2))
put("TTwoWnGap", f(w["never"]["gap"], 2)); put("TTwoWnLo", f(w["never"]["ci_lo"], 2)); put("TTwoWnHi", f(w["never"]["ci_hi"], 2))
put("TTwoWaldZ", f(w["wald_z_on_D"]["z"], 2)); put("TTwoWaldP", pv(w["wald_z_on_D"]["p"]))
for key, nm in [("00", "NW"), ("01", "NM"), ("10", "MW"), ("11", "MM")]:
    put("TTwoCell" + nm, i(T["t2_cells"][key]))
put("TThreeNG", i(t3["n_gain"])); put("TThreeNN", i(t3["n_nogain"]))
put("TThreeU", i(t3["U"])); put("TThreeZ", f(t3["z"], 2)); put("TThreeP", pv(t3["p"])); put("TThreeHolm", pv(t3["p_holm"]))
put("TThreePS", f(t3["prob_superiority"], 3)); put("TThreeHL", f(t3["hl"], 1))
put("TThreeLo", f(t3["ci_lo"], 1)); put("TThreeHi", f(t3["ci_hi"], 1))
put("TThreeMedG", f(t3["median_gain"], 0)); put("TThreeMedN", f(t3["median_nogain"], 0))
put("TThreeMeanG", f(t3["mean_gain"], 1)); put("TThreeMeanN", f(t3["mean_nogain"], 1))
put("TThreeFortyG", pc(t3["share_exactly_40"]["gain"], 0)); put("TThreeFortyN", pc(t3["share_exactly_40"]["nogain"], 0))
put("TThreeOverG", pc(t3["share_over_40"]["gain"], 0)); put("TThreeOverN", pc(t3["share_over_40"]["nogain"], 0))
put("TThreeUnderG", pc(t3["share_under_40"]["gain"], 0)); put("TThreeUnderN", pc(t3["share_under_40"]["nogain"], 0))
ww = t3["welch"]
put("TThreeWD", f(ww["diff"], 2)); put("TThreeWLo", f(ww["ci_lo"], 2)); put("TThreeWHi", f(ww["ci_hi"], 2))
put("TThreeWT", f(ww["t"], 2)); put("TThreeWDf", i(ww["df"])); put("TThreeWP", pv(ww["p"]))
put("TThreeBMs", f(abs(t3["brunner_munzel"]["stat"]), 2)); put("TThreeBMp", pv(t3["brunner_munzel"]["p"]))
put("TFourN", i(t4["n"])); put("TFourUnk", i(T["t4_rows_unknown_dropped"])); put("TFourNoPay", i(T["t4_n_nopay"]))
put("TFourChi", f(t4["chi2"], 1)); put("TFourDf", i(t4["df"])); put("TFourP", pv(t4["p"])); put("TFourHolm", pv(t4["p_holm"]))
put("TFourV", f(t4["V"], 3)); put("TFourLo", f(t4["ci_lo"], 3)); put("TFourHi", f(t4["ci_hi"], 3))
put("TFourG", f(t4["g"]["stat"], 1)); put("TFourGp", pv(t4["g"]["p"]))
put("TFourMC", lt(t4["montecarlo"]["p"], t4["montecarlo"]["B"]))
put("TFourMinE", f(t4["cochran"]["min_expected"], 2)); put("TFourBelow", i(t4["cochran"]["cells_below5"])); put("TFourCells", i(t4["cochran"]["cells"]))
put("TFourSEI", pc(t4["rates"]["Self-emp-inc"])); put("TFourPriv", pc(t4["rates"]["Private"])); put("TFourFed", pc(t4["rates"]["Federal-gov"]))
for k, nm in [("t1", "TOne"), ("t2", "TTwo"), ("t3", "TThree"), ("t4", "TFour")]:
    put(nm + "Verdict", T[k]["verdict"])
put("TThreeWVerdict", t3["welch_verdict"])

(ROOT / "report" / "numbers.tex").write_text("% generated by src/04_macros.py. Do not edit.\n" + "\n".join(lines) + "\n")
print(len(lines), "macros written")
