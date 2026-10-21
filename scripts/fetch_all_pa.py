import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
from src import fetch

pitchers=fetch.fetch_player('pitcher',refresh=False)
frames=[]
for i , pid in enumerate(pitchers['player_id'],1):
    frames.append(fetch.fetch_pitcher_pa(pid))
    if i % 20 == 0:
        print(f'{i}/{len(pitchers)}')

df_all_pitcher=pd.concat(frames,ignore_index=True)
out=Path(__file__).resolve().parent.parent/ "data" / "clean" / "pa.csv"
out.parent.mkdir(parents=True, exist_ok=True)
df_all_pitcher.to_csv(out,index=False)
print(f'完成：{len(df_all_pitcher)} 個打席 → {out}')
