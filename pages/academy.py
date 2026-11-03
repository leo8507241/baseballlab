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
q25,q50,q75=df[col].quantile([0.25,0.5,0.75])
best=df.nlargest(1,col) if s['higher_better'] else df.nsmallest(1, col)
st.markdown(f"**中職實例**：今年最{'高' if s['higher_better'] else '低'}的是 "
                f"{best.iloc[0]['name']}（{best.iloc[0]['team']}）{fmt(best.iloc[0][col])}；"
                f"聯盟中位數 {fmt(q50)}。")

with st.expander("看公式"):
        st.latex(s["formula"])
