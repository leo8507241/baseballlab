import pandas as pd
from src.metrics import W


woba_weight={"uBB": W["ubb"], "HBP": W["wHBP"], "1B": W["w1B"],
             "2B": W["w2B"], "3B": W["w3B"], "HR": W["wHR"]}

not_count={'SH','SH_E','IBB','','nan'}

def prepare(pa,scale):
    pa=pa.copy()
    pa['result']=pa['result'].fillna('').astype(str)
    pa=pa[~pa['result'].isin(not_count)]
    pa['woba_val']=pa['result'].map(woba_weight).fillna(0)*scale
    pa['pa_round']=pd.to_numeric(pa['pa_round'], errors='coerce').clip(upper=3)
    return pa

def summarize(pa,keys):
    g=pa.groupby(keys)
    return g.agg(PA=('woba_val','size'),wOBA=('woba_val','mean')).reset_index()
