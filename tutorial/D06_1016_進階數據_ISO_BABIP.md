# Day 6｜10/16（五）｜進階數據①：ISO、BABIP、畢氏勝率

> 預計時間：2 小時　｜　階段：資料基礎

## 今天的目標

- 建立 `src/metrics.py`，把進階數據公式寫成函式
- 算出 ISO、BABIP、畢氏勝率
- 跟野球革命的數字比對，驗證公式正確

## 為什麼要做這一步

野球革命已經算好 ISO、BABIP 了，為什麼還要自己算？

1. **數據學院的計算機**要讓使用者輸入數字自己算，必須有公式。
2. **預測模型**要用到畢氏勝率，野球革命沒有提供。
3. 自己算一次，才真的懂這個數據在量什麼。期末被問到時講得出來。

---

## 步驟

### 1. 三個公式

| 數據 | 公式 | 意思 |
| --- | --- | --- |
| ISO | (二安 + 2×三安 + 3×全壘打) ÷ 打數 | 長打率減掉打擊率，只看長打能力 |
| BABIP | (安打 − 全壘打) ÷ (打數 − 三振 − 全壘打 + 犧飛) | 打進場內的球變成安打的比例，常用來判斷運氣 |
| 畢氏勝率 | 得分^1.83 ÷ (得分^1.83 + 失分^1.83) | 用得失分估算「應該」有的勝率 |

### 2. 建立 `src/metrics.py`

```python
"""進階數據公式。每個函式都可以吃單一數字，也可以吃 pandas 的整欄。"""

def iso(double, triple, HR, AB):
    return (double + 2 * triple + 3 * HR) / AB

def babip(H, HR, AB, SO, SF):
    return (H - HR) / (AB - SO - HR + SF)

def pythag(rs, ra, exp=1.83):
    """畢氏勝率：用得分、失分估算球隊應有的勝率。"""
    return rs ** exp / (rs ** exp + ra ** exp)
```

**為什麼可以吃整欄？** pandas 的欄位做加減乘除時，會自動對每一列分別計算（這叫向量化）。所以 `iso(df["Double"], df["Triple"], df["HR"], df["AB"])` 會一次回傳每位打者的 ISO，不用寫迴圈。

### 3. 驗證 ISO 和 BABIP

新增 `explore_metrics.py`：

```python
from src import fetch, metrics

b = fetch.fetch_leaders("batter")
b["ISO_calc"] = metrics.iso(b["Double"], b["Triple"], b["HR"], b["AB"])
b["BABIP_calc"] = metrics.babip(b["H"], b["HR"], b["AB"], b["SO"], b["SF"])

q = b[b["PA"] >= 200]
print("ISO 最大差異：", (q["ISO_calc"] - q["ISO"]).abs().max())
print("BABIP 最大差異：", (q["BABIP_calc"] - q["BABIP"]).abs().max())
```

兩個差異都應該小於 0.001（只是四捨五入造成的）。

> 為什麼只看 `PA >= 200`？打席太少的球員，分母可能是 0，會算出無限大或 `NaN`。

### 4. 練習：畢氏勝率

用昨天的得失分，算出每隊的畢氏勝率，再跟實際勝率 `PCT` 比較。

1. 哪一隊「實際勝率 − 畢氏勝率」最大（贏得比實力多）？
2. 哪一隊最小（贏得比實力少）？

<details>
<summary>參考解答</summary>

```python
games = fetch.fetch_games()
home = games.groupby("home").agg(RS=("home_runs", "sum"), RA=("away_runs", "sum"))
away = games.groupby("away").agg(RS=("away_runs", "sum"), RA=("home_runs", "sum"))
runs = home.add(away, fill_value=0)

standings = fetch.fetch_standings().set_index("team")
runs["PCT"] = standings["PCT"]
runs["pythag"] = metrics.pythag(runs["RS"], runs["RA"])
runs["luck"] = runs["PCT"] - runs["pythag"]
print(runs.sort_values("luck"))
```

你會發現：**中信兄弟**得失分是正的（+9），畢氏勝率 .508，但實際勝率只有 .475，是最「衰」的球隊；**樂天桃猿**則贏得比實力多。這就是球季觀察室要講的故事。

</details>

### 5. 想一想

把畢氏勝率的指數從 1.83 改成 2，結果差多少？（答案：差很小。1.83 是大聯盟用歷史資料找出來最準的數字，中職可以用一樣的值。）

---

## 完成檢查

- [ ] `src/metrics.py` 有 `iso`、`babip`、`pythag` 三個函式
- [ ] ISO、BABIP 和野球革命的差異都小於 0.001
- [ ] 知道哪一隊運氣最好、哪一隊最差
- [ ] `git commit -m "Day 6: ISO、BABIP、畢氏勝率"`

## 明天預告

wOBA 和 FIP 比較複雜，各自有一個要用全聯盟資料算出來的「常數」。算完後寫 clean.py，把整理好的表格（包含中職官網的半季戰績）存成 CSV。
