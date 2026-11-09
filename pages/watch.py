import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import model, ui
from src.data import load, load_pa, load_span
from src.splits import woba_weight as RESULT_WEIGHT

ui.setup('球季觀察室')
teams, batters, pitchers, const, lg=load()
span = load_span()
ui.glossary("**wOBA** 打者整體攻擊力（越高越好）｜**ERA** 防禦率，每九局失掉的責任分｜"
            "**FIP** 只看三振、保送、全壘打的投手表現（越低越好）｜**BABIP** 打進場內的球變成安打的比例")

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
    return (50 + 15*(df-df.mean())/df.std()).clip(10,90)

scores = team_table()
c1, c2 = st.columns(2)
with c1:
    cats = list(scores.columns)
    fig = go.Figure()
    fig.add_scatterpolar(r=[50] * 7, theta=cats + cats[:1], name="聯盟平均",
                         line=dict(color="#8C9BB0", dash="dot"), hoverinfo="skip")
    vals = scores.loc[team].tolist()
    fig.add_scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], fill="toself", name=team,
                         line=dict(color=color), hovertemplate="%{theta}：%{r:.0f} 分<extra></extra>")
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="#26384F"),
                                 angularaxis=dict(gridcolor="#26384F", linecolor="#26384F")))
    ui.style_fig(fig, 380, "六項戰力（聯盟平均 = 50）")
    st.plotly_chart(fig, width="stretch")
    s = scores.loc[team]
    ui.insight(f"{team}的相對強項是<b>{s.idxmax()}</b>（{s.max():.0f} 分），"
               f"相對弱項是<b>{s.idxmin()}</b>（{s.min():.0f} 分）。50 分是六隊平均，分數越高越好。")
    st.caption(f"2026 例行賽（{span}）｜全隊數據，以六隊平均 50 分換算")
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
# ---------- Day 21：ERA vs FIP 散佈圖 ----------
st.header("ERA 和 FIP 的落差")
q = pitchers[pitchers["IP"] >= 40].reset_index(drop=True)
mine = q["abbr"] == abbr
st.caption("點圖上任一位投手，下方的數據和走勢圖會跟著切換。")
fig = go.Figure()
fig.add_scatter(x=q.loc[~mine, "FIP_calc"], y=q.loc[~mine, "ERA"], mode="markers", name="其他球隊",
                marker=dict(color="#8C9BB0", opacity=0.35, size=8), text=q.loc[~mine, "name"],
                customdata=q.index[~mine], hovertemplate="%{text}<br>FIP %{x:.2f} / ERA %{y:.2f}")
fig.add_scatter(x=q.loc[mine, "FIP_calc"], y=q.loc[mine, "ERA"], mode="markers", name=team,
                marker=dict(color=color, size=12, line=dict(color="white", width=1)), text=q.loc[mine, "name"],
                customdata=q.index[mine], hovertemplate="%{text}<br>FIP %{x:.2f} / ERA %{y:.2f}")

lo, hi = 1.5, max(q["ERA"].max(), q["FIP_calc"].max()) + 0.3
fig.add_scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(dash="dash", color="#8C9BB0"),
                showlegend=False, hoverinfo="skip")
fig.add_annotation(x=lo + 0.3, y=hi - 0.3, text="ERA > FIP：運氣差、被低估", showarrow=False,
                   font=dict(color="#4A86DE"), xanchor="left")
fig.add_annotation(x=hi - 0.3, y=lo + 0.3, text="ERA < FIP：運氣好、小心回落", showarrow=False,
                   font=dict(color="#E2483E"), xanchor="right")
fig.update_layout(xaxis_title="FIP 投手自身表現（越左越好）", yaxis_title="ERA 防禦率（越下面越好）")
ui.style_fig(fig, 460)
event = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points")



picked = None
if event and event.selection.points:
    picked = q.loc[event.selection.points[0]["customdata"]]
if picked is None:
    picked = q[mine].sort_values("IP", ascending=False).iloc[0]
gap = picked["ERA"] - picked["FIP_calc"]
if gap >= 0.5:
    verdict = "防禦率可能被守備或運氣拖累，實際投球內容比成績好。"
elif gap <= -0.5:
    verdict = "防禦率可能有守備或運氣幫忙，之後有回升的風險。"
else:
    verdict = "兩者很接近，成績大致反映實際投球內容。"
ui.insight(f"<b>{picked['name']}</b> 的 ERA {picked['ERA']:.2f}、FIP {picked['FIP_calc']:.2f}，"
           f"ERA 比 FIP {'高' if gap >= 0 else '低'} {abs(gap):.2f}：{verdict}")
