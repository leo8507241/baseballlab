"""把網站推上 GitHub，Streamlit Cloud 會自動重新部署。用法：python scripts/deploy.py"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Day 32：先跑上線前檢查，沒通過就不上傳
if subprocess.run([sys.executable, "scripts/check_before_deploy.py"], cwd=ROOT).returncode != 0:
    sys.exit("上線前檢查沒通過，取消部署")

msg = f"更新網站 {datetime.now():%Y-%m-%d %H:%M}"
subprocess.run(["git", "add", "."], cwd=ROOT, check=True)
if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
    sys.exit("沒有任何變更，不需要部署")
subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=True)
subprocess.run(["git", "push"], cwd=ROOT, check=True)
print("已推上 GitHub，Streamlit Cloud 約 1–2 分鐘後自動更新：https://haoqiudai-lab1.streamlit.app")
