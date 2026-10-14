# Day 7｜10/17（六）｜進階數據②：wOBA、FIP 與資料清理

> 預計時間：2 小時　｜　階段：資料基礎

## 今天的目標

- 算出 wOBA，並學會用「倍數」讓它跟上壘率同一個尺度
- 算出 FIP，並學會用「常數」讓它跟防禦率同一個尺度
- 寫 `src/clean.py`：一個指令把所有表格整理好，存到 `data/clean/`

## 為什麼要做這一步

wOBA 是打者最重要的單一數據，FIP 是投手最重要的單一數據，預測模型的核心就是這兩個。`clean.py` 則是網站和模型的資料入口：網站之後只讀 `data/clean/` 的 CSV，不再碰原始 JSON。

---

## 步驟

### 1. wOBA 和它的倍數

wOBA 先依每種打擊結果的價值加權：

```text
原始 wOBA = (0.69×非故意四壞 + 0.72×觸身 + 0.89×一安 + 1.27×二安 + 1.62×三安 + 2.10×全壘打)
          ÷ (打數 + 四壞 − 故意四壞 + 犧飛 + 觸身)
```

但這樣算出來的數字整體會偏低。慣例是再乘上一個**倍數**，讓「全聯盟的 wOBA」等於「全聯盟的上壘率」，這樣讀者可以用熟悉的上壘率標準來理解（.320 是平均、.400 很強）。

在 `src/metrics.py` 最上面加入權重，並新增兩個函式：

```python
# wOBA 權重：大聯盟常用的近似值。中職沒有官方公布，所以算出來會跟野球革命略有差異。
WOBA_WEIGHTS = {"uBB": 0.69, "HBP": 0.72, "1B": 0.89, "2B": 1.27, "3B": 1.62, "HR": 2.10}

def woba(uBB, HBP, single, double, triple, HR, AB, BB, IBB, SF, scale=1.0):
    w = WOBA_WEIGHTS
    num = (w["uBB"] * uBB + w["HBP"] * HBP + w["1B"] * single
           + w["2B"] * double + w["3B"] * triple + w["HR"] * HR)
    den = AB + BB - IBB + SF + HBP
    return num / den * scale

def woba_scale(lg):
    """讓「聯盟 wOBA」等於「聯盟上壘率」的倍數。lg 是全聯盟加總後的一列資料。"""
    obp = (lg["H"] + lg["BB"] + lg["HBP"]) / (lg["AB"] + lg["BB"] + lg["HBP"] + lg["SF"])
    raw = woba(lg["uBB"], lg["HBP"], lg["1B"], lg["2B"], lg["3B"], lg["HR"],
               lg["AB"], lg["BB"], lg["IBB"], lg["SF"])
    return obp / raw
```

### 2. FIP 和它的常數

FIP 只看三振、保送、全壘打（投手自己能控制的事）：

```text
FIP = (13×全壘打 + 3×保送 − 2×三振) ÷ 局數 + 常數
```

常數的作用跟 wOBA 的倍數一樣：讓「全聯盟的 FIP」等於「全聯盟的防禦率」。加到 `src/metrics.py`：

```python
def fip_constant(lg_er, lg_ip, lg_hr, lg_bb, lg_so):
    """讓「聯盟 FIP 平均」等於「聯盟 ERA 平均」的常數。"""
    lg_era = lg_er * 9 / lg_ip
    return lg_era - (13 * lg_hr + 3 * lg_bb - 2 * lg_so) / lg_ip

def fip(HR, BB, SO, IP, const):
    # 野球革命的投手資料沒有觸身球，所以這裡的 FIP 只用保送。
    return (13 * HR + 3 * BB - 2 * SO) / IP + const
```

### 3. 建立 `src/clean.py`

