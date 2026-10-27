import streamlit as st

st.set_page_config(page_title='好球帶研究室',page_icon='⚾',layout='wide')

pages = [
    st.Page("pages/home.py", title="首頁", default=True),
    st.Page("pages/academy.py", title="數據學院"),
    st.Page("pages/watch.py", title="球季觀察室"),
    st.Page("pages/predict.py", title="台灣大賽預測"),
]

st.navigation(pages,position='top').run()
