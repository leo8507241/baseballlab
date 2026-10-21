
def iso(double,triple,homerun,ab):
    return (double+2*triple+3*homerun)/ab

def babip (h,hr,ab,so,sf):
    return( h-hr)/(ab-so-hr+sf)

def pythag( rs , ra ,exp=1.83):
    return (rs**exp)/(rs**exp+ra**exp)





W={'ubb':0.776,'wHBP':0.795,'w1B':0.950,'w2B':1.322,'w3B':1.800,'wHR':2.464}
def woba(hbp,h,double,triple,hr,ab,bb,ibb,sf):
    w=W
    num=(w['ubb']*(bb-ibb)+w['wHBP']*hbp+w['w1B']*(h-double-triple-hr)+w['w2B']*double+w['w3B']*triple+w['wHR']*hr)
    den=ab+bb-ibb+sf+hbp
    return num/den

def woba_scale(lg):
    obp=(lg['H']+lg['BB']+lg['HBP'])/(lg['AB']+lg['BB']+lg['HBP']+lg['SF'])
    woba_real=woba(lg['HBP'],lg['H'],lg['Double'],lg['Triple'],lg['HR'],lg['AB'],lg['BB'],lg['IBB'],lg['SF'])
    return obp/woba_real

def fip_const(lg_er,lg_ip,lg_hr,lg_bb,lg_k):
    lg_era=(lg_er*9)/(lg_ip/3)
    return lg_era-((13*lg_hr+3*(lg_bb)-2*lg_k)/(lg_ip/3))

def fip(hr,k,bb,ip,const=2.869):
    return (13*hr+3*bb-2*k)/(ip/3)+const

