"""上線後實驗：一次跑完實驗 1–4，印出報告並存成 data/clean/stability_summary.json。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pandas as pd

from src import config, fetch, stability as st
from src.data import load_raw

teams, batters, pitchers, const, lg = load_raw()
games = fetch.fetch_games()
pa = pd.read_csv(ROOT / "data/clean/pa.csv", dtype=str, keep_default_na=False)
a, b = config.TS_TEAMS
result = {}

# 實驗 1
s = st.exp_seeds(teams)
result["exp1"] = {"平均": s.mean(), "標準差": s.std(), "通過": bool(s.std() < 0.01)}

# 實驗 2
sens = st.exp_sensitivity(teams)
innings = {i: st.default_game_prob(teams, batters, pitchers, lg, sp_innings=i) for i in (5, 6, 7)}
spread = max(sens.groupby("參數")["奪冠機率"].agg(lambda x: x.max() - x.min()).max(),
             max(innings.values()) - min(innings.values()))
result["exp2"] = {"最大變動": spread, "先發局數": innings,
                  "看好的球隊不變": bool((sens["奪冠機率"] > 0.5).all() or (sens["奪冠機率"] < 0.5).all()),
                  "通過": bool(max(innings.values()) - min(innings.values()) <= 0.05)}

# 實驗 3
boot = st.exp_bootstrap_series(teams, games)
lo, hi = boot.quantile([0.025, 0.975])
result["exp3"] = {"奪冠機率95%區間": [lo, hi], "區間寬度": hi - lo, "通過": bool(hi - lo <= 0.10)}
stab = st.rule_stability_table(pa, const["woba_scale"], teams, batters, pitchers, lg)
stab.to_csv(ROOT / "data/clean/rule_stability.csv", index=False)
result["exp3"]["規則穩定比例"] = float((stab["ratio"] >= 0.8).mean())

# 實驗 4
cut = st.exp_cutoff(games)
drift = cut["奪冠機率"].max() - cut["奪冠機率"].min()
result["exp4"] = {"各截止日": cut["奪冠機率"].round(3).tolist(), "最大差距": drift, "通過": bool(drift <= 0.10)}

out = ROOT / "data/clean/stability_summary.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
for k, v in result.items():
    print(k, json.dumps(v, ensure_ascii=False, default=lambda x: round(float(x), 3)))
