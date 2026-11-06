"""上線前檢查：跑頁面測試和實驗 1、2，結果寫進 logs/stability_log.csv；沒通過就回傳錯誤碼，不准部署。"""
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

tests_ok = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT).returncode == 0
subprocess.run([sys.executable, "scripts/run_experiments.py"], cwd=ROOT, check=True)
summary = json.loads((ROOT / "data/clean/stability_summary.json").read_text(encoding="utf-8"))

row = {"時間": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "頁面測試": tests_ok,
       "實驗1": summary["exp1"]["通過"], "實驗2": summary["exp2"]["通過"],
       "實驗3區間寬度": round(summary["exp3"]["區間寬度"], 3), "實驗4最大差距": round(summary["exp4"]["最大差距"], 3)}
log = ROOT / "logs" / "stability_log.csv"
log.parent.mkdir(exist_ok=True)
new = not log.exists()
with log.open("a", encoding="utf-8") as f:
    if new:
        f.write(",".join(row) + "\n")
    f.write(",".join(str(v) for v in row.values()) + "\n")

ok = tests_ok and row["實驗1"] and row["實驗2"]
print("檢查通過，可以部署" if ok else "檢查沒通過，先不要部署")
sys.exit(0 if ok else 1)
