# Day 30｜11/10（二）｜上線後實驗③：資料重抽（Bootstrap）

> 預計時間：2 小時　｜　階段：上線後實驗

## Jupyter 版做法

- 筆記本：`notebooks/D30.ipynb`，第一格放每日開場程式碼（見 [README](README.md#用-jupyter-做的方式)）。
- 加到檔案最後面（`%%writefile -a`）：`src/stability.py`、`src/rules.py`、`src/data.py`
- 要打開檔案修改中間：`pages/predict.py`
- **一定要在終端機執行**：
  - 第 5 步「確認」的 `streamlit run app.py`：網站會一直執行，用 `!` 跑會讓 notebook 卡住
- 結束時在格子執行 `!git add .` 和 `!git commit -m "Day 30: 實驗 3 Bootstrap"`。

## 今天的目標

- 學會 Bootstrap：從手上的資料「有放回地重抽」，模擬「如果球季重打一次」
- 算出奪冠機率的 95% 區間
- 檢查每一條弱點規則在重抽中有幾成會成立
- 讓預測頁只顯示穩定的弱點

## 為什麼要做這一步

2026 年只有一個球季。如果同樣兩支球隊再打一次例行賽，得失分一定會有點不同，畢氏勝率和奪冠機率也會跟著變。Bootstrap 的做法是：從 360 場比賽中**有放回地**抽 360 場（同一場可能被抽到兩次，有些場不會被抽到），當作「另一個平行時空的球季」。重複 200 次，就能看出奪冠機率在不同球季之間會跳多少。

---

## 步驟

### 1. 奪冠機率的區間

在 `src/stability.py` 加入：

> **Jupyter**：新的一格，第一行寫 `%%writefile -a src/stability.py`（`-a` 是加到檔案最後面，不會覆蓋），第二行留空，再貼這段。

```python
# ---------- 實驗 3：資料重抽（Bootstrap） ----------
def exp_bootstrap_series(teams, games, n_boot=200, seed=0):
    """從例行賽 360 場比賽中「有放回地」重抽，重算得失分 → 畢氏勝率 → 奪冠機率。"""
    rng = np.random.default_rng(seed)
    a, b = config.TS_TEAMS
    out = []
    for _ in range(n_boot):
        g = games.iloc[rng.integers(0, len(games), len(games))]
        rs_ra = {}
        for team in (a, b):
            home, away = g[g["home"] == team], g[g["away"] == team]
            rs_ra[team] = (home["home_runs"].sum() + away["away_runs"].sum(),
                           home["away_runs"].sum() + away["home_runs"].sum())
        pa, pb = pythag(*rs_ra[a]), pythag(*rs_ra[b])
        out.append(model.simulate_series(pa, pb, config.TS_HOME_PATTERN, config.TS_NEED,
                                         config.HOME_ADVANTAGE, n=2_000, seed=1)[0])
    return pd.Series(out, name="奪冠機率")
```

- `rng.integers(0, len(games), len(games))`：抽 360 個 0–359 的隨機數字（可以重複），用它們挑出比賽。
- 每次重抽只模擬 2,000 次，因為要做 200 次，總共 40 萬次模擬；實驗 1 已經證明模擬次數不是主要的誤差來源。

> **Jupyter**：把雙引號裡面的程式碼貼在新的一格執行就好，不用 `python -c`。

```bash
python -c "
import pandas as pd
from src import fetch, stability as st
b = st.exp_bootstrap_series(pd.read_csv('data/clean/teams.csv'), fetch.fetch_games())
print(b.quantile([0.025, 0.5, 0.975]).round(3))
"
```

結果大約是：**95% 區間 35%–90%**，寬度 55 個百分點，遠超過企劃書的 10 個百分點，**沒有通過**。

怎麼解讀？這不是程式寫錯，而是**一個球季的得失分本來就有很大的隨機性**。味全龍和中信兄弟的實力差距，在「不同的平行球季」裡可能大、可能小。所以網站上只寫「68%」會讓人以為很確定，應該加上區間（明天做）。

### 2. 弱點規則的可靠度

預測頁說「鋼龍對右打明顯較弱」，這是根據他整季面對的幾百個打席。如果換一批類似的打席，這個結論還成立嗎？

> **Jupyter**：新的一格，第一行寫 `%%writefile -a src/stability.py`（`-a` 是加到檔案最後面，不會覆蓋），第二行留空，再貼這段。

```python
def exp_bootstrap_rules(pa, scale, sp, lineup, lg, n_boot=200, seed=0):
    """重抽逐打席資料，重算這位先發的拆分數據，統計每條弱點規則有幾成的機率成立。"""
    rng = np.random.default_rng(seed)
    base = splits.prepare(pa, scale)
    mine = base[base["pitcher_id"] == sp["player_id"]]
    counts = {}
    for _ in range(n_boot):
        s = mine.iloc[rng.integers(0, len(mine), len(mine))]
        p = sp.copy()
        for hand in ("L", "R"):
            sub = s[s["b_hand"] == hand]
            p[f"PA_vs{hand}"], p[f"wOBA_vs{hand}"] = len(sub), sub["woba_val"].mean()
        p["wOBA_round3"] = s.loc[s["pa_round"] == 3, "woba_val"].mean()
        for sentence in rules.pitcher_weak(p, lineup, lg):
            key = sentence.split("：")[0]          # 用冒號前的標題當作規則名稱
            counts[key] = counts.get(key, 0) + 1
    return pd.Series(counts).div(n_boot).sort_values(ascending=False).rename("成立比例")
```

- 只重抽**這位先發**面對過的打席，重算他對左右打、第三輪的被 wOBA。
- 每次都用 Day 13 的 `pitcher_weak` 產生弱點句子，記下每條規則出現幾次。
- 句子冒號前面的文字（例如「對右打明顯較弱」）當作規則名稱。

測試兩隊王牌：

> **Jupyter**：把雙引號裡面的程式碼貼在新的一格執行就好，不用 `python -c`。

```bash
python -c "
import pandas as pd
from src import stability as st
from src.data import load
teams, batters, pitchers, const, lg = load()
pa = pd.read_csv('data/clean/pa.csv', dtype=str, keep_default_na=False)
for abbr, opp in [('象', '龍'), ('龍', '象')]:
    sp = pitchers[(pitchers['abbr'] == abbr) & (pitchers['role'] == '先發')].nlargest(1, 'IP').iloc[0]
    lineup = batters[batters['abbr'] == opp].nlargest(9, 'PA')
    print(sp['name'], st.exp_bootstrap_rules(pa, const['woba_scale'], sp, lineup, lg).round(2).to_dict())
"
```

以鋼龍為例：「對右打明顯較弱」只在約 46% 的重抽中成立。企劃書的標準是 80%，所以這條結論**不夠穩定，不應該顯示**。

### 3. 每位先發都算一次，存起來

> **Jupyter**：新的一格，第一行寫 `%%writefile -a src/stability.py`（`-a` 是加到檔案最後面，不會覆蓋），第二行留空，再貼這段。

```python
def rule_stability_table(pa, scale, teams, batters, pitchers, lg, n_boot=200):
    """台灣大賽兩隊每位先發的每條弱點規則，在重抽中成立的比例。存起來給預測頁過濾用。"""
    t = teams.set_index("team")
    a, b = config.TS_TEAMS
    rows = []
    for team, opp in ((a, b), (b, a)):
        abbr, opp_abbr = t.loc[team, "abbr"], t.loc[opp, "abbr"]
        lineup = batters[batters["abbr"] == opp_abbr].nlargest(9, "PA")
        for _, sp in pitchers[(pitchers["abbr"] == abbr) & (pitchers["role"] == "先發")].iterrows():
            ratio = exp_bootstrap_rules(pa, scale, sp, lineup, lg, n_boot)
            rows += [{"pitcher_id": sp["player_id"], "rule": k, "ratio": v} for k, v in ratio.items()]
    return pd.DataFrame(rows)
```

這張表明天會由 `run_experiments.py` 自動產生並存成 `data/clean/rule_stability.csv`。今天先手動跑一次：

> **Jupyter**：把雙引號裡面的程式碼貼在新的一格執行就好，不用 `python -c`。

```bash
python -c "
import pandas as pd
from src import stability as st
from src.data import load
teams, batters, pitchers, const, lg = load()
pa = pd.read_csv('data/clean/pa.csv', dtype=str, keep_default_na=False)
st.rule_stability_table(pa, const['woba_scale'], teams, batters, pitchers, lg).to_csv('data/clean/rule_stability.csv', index=False)
"
```

### 4. 練習：預測頁只顯示穩定的弱點

做法：在產生弱點和策略之前，先把「不穩定的弱點」用到的拆分數據**清空**。這樣不只投手弱點，應對策略也不會用到不穩定的結論（不然會出現「投手弱點」沒寫，「應對策略」卻說「鋼龍怕右打」的矛盾）。

1. 在 `src/rules.py` 最後面寫 `stable_pitcher(sp, opp_lineup, lg, stab, threshold=0.8)`：找出這位投手目前觸發、但成立比例低於 80% 的規則，把相關欄位設成 `NaN`，回傳（清理後的投手, 隱藏了幾項）。
2. 在 `src/data.py` 加 `load_rule_stability()` 讀 CSV（沒有檔案回傳 `None`）。
3. 預測頁的弱點分析改用清理後的投手，並在投手弱點下面註明「另有 N 項在重抽測試中不夠穩定，沒有列出」。

<details>
<summary>參考解答</summary>

`src/rules.py`：

> **Jupyter**：新的一格，第一行寫 `%%writefile -a src/rules.py`（`-a` 是加到檔案最後面，不會覆蓋），第二行留空，再貼這段。

```python
# 規則名稱 → 這條規則用到的拆分數據欄位
RULE_COLUMNS = {"對左打明顯較弱": ["wOBA_vsL", "wOBA_vsR"], "對右打明顯較弱": ["wOBA_vsL", "wOBA_vsR"],
                "第三輪打線開始被看穿": ["wOBA_round3"]}

def stable_pitcher(sp, opp_lineup, lg, stab, threshold=0.8):
    """
    Day 30：把「在 Bootstrap 重抽中成立不到 threshold」的弱點所用到的拆分數據清空，
    之後的弱點分析和應對策略就都不會用到不穩定的結論。回傳（清理後的投手, 被隱藏幾項）。
    """
    if stab is None:
        return sp, 0
    ratio = stab[stab["pitcher_id"] == sp["player_id"]].set_index("rule")["ratio"]
    sp = sp.copy()
    hidden = 0
    for sentence in pitcher_weak(sp, opp_lineup, lg):
        rule = sentence.split("：")[0]
        if rule in RULE_COLUMNS and ratio.get(rule, 1.0) < threshold:
            for col in RULE_COLUMNS[rule]:
                sp[col] = float("nan")
            hidden += 1
    return sp, hidden
```

`src/data.py`：

> **Jupyter**：新的一格，第一行寫 `%%writefile -a src/data.py`（`-a` 是加到檔案最後面，不會覆蓋），第二行留空，再貼這段。

```python
@st.cache_data
def load_rule_stability():
    """每條弱點規則在重抽中成立的比例（Day 30）；還沒跑就回傳 None。"""
    path = CLEAN / "rule_stability.csv"
    return pd.read_csv(path) if path.exists() else None
```

`pages/predict.py` 的弱點分析整段換成（記得在 import 加上 `load_rule_stability`）：

> **Jupyter**：這段要插進 `pages/predict.py` 的中間，不能用 `%%writefile`。在 JupyterLab 左側檔案列表雙擊打開 `pages/predict.py`，貼到指定位置，按 `Cmd + S` 存檔。（把原本「弱點分析與應對策略」整段換掉，最上面的 import 也要加上 `load_rule_stability`）

```python
st.header("弱點分析與應對策略")
stab = load_rule_stability()
sa, hid_a = rules.stable_pitcher(sp_a, lu_b, lg, stab)   # 不穩定的拆分數據先清掉
sb, hid_b = rules.stable_pitcher(sp_b, lu_a, lg, stab)
note = lambda n: [f"<span style='color:#8C9BB0'>另有 {n} 項在重抽測試中不夠穩定，沒有列出。</span>"] if n else []
for title, fa, fb in [
    ("投手弱點", lambda: rules.pitcher_weak(sa, lu_b, lg) + note(hid_a),
                 lambda: rules.pitcher_weak(sb, lu_a, lg) + note(hid_b)),
    ("打線弱點", lambda: rules.lineup_weak(lu_a, sp_b), lambda: rules.lineup_weak(lu_b, sp_a)),
    ("應對策略", lambda: rules.strategy(lu_a, bench_a, sa, sb, lg),
                 lambda: rules.strategy(lu_b, bench_b, sb, sa, lg)),
]:
    st.subheader(title)
    c1, c2 = st.columns(2)
    with c1:
        ui.bullet_card(A_NAME, fa(), A["color"])
    with c2:
        ui.bullet_card(B_NAME, fb(), B["color"])
```

注意：單場勝率的計算（Day 16）還是用原本的 `sp_a`、`sp_b`，只有文字分析改用清理後的版本。

</details>

### 5. 確認

> **一定要在終端機執行**：網站會一直執行，用 `!` 跑會讓 notebook 卡住。在 JupyterLab 用 **File → New → Terminal** 開一個終端機執行。

```bash
streamlit run app.py
```

預測頁選鋼龍當先發：「投手弱點」應該不再寫「對右打明顯較弱」，而是出現「另有 1 項在重抽測試中不夠穩定」；中信兄弟的應對策略也不會再說「鋼龍怕右打」。

把今天的結果記到 `my_notes.md`：實驗 3 **沒通過**（區間寬度 55 個百分點）；全部規則中只有約三成在 80% 以上的重抽中成立。

---

## 完成檢查

- [ ] 算出奪冠機率的 95% 區間
- [ ] `data/clean/rule_stability.csv` 產生了
- [ ] 預測頁不再顯示不穩定的弱點，策略也跟著一致
- [ ] `git commit -m "Day 30: 實驗 3 Bootstrap"`

## 明天預告

最後兩組實驗：換資料截止日，以及跟真實比賽結果比較；再把五組實驗包成一支程式，並在網站上顯示奪冠機率的區間。
