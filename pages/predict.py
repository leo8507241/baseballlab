
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
