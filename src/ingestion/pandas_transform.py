from pathlib import Path
import pandas as pd


def compute_daily_currency_stats(csv_path: Path | str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    missing = {"currency_code", "rate"} - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    return (
        df.groupby("currency_code")["rate"]
        .agg(["mean", "min", "max"])
        .round(4)
        .reset_index()
        .rename(columns={"mean": "avg_rate", "min": "min_rate", "max": "max_rate"})
    )
