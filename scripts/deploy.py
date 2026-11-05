"""把網站上傳到 Hugging Face Space。用法：python scripts/deploy.py"""
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent
SPACE = "leo88888/haoqiudai-lab"

api = HfApi()
api.create_repo(SPACE, repo_type="space", space_sdk="static", exist_ok=True)   # 先建空殼，README 的 sdk 會改成 streamlit

api.upload_folder(
    folder_path=str(ROOT), repo_id=SPACE, repo_type="space",
    ignore_patterns=[".venv/*", "data/raw/*", "tutorial/*", "tests/*", ".git/*", "notebooks/*",
                     "*.ipynb", "anaconda_projects/*", ".virtual_documents/*",
                     "**/__pycache__/*", "**/.ipynb_checkpoints/*", "explore*.py", ".DS_Store"],
    commit_message="更新網站",
)
print(f"上傳完成：https://huggingface.co/spaces/{SPACE}")
