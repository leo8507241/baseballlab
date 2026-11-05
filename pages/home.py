import streamlit as st

from src import config, ui
from src.data import load, load_half

ui.setup("好球帶研究室")
teams, batters, pitchers, const, lg = load()

st.markdown(f"""
<div class="card" style="padding:28px">
  <p class="eyebrow">2026 中華職棒 · {config.TS_TEAMS[0]} vs {config.TS_TEAMS[1]}</p>
  <h2 style="margin:6px 0 10px">用進階數據，看懂這個十月。</h2>
  <p style="color:#8C9BB0;max-width:36em">從 wOBA 到 FIP，從被低估的球員到台灣大賽勝率，
  這裡的每個結論都有數據根據。</p>
</div>""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.page_link("pages/academy.py", label="數據學院：每個數據的白話解釋與計算機")
c2.page_link("pages/watch.py", label="球季觀察室：誰被低估？誰是泡沫？")
c3.page_link("pages/predict.py", label="台灣大賽預測：自選先發與打線算勝率")
st.header('球季數據亮點')
qb=batters[batters['PA']>=300]
qp=pitchers[pitchers['IP']>=50]
top_woba=qb.nlargest(1,'wOBA_calc').iloc[0]
gap=qp.assign(d=qp['ERA']-qp['FIP_calc']).nlargest(1,'d').iloc[0]
top_k = qp[qp["role"] == "先發"].nlargest(1, "Kp").iloc[0]
top_babip = qb.nlargest(1, "BABIP").iloc[0]
cols = st.columns(4)
with cols[0]:
    ui.kpi("wOBA 最高", ui.f3(top_woba["wOBA_calc"]), f"{top_woba['team']}・{top_woba['name']}")
with cols[1]:
    ui.kpi("ERA 與 FIP 落差最大", f"+{gap['d']:.2f}", f"{gap['team']}・{gap['name']}", ui.chip("運氣差", "cold"))
with cols[2]:
    ui.kpi("先發三振率最高", f"{top_k['Kp']:.1f}%", f"{top_k['team']}・{top_k['name']}", ui.chip("聯盟第 1", "good"))
with cols[3]:
    ui.kpi("BABIP 最高", ui.f3(top_babip["BABIP"]), f"{top_babip['team']}・{top_babip['name']}",
           ui.chip("可能有運氣成分", "hot"))
st.header("全年戰績")
show = teams[["rank", "team", "W", "L", "T", "PCT", "RS", "RA", "pythag", "luck"]]
st.dataframe(show, hide_index=True, width="stretch", column_config={
    "rank": "排名", "team": "球隊", "PCT": st.column_config.NumberColumn("勝率", format="%.3f"),
    "RS": "得分", "RA": "失分",
    "pythag": st.column_config.NumberColumn("畢氏勝率", format="%.3f"),
    "luck": st.column_config.NumberColumn("實際 − 畢氏", format="%+.3f",
                                          help="正數代表贏得比得失分差應有的多，可能有運氣成分")})
half = load_half()
if half is not None:
    st.subheader("上下半季戰績")
    c1, c2 = st.columns(2)
    for col, name in [(c1, "上半季"), (c2, "下半季")]:
        h = half[half["half"] == name].copy()
        h["PCT"] = h["W"] / (h["W"] + h["L"])
        h = h.sort_values("PCT", ascending=False)
        col.markdown(f"**{name}**（冠軍：{h.iloc[0]['team']}）")
        col.dataframe(h[["team", "W", "L", "T", "PCT"]], hide_index=True, width="stretch", column_config={
            "team": "球隊", "PCT": st.column_config.NumberColumn("勝率", format="%.3f")})
    st.caption(f"半季戰績來源：{half['source'].iloc[0]}，並已跟野球革命的全年戰績交叉比對")
st.caption("資料來源：野球革命 Rebas、中華職棒官方網站")
