import pandas as pd
from src.metrics import W

# 打席結果代碼 → wOBA 權重（沒列出的都是出局，權重 0）
woba_weight={"uBB": W["ubb"], "HBP": W["wHBP"], "1B": W["w1B"],
             "2B": W["w2B"], "3B": W["w3B"], "HR": W["wHR"]}
# 不算進 wOBA 分母的打席：故意四壞、犧牲觸擊、資料空白
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

BREAKING = {"SL", "CU", "CH", "FO", "FS", "SC", "SV", "KC"}  # 變化球與變速球
SWING = {"SW", "F", "FT", "H"}                               # 有出棒的投球結果

def batter_hand(pa):
    share=pa.groupby('batter_id')['b_hand'].value_counts(normalize=True).unstack(fill_value=0)
    def label(row):
        if row.get('L',0)>=0.1 and row.get('R',0)>=0.1:
            return 'S'
        return 'L' if row.get('L',0)>row.get('R',0) else 'R'
    return share.apply(label,axis=1).rename('bats').reset_index()

def pitcher_hand(pa):
    return pa.groupby('pitcher_id')['p_hand'].agg(lambda x:x.mode().iat[0]).rename('throws').reset_index()

def breaking_whiff(pa):
    rows=[]
    for bid, types, codes in pa[['batter_id','pitch_types','pitch_codes']].itertuples(index=False):
        for t, c in zip(str(types).split(','),str(codes).split(',')):
            if t in BREAKING and c in SWING:
                rows.append((bid,c=='SW'))
    df=pd.DataFrame(rows,columns=['batter_id','whiff'])
    out=df.groupby('batter_id')['whiff'].agg(swings='size',whiff_rate='mean').reset_index()
    return out

def pitch_mix(pa):
    rows=[]
    for pid,types in pa[['pitcher_id','pitch_types']].itertuples(index=False):
        for t in str(types).split(','):
            if t and t!='nan':
                rows.append((pid,t))
    df_pit=pd.DataFrame(rows,columns=['pitcher_id','pitch'])
    mix=df_pit.groupby('pitcher_id')['pitch'].value_counts(normalize=True).rename('share').reset_index()
    count=mix[mix['pitch'].isin(BREAKING)].sort_values('share',ascending=False)
    main=count.groupby('pitcher_id').head(1).rename(columns={'pitch':'main_breaking','share':'main_breaking_share'})
    return mix, main

def build_splits(pa, scale):
    pa = prepare(pa, scale)
    # 打者：對左投、右投
    bvs = summarize(pa, ["batter_id", "p_hand"]).pivot(index="batter_id", columns="p_hand",
                                                      values=["PA", "wOBA"])
    bvs.columns = [f"{a}_vs{b}" for a, b in bvs.columns]
    batters = (bvs.reset_index().merge(batter_hand(pa), on="batter_id", how="left")
               .merge(breaking_whiff(pa), on="batter_id", how="left"))
    # 投手：對左打、右打，以及第 1、2、3 輪打線
    pvs = summarize(pa, ["pitcher_id", "b_hand"]).pivot(index="pitcher_id", columns="b_hand",
                                                       values=["PA", "wOBA"])
    pvs.columns = [f"{a}_vs{b}" for a, b in pvs.columns]
    tto = summarize(pa, ["pitcher_id", "pa_round"]).pivot(index="pitcher_id", columns="pa_round",
                                                         values="wOBA")
    tto.columns = [f"wOBA_round{int(c)}" for c in tto.columns]
    _, main = pitch_mix(pa)
    pitchers = (pvs.reset_index().merge(tto.reset_index(), on="pitcher_id", how="left")
                .merge(pitcher_hand(pa), on="pitcher_id", how="left")
                .merge(main, on="pitcher_id", how="left"))
    league = {"wOBA": pa["woba_val"].mean()}
    return batters, pitchers, league
