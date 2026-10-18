# Day 33｜11/14（六）｜穩定性實驗報告與 README

> 預計時間：2 小時　｜　階段：收尾

## Jupyter 版做法

- 筆記本：`notebooks/D33.ipynb`，第一格放每日開場程式碼（見 [README](README.md#用-jupyter-做的方式)）。
- 新檔案或整個換掉（`%%writefile`）：`reports/stability_report.md`
- 要打開檔案修改中間：`README.md`
- **一定要在終端機執行**：
  - 第 6 步「打上版本標籤」的 `git push --tags`：第一次推送可能要輸入帳號和 token，`!` 沒辦法輸入
- 結束時在格子執行 `!git add .` 和 `!git commit -m "Day 33: 實驗報告與 README"`。

## 今天的目標

- 把五組實驗整理成一份**穩定性實驗報告**（企劃書 4-4 要求的產出）
- 寫一份清楚的 README：這個專案是什麼、怎麼執行、資料從哪來、方法是什麼
- 刪掉探索用的暫存檔，打上版本標籤 `v1.0`

## 為什麼要做這一步

實驗做完不寫下來，就等於沒做。報告要讓沒參與的人看懂：測了什麼、結果如何、代表什麼、做了哪些調整。README 則是老師、同學打開 GitHub 第一個看到的東西。

---

## 步驟

### 1. 穩定性實驗報告

新增 `reports/stability_report.md`，用 `python scripts/run_experiments.py` 最新的結果和你這週在 `my_notes.md` 的紀錄來填。建議結構：

> **Jupyter**：新的一格，第一行寫 `%%writefile reports/stability_report.md`，下面貼這段，執行後就會存成檔案（會覆蓋同名檔案）。

```markdown
# 好球帶研究室：模型穩定性實驗報告

## 結論
（3 句話：哪些通過、哪些沒通過、網站因此做了什麼調整）

## 實驗結果

| 實驗 | 結果 | 標準 | 通過 |
| --- | --- | --- | --- |
| 1. 模擬次數與亂數 | 標準差 0.46 個百分點 | < 1 | ✓ |
| 2. 參數敏感度 | 先發局數影響 1.2 個百分點；主場優勢 0–6% 影響 5.3 個百分點 | ≤ 5 | ✓ |
| 3. 資料重抽 | 奪冠機率 95% 區間 35%–90%；規則只有約 36% 達 80% 穩定 | 寬度 ≤ 10 | ✗ |
| 4. 資料截止日 | 8/31 84.1% → 9/15 75.3% → 季末 67.6% | 差距 ≤ 10 | ✗ |
| 5. 實際結果 | 最後一天揭曉時補上：命中率、Brier score、主場必勝的命中率 | 不劣於簡單方法 | ？ |

## 解讀
- 實驗 3：一個球季的得失分本身就有很大的隨機性……
- 實驗 4：中信兄弟下半季變強（上半季 20-38、下半季 36-24），整季平均低估了近況……

## 因此做的調整
- 預測頁的奪冠機率旁加上 95% 區間
- 弱點規則在重抽中成立不到 80% 就不顯示，應對策略也一起排除
- 上線前自動跑測試與實驗 1、2，沒通過不部署

## 下一步
- 近期比賽加權的實力估計（針對實驗 4）
- ……
```

每一組實驗可以加一張圖（例如實驗 1 的 30 個奪冠機率分布、實驗 4 的三個截止日折線），用 Plotly 畫好後，在網頁上用圖表右上角的相機按鈕下載 PNG，放進 `reports/` 再貼進報告。

### 2. 清理

> **Jupyter**：可以在格子裡執行，每一行指令前面加 `!`（例如 `!python scripts/update_data.py`）。

```bash
rm -f explore*.py
git status
```

- 刪掉 `explore.py`、`explore_runs.py`、`explore_metrics.py` 這些 Day 2–6 的探索檔
- Day 8 的 `scripts/fetch_all_pa.py` 已經被 `update_data.py` 取代，也可以刪掉
- 檢查有沒有 `print("test")` 這類除錯用的程式碼留在頁面裡

### 3. 檢查說明文字

打開 `src/` 的每個檔案，確認：

- [ ] 檔案最上面有一行說明這個檔案做什麼
- [ ] 每個函式下面有一行 `"""說明"""`
- [ ] 有「為什麼這樣寫」的地方有註解（例如 FIP 為什麼沒有觸身球）

不需要每一行都寫註解，只寫「看程式碼看不出來」的事。

### 4. 練習：寫 README

保留最上面 Hugging Face 的設定區塊（Day 26 寫的 `---` 那段），下面寫完整的說明。至少要有：

1. 一句話介紹 + 線上網址
2. 四個頁面各做什麼
3. 怎麼在自己電腦執行（安裝、更新資料、啟動）
4. 資料來源
5. 方法說明（畢氏勝率、Log5、蒙地卡羅、單場模型、規則引擎）
6. 已知限制

<details>
<summary>參考範例</summary>

> **Jupyter**：這段要插進 `README.md` 的中間，不能用 `%%writefile`。在 JupyterLab 左側檔案列表雙擊打開 `README.md`，貼到指定位置，按 `Cmd + S` 存檔。（保留最上面的 `---` 設定區塊，下面換成你的說明）

```markdown
# 好球帶研究室

用進階數據看懂中華職棒的互動網站。線上版：https://huggingface.co/spaces/<你的帳號>/haoqiudai-lab

## 網站內容

| 頁面 | 內容 |
| --- | --- |
| 首頁 | 球季數據亮點、加上畢氏勝率的戰績表 |
| 數據學院 | 14 個進階數據的白話解釋、中職分布、互動計算機 |
| 球季觀察室 | 球隊雷達圖、話題球員標籤、ERA vs FIP 散佈圖、球員卡 |
| 台灣大賽預測 | 系列賽奪冠機率、自選先發與打線的單場分析、弱點與策略、賽後揭曉 |

## 在自己電腦執行

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python scripts/update_data.py     # 第一次約 10 分鐘
    python scripts/run_experiments.py # 上線後實驗
    streamlit run app.py

## 資料來源

- 中華職棒官方網站（https://www.cpbl.com.tw/）：上下半季戰績（戰績頁）
- 野球革命 Rebas（https://www.rebas.tw/）：球員成績、逐打席紀錄、季後賽比分
- 兩個來源交叉比對：上半季＋下半季＝全年戰績；官網抓不到時改用野球革命計算

## 方法

- **系列賽**：畢氏勝率估算實力 → Log5 換算單場勝率（主場 +2.3%，來自中職 2023–2026 主場勝率）→ 蒙地卡羅模擬 10,000 次
- **單場**：依先發投手左右手調整打線 wOBA，結合先發 FIP、牛棚 FIP、守備效率估算兩隊得分，再用畢氏公式換算勝率
- **弱點與策略**：規則引擎，門檻以聯盟百分位數設定；Bootstrap 重抽中成立不到 80% 的弱點不顯示
- **上線後實驗**：五組穩定性實驗（亂數、參數、資料重抽、截止日、實際結果），報告見 `reports/stability_report.md`

## 已知限制

- wOBA 權重使用大聯盟近似值；FIP 因資料沒有觸身球，只用保送計算
- 單場模型的係數是簡化假設，未經歷史資料校正
- 奪冠機率的 95% 區間很寬（約 35%–90%），網站上的單一數字只是中間值
- 拆分數據樣本少於 30 個打席時不採用
```

（README 裡的程式碼區塊用縮排四格，避免跟外層的格式衝突。）

</details>

### 5. 最後檢查 `requirements.txt`

> **Jupyter**：可以在格子裡執行，每一行指令前面加 `!`（例如 `!python scripts/update_data.py`）。

```bash
pip freeze | grep -i -E "streamlit|pandas|numpy|plotly|requests"
```

確認版本跟 `requirements.txt` 寫的一樣。

### 6. 打上版本標籤

> **一定要在終端機執行**：第一次推送可能要輸入帳號和 token，`!` 沒辦法輸入。在 JupyterLab 用 **File → New → Terminal** 開一個終端機執行。

```bash
python -m pytest -q
git add .
git commit -m "Day 33: 實驗報告與 README"
git tag v1.0
git push --tags
python scripts/deploy.py
```

`git tag v1.0`：在這個 commit 貼一個標籤。之後就算繼續改，隨時都能回到「期末交出去的版本」。

---

## 完成檢查

- [ ] `reports/stability_report.md` 寫完，五組實驗都有結果和解讀
- [ ] GitHub 首頁顯示完整的 README
- [ ] 沒有探索用的暫存檔
- [ ] `src/` 每個函式都有一行說明
- [ ] GitHub 上看得到 `v1.0` 標籤
- [ ] 線上版是最新版本

## 明天預告

最後一天：揭曉台灣大賽的答案，跟鎖定的預測對照，再回顧整個專案、整理 Demo 流程。
