"""Cross-band photometric features."""
import numpy as np
def basic_cross_band_features(g_lc,r_lc):
    g=g_lc["mag"].to_numpy(dtype=float); r=r_lc["mag"].to_numpy(dtype=float)
    g=g[np.isfinite(g)]; r=r[np.isfinite(r)]
    if len(g)==0 or len(r)==0: raise ValueError("Both g and r must contain valid magnitudes.")
    return {"mean_color_gr":np.mean(g)-np.mean(r),"median_color_gr":np.median(g)-np.median(r),"g_variability_ratio":np.std(g,ddof=1)/np.mean(g),"r_variability_ratio":np.std(r,ddof=1)/np.mean(r)}
