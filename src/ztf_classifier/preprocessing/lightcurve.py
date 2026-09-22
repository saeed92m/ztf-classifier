"""Light-curve preparation utilities."""
import numpy as np

def prepare_band_lightcurve(internal_lc,fid):
    band=internal_lc[internal_lc["fid"]==fid].copy()
    if len(band)==0:return band
    valid=(np.isfinite(band["mjd"].to_numpy(dtype=float))&np.isfinite(band["mag"].to_numpy(dtype=float))&np.isfinite(band["magerr"].to_numpy(dtype=float))&(band["magerr"].to_numpy(dtype=float)>0))
    return band.loc[valid].sort_values("mjd").reset_index(drop=True)
