
"""全站共用的樣式與小元件（卡片、數字方塊、標籤）。"""
import streamlit as st

COLORS = {"bg": "#0D1520", "surface": "#142030", "surface2": "#1B2A3D", "line": "#26384F",
          "fg": "#E9EEF4", "muted": "#8C9BB0", "accent": "#F4B23E",
          "good": "#46B98C", "bad": "#E8654F", "cold": "#4A86DE", "hot": "#E2483E"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Noto+Sans+TC:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
h1, h2, h3 { font-weight: 900 !important; letter-spacing: .02em; }
.num { font-family: 'Barlow Condensed', sans-serif; font-variant-numeric: tabular-nums; }
.eyebrow { color: #F4B23E; font-size: 13px; letter-spacing: .14em; font-weight: 700; margin: 0; }
.card { background: #142030; border: 1px solid #26384F; border-radius: 10px; padding: 18px 20px; margin-bottom: 12px; }
.kpi-label { color: #8C9BB0; font-size: 13px; }
.kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 40px; font-weight: 700; line-height: 1.1; }
.kpi-who { font-weight: 700; }
.chip { display: inline-block; font-size: 12px; font-weight: 700; padding: 2px 9px;
        border-radius: 999px; border: 1px solid currentColor; margin-top: 4px; }
.chip.good { color: #46B98C; } .chip.bad { color: #E8654F; } .chip.warn { color: #F4B23E; }
.chip.cold { color: #4A86DE; } .chip.hot { color: #E2483E; }
.card ul { margin: 0; padding-left: 20px; } .card li { margin-bottom: 6px; }
</style>
"""

def setup(title):
    st.markdown(CSS, unsafe_allow_html=True)
    st.title(title)

def chip(text, tone="warn"):
    return f'<span class="chip {tone}">{text}</span>'

def kpi(label, value, who="", note=""):
    st.markdown(f'<div class="card"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-who">{who}</div>{note}</div>',
                unsafe_allow_html=True)

def bullet_card(title, items, color):
    lis = "".join(f"<li>{x}</li>" for x in items)
    st.markdown(f'<div class="card" style="border-top:4px solid {color}">'
                f'<b>{title}</b><ul style="margin-top:8px">{lis}</ul></div>', unsafe_allow_html=True)

def f3(x):
    return f"{x:.3f}".lstrip("0") if x >= 0 else "-" + f"{-x:.3f}".lstrip("0")
