
"""網站讀資料的地方。只讀 data/clean 的 CSV，不在使用者開頁時爬網站。"""
from pathlib import Path

import pandas as pd
import streamlit as st

CLEAN = Path(__file__).resolve().parent.parent / "data" / "clean"

def load_raw():
    """不經過 Streamlit 快取的版本，給 scripts/ 裡的程式用。"""
    return load.__wrapped__()
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
import json

def load_locked():
    """Day 18 鎖定的台灣大賽預測；還沒鎖定就回傳 None。"""
    path=CLEAN/'prediction_locked.json'
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

@st.cache_data
def load_half():
    """中職官網的上下半季戰績（Day 25）；沒有檔案就回傳 None。"""
    path = CLEAN / "half_standings.csv"
    return pd.read_csv(path) if path.exists() else None
@st.cache_data
def load_rule_stability():
    """每條弱點規則在重抽中成立的比例（Day 30）；還沒跑就回傳 None。"""
    path = CLEAN / "rule_stability.csv"
    return pd.read_csv(path) if path.exists() else None
@st.cache_data
def load_stability():
    """上線後實驗的摘要（Day 31）；還沒跑實驗就回傳 None。"""
    path = CLEAN / "stability_summary.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