```python
"""把 data/raw 的原始資料整理成網站要用的乾淨表格，存到 data/clean。"""
from pathlib import Path

import pandas as pd

from src import cpbl, fetch, metrics

CLEAN_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"

def build_teams():
    teams = fetch.fetch_teams()
    standings = fetch.fetch_standings()
    games = fetch.fetch_games()

    # 每隊得分、失分：主場和客場分開算再加起來
    home = games.groupby("home").agg(RS=("home_runs", "sum"), RA=("away_runs", "sum"))
    away = games.groupby("away").agg(RS=("away_runs", "sum"), RA=("home_runs", "sum"))
    runs = home.add(away, fill_value=0).rename_axis("team").reset_index()

    df = standings.merge(teams[["team", "team_id", "color"]], on="team").merge(runs, on="team")
    df["G"] = df["W"] + df["L"] + df["T"]
    df["pythag"] = metrics.pythag(df["RS"], df["RA"])
    df["luck"] = df["PCT"] - df["pythag"]       # 正數＝贏得比實力多
    return df.sort_values("rank")

def build_batters(teams):
    b = fetch.fetch_leaders("batter").rename(columns={"Double": "2B", "Triple": "3B"})
    b["1B"] = b["H"] - b["2B"] - b["3B"] - b["HR"]
    b["uBB"] = b["BB"] - b["IBB"]
    scale = metrics.woba_scale(b.sum(numeric_only=True))
    b["wOBA_calc"] = metrics.woba(b["uBB"], b["HBP"], b["1B"], b["2B"], b["3B"], b["HR"],
                                  b["AB"], b["BB"], b["IBB"], b["SF"], scale)
    b["ISO_calc"] = metrics.iso(b["2B"], b["3B"], b["HR"], b["AB"])
    b["BABIP_calc"] = metrics.babip(b["H"], b["HR"], b["AB"], b["SO"], b["SF"])
    b = b.merge(teams[["abbr", "team"]], on="abbr", how="left")
    return b, scale

def build_pitchers(teams):
    p = fetch.fetch_leaders("pitcher").rename(columns={"Double": "2B", "Triple": "3B"})
    p["IP"] = p["IPOut"] / 3
    p["role"] = (p["SP"] >= p["games"] / 2).map({True: "先發", False: "後援"})
    const = metrics.fip_constant(p["ER"].sum(), p["IP"].sum(), p["HR"].sum(),
                                 p["BB"].sum(), p["SO"].sum())
    p["FIP_calc"] = metrics.fip(p["HR"], p["BB"], p["SO"], p["IP"], const)
    p = p.merge(teams[["abbr", "team"]], on="abbr", how="left")
    return p, const

def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    teams = build_teams()
    batters, scale = build_batters(teams)
    pitchers, const = build_pitchers(teams)
    teams.to_csv(CLEAN_DIR / "teams.csv", index=False)
    batters.to_csv(CLEAN_DIR / "batters.csv", index=False)
    pitchers.to_csv(CLEAN_DIR / "pitchers.csv", index=False)
    pd.Series({"woba_scale": scale, "fip_const": const}).to_csv(CLEAN_DIR / "league_constants.csv")

    # 中職官網的上下半季戰績（抓不到就用野球革命自己算），並跟全年戰績交叉比對
    half, source = cpbl.half_standings(refresh=True)
    half.assign(source=source).to_csv(CLEAN_DIR / "half_standings.csv", index=False)
    bad = cpbl.cross_check(half, teams)
    print(f"半季戰績來源：{source}；交叉比對" + ("全部一致" if bad.empty else f"對不上：{list(bad.index)}"))
    print(f"球隊 {len(teams)}、打者 {len(batters)}、投手 {len(pitchers)}；"
          f"wOBA 倍數 = {scale:.3f}、FIP 常數 = {const:.2f}")

if __name__ == "__main__":
    main()
```

幾個細節：

- `b.sum(numeric_only=True)`：把全聯盟打者的數字欄位加總成一列，就是「聯盟總和」，丟給 `woba_scale`。
- `role`：先發場次超過出賽數一半的投手算先發，其他算後援。預測模型要分開算先發和牛棚。
- `league_constants.csv`：把倍數和常數存起來，之後數據學院的計算機要用。
- 最後一段把 Day 5 的半季戰績也存成 `half_standings.csv`，並記下資料來源。每次整理資料都會順便交叉比對一次，兩個來源對不上時馬上就會知道。
- `if __name__ == "__main__":`：直接執行這個檔案時才會跑 `main()`；被別的程式 import 時不會自動跑。

### 4. 執行與驗證

```bash
python -m src.clean
```

> 為什麼用 `python -m src.clean` 而不是 `python src/clean.py`？`-m` 會把專案根目錄當成起點，`from src import fetch` 才找得到。

應該印出：

```text
半季戰績來源：中職官網；交叉比對全部一致
球隊 6、打者 183、投手 181；wOBA 倍數 = 1.085、FIP 常數 = 3.02
```

### 5. 練習：比對野球革命

讀 `data/clean/batters.csv` 和 `pitchers.csv`，計算（打席 200 以上、投球 40 局以上）：

1. 你的 `wOBA_calc` 和野球革命的 `wOBA` 平均差多少？
2. 你的 `FIP_calc` 和野球革命的 `FIP` 平均差多少？

<details>
<summary>參考解答</summary>

```python
import pandas as pd
b = pd.read_csv("data/clean/batters.csv"); q = b[b["PA"] >= 200]
print("wOBA 平均絕對差：", (q["wOBA_calc"] - q["wOBA"]).abs().mean())   # 約 0.003
p = pd.read_csv("data/clean/pitchers.csv"); qp = p[p["IP"] >= 40]
print("FIP 平均差：", (qp["FIP_calc"] - qp["FIP"]).mean())               # 約 0.07
```

差異很小，來自權重和觸身球的差別。如果沒有乘倍數，wOBA 會整體低 0.023，可以把 `scale` 拿掉試試看。

</details>

---

## 完成檢查

- [ ] `data/clean/` 裡有 `teams.csv`、`batters.csv`、`pitchers.csv`、`league_constants.csv`、`half_standings.csv`
- [ ] wOBA 和野球革命平均只差 0.003 左右
- [ ] 能用一句話解釋「倍數」和「常數」在做什麼
- [ ] `git commit -m "Day 7: wOBA、FIP 與資料清理"`

## 明天預告

明天抓「每一個打席」的紀錄（約 2.8 萬筆），這是弱點分析的原料，第一次執行要跑 6 到 10 分鐘。
