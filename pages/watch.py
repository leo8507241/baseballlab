import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import model, ui
from src.data import load, load_pa
from src.splits import woba_weight as RESULT_WEIGHT

ui.setup('球季觀察室')
teams, batters, pitchers, const, lg=load()

team=st.pills('選擇球隊',teams['team'],default=teams['team'].iloc[0])
if team is None:
    st.stop()
T = teams.set_index("team").loc[team]
abbr, color = T["abbr"], T["color"]
def team_table():
    rows=[]
    tp=pd.DataFrame(model.team_pitching(pitchers)).set_index('abbr')
    for _, t in teams.iterrows():
        b=batters[batters['abbr']==t['abbr']]
        sp=pitchers[(pitchers['abbr']==t['abbr']) & (pitchers['role']=='先發')]
        w=b['PA']
        rows.append({
            'team':t['team'],
            "打擊":(b['wOBA_calc']*w).sum()/ w.sum(),
            "長打":(b['ISO_calc']*w).sum()/w.sum(),
            '選球':((b['BBp']-b['Kp'])*w).sum()/w.sum(),
            "先發": -(sp["FIP_calc"] * sp["IP"]).sum() / sp["IP"].sum(),   # 負號：越低越好
            "牛棚": -tp.loc[t["abbr"], "bullpen_fip"],
            "守備": tp.loc[t["abbr"], "DER"]
        })
    df=pd.DataFrame(rows).set_index('team')
    return (50 + 15*(df-df.mean())/df.std().clip(10,90))

scores = team_table()
c1, c2 = st.columns(2)
with c1:
    cats = list(scores.columns)
    fig = go.Figure()
    fig.add_scatterpolar(r=[50] * 7, theta=cats + cats[:1], name="聯盟平均",
                         line=dict(color="#8C9BB0", dash="dot"))
    vals = scores.loc[team].tolist()
    fig.add_scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], fill="toself", name=team,
                         line=dict(color=color))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="#26384F"),
                                 angularaxis=dict(gridcolor="#26384F", linecolor="#26384F")),
                      title="六項戰力（聯盟平均 = 50）", height=380, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")
with c2:
    luck=T['luck']
    ui.kpi('實際勝率',ui.f3(T['PCT']))
    ui.kpi('畢氏勝率',ui.f3(T['pythag']))
    ui.kpi('實際 − 畢氏',ui.f3(luck),note=ui.chip("贏得比實力多" if luck > 0 else "贏得比實力少","hot" if luck > 0 else "cold"))

st.header('本季話題球員')
tb=batters[(batters['abbr']==abbr) & (batters['PA']>=150)]
tpit=pitchers[(pitchers['abbr']==abbr) & (pitchers['IP']>=30)]
tags=[]
rise = tb[tb['prev_PA']>=100].assign(d=lambda d: d["wOBA"] - d["prev_wOBA"]).nlargest(1,'d')
bubble = tb[tb['prev_PA']>=100].assign(d=lambda d: d["BABIP"] - d["prev_BABIP"]).nlargest(1,'d')   # ← 從下面移上來
if len(rise) and rise.iloc[0]['d'] >= 0.030:
    r = rise.iloc[0]
    why = (f"三振率 {r['prev_Kp']:.1f}% → {r['Kp']:.1f}%，"
           f"保送率 {r['prev_BBp']:.1f}% → {r['BBp']:.1f}%。")
    if len(bubble) and bubble.iloc[0]["d"] >= 0.030 and bubble.iloc[0]["player_id"] == r["player_id"]:
        why = "進步明顯，但 BABIP 也大幅上升，需要觀察能不能維持。"
    tags.append(("good", "異軍突起", r["name"], f"wOBA {ui.f3(r['wOBA'])}（去年 {ui.f3(r['prev_wOBA'])}）", why))
under=tpit.assign(d=tpit["ERA"] - tpit["FIP_calc"]).nlargest(1,'d')
if len(under) and under.iloc[0]["d"] >= 0.5:
    r = under.iloc[0]
    tags.append(("cold", "被低估", r["name"], f"ERA {r['ERA']:.2f} ／ FIP {r['FIP_calc']:.2f}",
                 "防禦率被守備或運氣拖累，實際投球內容比成績好。"))
if len(bubble) and bubble.iloc[0]["d"] >= 0.030:
    r = bubble.iloc[0]
    tags.append(("hot", "泡沫警示", r["name"], f"BABIP {ui.f3(r['BABIP'])}（去年 {ui.f3(r['prev_BABIP'])}）",
                 "打進場內的球落地比例明顯升高，打擊成績可能有運氣成分。"))
down = tpit[tpit["prev_IPOut"] >= 90].assign(d=lambda d: d["Kp"] - d["prev_Kp"]).nsmallest(1, "d")
if len(down) and down.iloc[0]["d"] <= -3:
    r = down.iloc[0]
    tags.append(("bad", "真的退步", r["name"], f"三振率 {r['Kp']:.1f}%（去年 {r['prev_Kp']:.1f}%）",
                 "三振能力下滑不太受運氣影響，值得觀察球速或球種變化。"))
cols = st.columns(2)
for i, (tone, label, name, nums, why) in enumerate(tags):
    with cols[i % 2]:
        st.markdown(f'<div class="card">{ui.chip(label, tone)}<h4 style="margin:8px 0 2px">{name}</h4>'
                    f'<div class="num" style="font-size:20px">{nums}</div>'
                    f'<div class="kpi-label">{why}</div></div>', unsafe_allow_html=True)
if not tags:
    st.caption("這一隊沒有符合條件的話題球員。")
