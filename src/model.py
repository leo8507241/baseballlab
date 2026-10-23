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
