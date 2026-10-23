"""一鍵更新：抓資料 → 清理 → 拆分數據。用法：python scripts/update_data.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pandas as pd

from src import clean, fetch, splits

clean.main()
const = pd.read_csv(ROOT / "data/clean/league_constants.csv", index_col=0).iloc[:, 0]

pitchers = pd.read_csv(ROOT / "data/clean/pitchers.csv")
frames = [fetch.fetch_pitcher_pa(pid) for pid in pitchers["player_id"]]
pa = pd.concat(frames, ignore_index=True)
pa.to_csv(ROOT / "data/clean/pa.csv", index=False)

b_split, p_split, lg = splits.build_splits(pa, const["woba_scale"])
b_split.to_csv(ROOT / "data/clean/batter_splits.csv", index=False)
p_split.to_csv(ROOT / "data/clean/pitcher_splits.csv", index=False)
print(f"逐打席 {len(pa)} 筆；聯盟 wOBA {lg['wOBA']:.3f}")
