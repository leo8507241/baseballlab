import numpy as np
from src import metrics

def log5(pa,pb):
    return (pa-pa*pb)/(pa+pb-2*pa*pb)
def game_prob(pa,pb,a_is_home,hfa=0.023):
    p=log5(pa,pb)+(hfa if a_is_home else -hfa)
    return min(max(p,0.05),0.95)

def simulate_series(pa,pb,home_pattern,n=10000,hfa=0.023,seed=2026,need=4):
    rng=np.random.default_rng(seed)
    prob=[game_prob(pa,pb,h,hfa) for h in home_pattern]
    a_title=0
    results={}
    for _ in range(n):
        wa=wb=0
        for p in prob:
            if rng.random()< p:
                wa+=1
            else:
                wb+=1
            if wa==need or wb==need:
                break
        a_title+=1 if wa==need else 0
        key=f'{wa}-{wb}'
        results[key]=results.get(key,0)+1
    return a_title/n, results, prob

def league_context(teams,pitchers,lg_woba):
    ip=pitchers['IP'].sum()
    bip=pitchers['BF'].sum()-pitchers['SO'].sum()-pitchers['BB'].sum()-pitchers['HR'].sum()
    return {
        'R_per_G':teams['RS'].sum()/teams['G'].sum(),
        'wOBA':lg_woba,
        'FIP':(pitchers['FIP_calc']*pitchers['IP']).sum()/ip,
        'DER':1-(pitchers['H']-pitchers['HR']).sum()/bip
    }

def team_pitching(pitchers):
    rows=[]
    for abbr, g in pitchers.groupby('abbr'):
        pen=g[g['role']=='後援']
        bip=g['BF'].sum()-g['SO'].sum()-g['BB'].sum()-g['HR'].sum()
        rows.append({
            'abbr':abbr,
            'bullpen_fip':(pen['FIP_calc']*pen['IP']).sum()/pen['IP'].sum(),
            'DER':1-(g['H'].sum()-g['HR'].sum())/bip
        })
    return rows
def expected_runs(woba_vs_sp, woba_all, sp_fip, bullpen_fip, opp_der, ctx,
                  sp_innings=6, home=False):
    sp_part=sp_innings/9*(woba_vs_sp/ctx['wOBA'])**2*(sp_fip/ctx['FIP'])
    bp_part=(9-sp_innings)/9*(woba_all/ctx['wOBA'])**2*(bullpen_fip/ctx['FIP'])
    defense=1-(opp_der-ctx['DER'])*4
    park=1.023 if home else 0.977
    return ctx["R_per_G"] * (sp_part + bp_part) * defense * park
def win_prob_from_runs(ra, rb, exp=1.83):
    return metrics.pythag(ra, rb, exp)
