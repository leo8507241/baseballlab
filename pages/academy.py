import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src import metrics, ui
from src.data import load
ui.setup('數據學院')
teams,batters,pitchers,const,lg=load()
STATS=json.loads((Path(__file__).resolve().parent.parent/"content" / "stats.json").read_text(encoding='utf-8'))
TABLES = {"batters": batters, "pitchers": pitchers}

CALC = {
    "wOBA": ([("1B", 90), ("2B", 25), ("3B", 3), ("HR", 15), ("BB", 48), ("IBB", 3), ("HBP", 5), ("AB", 480), ("SF", 4)],
             lambda v: metrics.woba(v["HBP"], v["1B"] + v["2B"] + v["3B"] + v["HR"], v["2B"], v["3B"], v["HR"],
                                    v["AB"], v["BB"], v["IBB"], v["SF"]) * const["woba_scale"]),
    "ISO": ([("AB", 480), ("2B", 25), ("3B", 3), ("HR", 15)],
            lambda v: metrics.iso(v["2B"], v["3B"], v["HR"], v["AB"])),
    "BABIP": ([("H", 135), ("HR", 15), ("AB", 480), ("SO", 85), ("SF", 4)],
              lambda v: metrics.babip(v["H"], v["HR"], v["AB"], v["SO"], v["SF"])),
    "FIP": ([("IP", 150), ("HR", 12), ("BB", 40), ("SO", 130)],
            lambda v: metrics.fip(v["HR"], v["SO"], v["BB"], v["IP"] * 3, const["fip_const"])),
}
levels = ["入門", "進階", "高階"]
nav , main=st.columns([1,4])
with nav:
    key=st.radio('選擇數據',[s['key'] for s in STATS],format_func=lambda k: "{0[group]}｜{0[key]}（{0[level]}）".format(
                       next(s for s in STATS if s["key"] == k)))
s=next( x for x in STATS if x['key']==key)
df=TABLES[s['table']]
df=df[df[s['min_col']]>=s['min']]
col = s["column"]
fmt = ui.f3 if s["fmt"] == "{:.3f}" else s["fmt"].format   # 三位小數用棒球習慣：.320

with main:
    st.markdown(" → ".join(f"**{l}**" if l == s["level"] else l for l in levels))
    st.header(f"{s['key']}　{s['full']}")
    st.markdown(f"#### {s['one']}")
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="card"><p class="eyebrow">為什麼需要它</p>{s["why"]}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card"><p class="eyebrow">什麼時候用</p>{s["use"]}</div>', unsafe_allow_html=True)
    result=None
    if key in CALC:
        st.subheader('自己算算看')
        fields , fn= CALC[key]
        cols=st.columns(len(fields))
        val={}
        for i , (name,d) in enumerate(fields):
            val[name]=cols[i].number_input(name, min_value=0.0, value=float(d), key=f"{key}_{name}")
        try:
            result=fn(val)
        except ZeroDivisionError:
                st.warning("分母是 0，請檢查輸入的數字。")
q25,q50,q75=df[col].quantile([0.25,0.5,0.75])
best=df.nlargest(1,col) if s['higher_better'] else df.nsmallest(1, col)
st.markdown(f"**中職實例**：今年最{'高' if s['higher_better'] else '低'}的是 "
                f"{best.iloc[0]['name']}（{best.iloc[0]['team']}）{fmt(best.iloc[0][col])}；"
                f"聯盟中位數 {fmt(q50)}。")

with st.expander("看公式"):
        st.latex(s["formula"])
fig = go.Figure()
fig.add_histogram(x=df[col], nbinsx=25, marker_color="#26384F", name="中職球員分布")
for qv, label in [(q25, "25 百分位"), (q50, "中位數"), (q75, "75 百分位")]:
    fig.add_vline(x=qv, line_dash="dot", line_color="#8C9BB0", annotation_text=label)
if result is not None:
    fig.add_vline(x=result, line_color="#F4B23E", line_width=3,
                  annotation_text=f"你的計算 {fmt(result)}", annotation_font_color="#F4B23E")
fig.update_layout(title=f"好壞標準：2026 中職分布（{s['min_col']} ≥ {s['min']}）", height=320,
                  showlegend=False, margin=dict(t=50),
                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, width="stretch")
