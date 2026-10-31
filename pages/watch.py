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
