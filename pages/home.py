import streamlit as st

from src import ui
from src.data import load

ui.setup("首頁")              # 每一頁換成自己的標題
teams, batters, pitchers, const, lg = load()
st.write(f"讀到 {len(batters)} 位打者、{len(pitchers)} 位投手。")
ui.kpi("測試卡片", ".319", "聯盟 wOBA")
