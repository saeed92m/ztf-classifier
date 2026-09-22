"""Lomb-Scargle periodicity features."""
import numpy as np
from astropy.timeseries import LombScargle
def lomb_scargle_features(lc,band,min_period=0.05,samples_per_peak=5):
    t=lc["mjd"].to_numpy(dtype=float); y=lc["mag"].to_numpy(dtype=float); dy=lc["magerr"].to_numpy(dtype=float)
    valid=np.isfinite(t)&np.isfinite(y)&np.isfinite(dy)&(dy>0); t=t[valid]; y=y[valid]; dy=dy[valid]
    if len(t)<10: raise ValueError(f"Not enough observations for Lomb–Scargle: {band}")
    baseline=np.max(t)-np.min(t); max_period=baseline/2.0
    if max_period<=min_period: raise ValueError(f"Invalid period range for band {band}")
    frequency,power=LombScargle(t,y,dy).autopower(minimum_frequency=1.0/max_period,maximum_frequency=1.0/min_period,samples_per_peak=samples_per_peak)
    best_idx=np.argmax(power); best_frequency=frequency[best_idx]; best_power=power[best_idx]; best_period=1.0/best_frequency
    ls=LombScargle(t,y,dy)
    try: fap=ls.false_alarm_probability(best_power)
    except Exception: fap=np.nan
    return {f"{band}_ls_best_period_days":best_period,f"{band}_ls_best_frequency":best_frequency,f"{band}_ls_best_power":best_power,f"{band}_ls_fap":fap,f"{band}_ls_min_period_days":min_period,f"{band}_ls_max_period_days":max_period}
