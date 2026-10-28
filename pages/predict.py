
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import config, fetch, model, rules, ui
from src.data import load

ui.setup('台灣大賽預測')
teams, batters, pitchers, const, lg=load()
A_name , B_name=config.TS_TEAMS
A=teams.set_index('team').loc[A_name]
B=teams.set_index('team').loc[B_name]

p_a,results,prob=model.simulate_series(A['pythag'],B['pythag'],config.TS_HOME_PATTERN,hfa=config.HOME_ADVANTAGE,need=config.TS_NEED)
st.markdown('<p class="eyebrow">系列賽預測 · 蒙地卡羅模擬 10,000 次</p>', unsafe_allow_html=True)

c1,c2=st.columns(2)

with c1:
    ui.kpi(f'{A_name}奪冠機率',f'{p_a:.0%}',f"畢氏勝率{ui.f3(A['pythag'])}")
with c2:
    ui.kpi(f'{B_name}奪冠機率',f'{1-p_a:.0%}',f"畢氏勝率{ui.f3(B['pythag'])}")


order = ["4-0", "4-1", "4-2", "4-3", "3-4", "2-4", "1-4", "0-4"]
fig=go.Figure(go.Bar(
    x=order , y=[results.get(k,0)/100 for k in order],
    marker_color=[A["color"]] * 4 + [B["color"]] * 4,
    text=[f'{results.get(k,0)/100:.1f}%' for k in order],textposition="outside",cliponaxis=False))
fig.update_layout(title=f"系列賽結果分布（左邊 {A_name} 勝、右邊 {B_name} 勝）",
                  yaxis_title="機率（%）", height=320, margin=dict(t=50, b=20),
                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, width="stretch")
with st.expander("這個機率怎麼來的？"):
    neutral = model.log5(A["pythag"], B["pythag"])
    st.markdown(f"""
1. **畢氏勝率**：用整季得分與失分估算實力。{A_name} 得 {A['RS']} 失 {A['RA']} → {ui.f3(A['pythag'])}；
   {B_name} 得 {B['RS']} 失 {B['RA']} → {ui.f3(B['pythag'])}。
2. **Log5**：換算成兩隊對戰的單場勝率。中立場地 {A_name} 勝率 {neutral:.1%}，
   主場再加 {config.HOME_ADVANTAGE:.1%}、客場減 {config.HOME_ADVANTAGE:.1%}。
3. **蒙地卡羅模擬**：照七戰四勝和主客場順序，把整個系列賽跑 10,000 次，數每隊贏了幾次。
""")
    st.latex(r"\text{畢氏勝率}=\frac{\text{得分}^{1.83}}{\text{得分}^{1.83}+\text{失分}^{1.83}}"
             r"\qquad P(A)=\frac{A-AB}{A+B-2AB}")

st.header('單場對戰分析')
g=st.selectbox('場次',range(len(config.TS_HOME_PATTERN)),
              format_func=lambda i : f'G{i+1} {A_name if config.TS_HOME_PATTERN[i] else B_name}主場')
a_home=config.TS_HOME_PATTERN[g]

def team_picker(team,col):
    abbr=teams.set_index('team').loc[team,'abbr']
    sps=pitchers[(pitchers['abbr']==abbr) & (pitchers['role']=='先發')].sort_values('IP',ascending=False)
    bats = batters[batters["abbr"] == abbr].sort_values("PA", ascending=False)
    with col:
        st.subheader(team)
        sp_name = st.selectbox("先發投手", sps["name"],
                               format_func=lambda n: f"{n}（{rules.HAND.get(sps.set_index('name').loc[n, 'throws'], '')}・"
                                                     f"FIP {sps.set_index('name').loc[n, 'FIP_calc']:.2f}）",
                               key=f"sp_{abbr}")
        lineup_names = st.multiselect("先發打線（9 人）", bats["name"], default=list(bats["name"][:9]),
                                      max_selections=9, key=f"lu_{abbr}")
    sp = sps.set_index("name").loc[sp_name].copy()
    sp["name"] = sp_name
    lineup = bats[bats["name"].isin(lineup_names)]
    bench = bats[~bats["name"].isin(lineup_names)]
    return sp, lineup, bench, abbr

ca, cb = st.columns(2)
sp_a, lu_a, bench_a, abbr_a = team_picker(A_name, ca)
sp_b, lu_b, bench_b, abbr_b = team_picker(B_name, cb)
if len(lu_a) != 9 or len(lu_b) != 9:
    st.info("兩隊都選滿 9 位打者後，會算出這場比賽的勝率。")
    st.stop()
ctx = model.league_context(teams, pitchers, lg["wOBA"])
tp = pd.DataFrame(model.team_pitching(pitchers)).set_index("abbr")

def lineup_woba(lineup, sp):
    return lineup.apply(lambda b: rules.bat_woba(b, sp["throws"]), axis=1).mean()

inn = lambda sp: 5 if sp.get("wOBA_round3", 0) > lg["wOBA"] + 0.02 else 6
r_a = model.expected_runs(lineup_woba(lu_a, sp_b), lu_a["wOBA_calc"].mean(), sp_b["FIP_calc"],
                          tp.loc[abbr_b, "bullpen_fip"], tp.loc[abbr_b, "DER"], ctx, inn(sp_b), a_home)
r_b = model.expected_runs(lineup_woba(lu_b, sp_a), lu_b["wOBA_calc"].mean(), sp_a["FIP_calc"],
                          tp.loc[abbr_a, "bullpen_fip"], tp.loc[abbr_a, "DER"], ctx, inn(sp_a), not a_home)
p_game = model.win_prob_from_runs(r_a, r_b)

st.markdown(f'<div class="card"><p class="eyebrow">這場比賽的勝率</p>'
            f'<div class="kpi-value"><span style="color:{A["color"]}">{A_name} {p_game:.0%}</span> : '
            f'<span style="color:{B["color"]}">{1 - p_game:.0%} {B_name}</span></div>'
            f'<div class="kpi-label">預估得分 {r_a:.1f} : {r_b:.1f}</div></div>', unsafe_allow_html=True)