st.caption(f"2026 例行賽（{span}）｜投球 40 局以上，共 {len(q)} 位投手")
with st.expander("打者版：BABIP 和 wOBA"):
    qb = batters[batters["PA"] >= 200]
    mb = qb["abbr"] == abbr
    f2 = go.Figure()
    f2.add_scatter(x=qb.loc[~mb, "BABIP"], y=qb.loc[~mb, "wOBA_calc"], mode="markers", name="其他球隊",
                   marker=dict(color="#8C9BB0", opacity=0.35), text=qb.loc[~mb, "name"],
                   hovertemplate="%{text}<br>BABIP %{x:.3f} / wOBA %{y:.3f}<extra></extra>")
    f2.add_scatter(x=qb.loc[mb, "BABIP"], y=qb.loc[mb, "wOBA_calc"], mode="markers", name=team,
                   marker=dict(color=color, size=11), text=qb.loc[mb, "name"],
                   hovertemplate="%{text}<br>BABIP %{x:.3f} / wOBA %{y:.3f}<extra></extra>")
    f2.add_vline(x=qb["BABIP"].mean(), line_dash="dot", annotation_text="聯盟平均 BABIP")
    f2.update_layout(xaxis_title="BABIP 打進場內的安打率", yaxis_title="wOBA 整體攻擊力（越高越好）")
    ui.style_fig(f2, 400)
    st.plotly_chart(f2, width="stretch")
    st.caption(f"2026 例行賽（{span}）｜打席 200 以上，共 {len(qb)} 位打者")
p=picked
st.subheader(f'{p['name']}({p['team']})')
c1, c2, c3=st.columns(3)
c1.metric("ERA", f"{p['ERA']:.2f}", help="防禦率：每九局失掉的責任分，越低越好。")
c2.metric("FIP", f"{p['FIP_calc']:.2f}", help="只看三振、保送、全壘打算出的投手表現，換算成和 ERA 相近的尺度，越低越好。")
c3.metric("落差 ERA − FIP", f"{p['ERA'] - p['FIP_calc']:+.2f}", help="正數代表 ERA 比 FIP 差，可能被守備或運氣拖累。")

items = [("三振率", "Kp", True, "{:.1f}%"), ("保送率", "BBp", False, "{:.1f}%"),
         ("被全壘打", "HR9", False, "{:.2f}"), ("滾地球率", "GBp", True, "{:.1f}%"),
         ("FIP 自身表現", "FIP_calc", False, "{:.2f}")]
names, pcts, texts=[],[],[]
for label,col,higher_better,fmt in items:
    pct=(q[col]<p[col]).mean()*100
    pcts.append(pct if higher_better else 100-pct)
    names.append(label)
    texts.append(f'{fmt.format(p[col])} (PR{pcts[-1]:.0f})')
fig = go.Figure(go.Bar(x=pcts, y=names, orientation="h", text=texts, textposition="outside",
                       hovertemplate="%{y}：%{text}<extra></extra>",
                       marker=dict(color=pcts, colorscale=[[0, "#4A86DE"], [0.5, "#96A0AF"], [1, "#E2483E"]],
                                   cmin=0, cmax=100)))
fig.update_layout(xaxis=dict(range=[0, 120], showticklabels=False), yaxis=dict(autorange="reversed"))
ui.style_fig(fig, 300, "聯盟百分位數（紅色越深越好）")
st.plotly_chart(fig, width="stretch")
ui.insight(f"{p['name']}最突出的是<b>{names[int(np.argmax(pcts))]}</b>（PR{max(pcts):.0f}），"
           f"最需要注意的是<b>{names[int(np.argmin(pcts))]}</b>（PR{min(pcts):.0f}）。"
           "PR90 代表贏過聯盟 90% 的投手。")
st.caption(f"2026 例行賽（{span}）｜和投球 40 局以上的 {len(q)} 位投手比較")
pa = load_pa()
mine_pa = pa[pa["pitcher_id"] == p["player_id"]].copy()
mine_pa = mine_pa[~mine_pa["result"].isin(["IBB", "SH", "SH_E", ""])]
mine_pa["w"] = mine_pa["result"].map(RESULT_WEIGHT).fillna(0) * const["woba_scale"]
by_game = mine_pa.groupby("date")["w"].agg(["sum", "size"]).sort_index()
roll = by_game["sum"].rolling(5, min_periods=3).sum() / by_game["size"].rolling(5, min_periods=3).sum()
fig = go.Figure(go.Scatter(x=roll.index, y=roll, mode="lines", line=dict(color=color, width=3),
                           fill="tozeroy", fillcolor="rgba(244,178,62,0.08)"))
fig.add_hline(y=lg["wOBA"], line_dash="dot", annotation_text="聯盟平均")
fig.update_layout(xaxis_title="比賽日期", yaxis_title="被 wOBA")
ui.style_fig(fig, 300, "最近 5 場被 wOBA 走勢（對手的攻擊力，越低越好）")
st.plotly_chart(fig, width="stretch")
st.caption(f"2026 例行賽（{span}）｜每個點是到該場為止最近 5 場的被 wOBA，至少滿 3 場才開始計算")
