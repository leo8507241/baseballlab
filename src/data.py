
"""網站讀資料的地方。只讀 data/clean 的 CSV，不在使用者開頁時爬網站。"""
from pathlib import Path

import pandas as pd
import streamlit as st

CLEAN = Path(__file__).resolve().parent.parent / "data" / "clean"

@st.cache_data
def load():
    teams = pd.read_csv(CLEAN / "teams.csv")
    batters = pd.read_csv(CLEAN / "batters.csv").merge(
        pd.read_csv(CLEAN / "batter_splits.csv"), left_on="player_id", right_on="batter_id", how="left")
    pitchers = pd.read_csv(CLEAN / "pitchers.csv").merge(
        pd.read_csv(CLEAN / "pitcher_splits.csv"), left_on="player_id", right_on="pitcher_id", how="left")
    batters["bats"] = batters["bats"].fillna("R")
    const = pd.read_csv(CLEAN / "league_constants.csv", index_col=0).iloc[:, 0]
    q = pitchers[pitchers["IP"] >= 30]
    lg = {"wOBA": (batters["wOBA_calc"] * batters["PA"]).sum() / batters["PA"].sum(),
          "BBp_p75": q["BBp"].quantile(0.75), "HR9_p75": q["HR9"].quantile(0.75)}
    return teams, batters, pitchers, const, lg

@st.cache_data
def load_pa():
    return pd.read_csv(CLEAN / "pa.csv", dtype={"result": str}, keep_default_na=False)
