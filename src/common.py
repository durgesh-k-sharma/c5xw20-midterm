"""Shared constants. Seed and paths are fixed here so every script agrees."""
from pathlib import Path

SEED = 558
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "adult.data"
OUT = ROOT / "outputs"
FIG = OUT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

COLS = ["age", "workclass", "fnlwgt", "education", "education-num", "marital-status",
        "occupation", "relationship", "race", "sex", "capital-gain", "capital-loss",
        "hours-per-week", "native-country", "income"]
CAT = ["workclass", "education", "marital-status", "occupation", "relationship",
       "race", "sex", "native-country"]
NUM = ["age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week"]

EDU_BAND = {
    **{k: "1 Below HS" for k in ["Preschool", "1st-4th", "5th-6th", "7th-8th", "9th",
                                 "10th", "11th", "12th"]},
    "HS-grad": "2 HS grad",
    **{k: "3 Some college" for k in ["Some-college", "Assoc-acdm", "Assoc-voc"]},
    **{k: "4 Bachelors+" for k in ["Bachelors", "Masters", "Prof-school", "Doctorate"]},
}
