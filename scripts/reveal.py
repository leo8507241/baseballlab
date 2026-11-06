"""揭曉：抓台灣大賽實際比分，跟鎖定的預測對照，結果存成 data/clean/reveal.json。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pandas as pd

from src import config, fetch

YEAR = 2026   # 測試
locked = json.loads((ROOT / "data/clean/prediction_locked.json").read_text(encoding="utf-8"))
A, B = locked["teams"]

season_id = fetch.find_season_id(YEAR, config.POSTSEASON_TITLE)
games = fetch.fetch_games(season_id, refresh=True).sort_values("date").reset_index(drop=True)
games.to_csv(ROOT / "data/clean/postseason.csv", index=False)

rows = []
for i, g in games.iterrows():
    a_home = g["home"] == A                               # 依實際主客場，挑鎖定時算好的勝率
    p_a = locked["game_prob_A_home"] if a_home else locked["game_prob_A_away"]
    winner = g["home"] if g["winner_side"] == "HOME" else g["away"]
    rows.append({"場次": f"G{i + 1}", "日期": g["date"], "主場": g["home"],
                 "比分": f"{g['away']} {g['away_runs']} : {g['home_runs']} {g['home']}",
                 f"{A} 勝率": p_a, "模型看好": A if p_a >= 0.5 else B, "實際勝方": winner,
                 "A 贏": winner == A, "主場贏": g["winner_side"] == "HOME"})
table = pd.DataFrame(rows)
table["猜對"] = table["模型看好"] == table["實際勝方"]

wins_a = int(table["A 贏"].sum())
wins_b = len(table) - wins_a
actual = f"{wins_a}-{wins_b}"
champion = A if wins_a > wins_b else B
reveal = {
    "season_id": season_id,
    "actual_score": actual,
    "actual_champion": champion,
    "predicted_champion": max(locked["champion_prob"], key=locked["champion_prob"].get),
    "prob_of_actual_score": locked["result_dist"].get(actual, 0),
    "games": len(table),
    "hit_rate": float(table["猜對"].mean()),
    "home_wins_rate": float(table["主場贏"].mean()),        # 簡單方法：主場球隊必勝
    "brier": float(((table[f"{A} 勝率"] - table["A 贏"]) ** 2).mean()),
}
(ROOT / "data/clean/reveal.json").write_text(json.dumps(reveal, ensure_ascii=False, indent=2), encoding="utf-8")
table.to_csv(ROOT / "data/clean/reveal_games.csv", index=False)
print(table[["場次", "比分", "模型看好", "實際勝方", "猜對"]].to_string(index=False))
print(json.dumps(reveal, ensure_ascii=False, indent=2))
