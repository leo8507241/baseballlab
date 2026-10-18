
def iso(double,triple,homerun,ab):
    return (double+2*triple+3*homerun)/ab

def babip (h,hr,ab,so,sf):
    return( h-hr)/(ab-so-hr+sf)

def pythag( rs , ra ,exp=1.83):
    return (rs**exp)/(rs**exp+ra**exp)
