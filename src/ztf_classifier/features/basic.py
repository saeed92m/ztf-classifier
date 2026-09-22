"""Basic per-band statistical features."""
import numpy as np

def basic_band_features(lc,band):
    x=lc["mag"].to_numpy(dtype=float); e=lc["magerr"].to_numpy(dtype=float); t=lc["mjd"].to_numpy(dtype=float)
    valid=np.isfinite(x)&np.isfinite(e)&np.isfinite(t)&(e>0); x=x[valid]; e=e[valid]; t=t[valid]
    if len(x)==0: raise ValueError(f"No valid observations for band {band}")
    median=np.median(x); mean=np.mean(x); weights=1.0/np.square(e); weighted_mean=np.sum(weights*x)/np.sum(weights)
    q05,q25,q75,q95=np.percentile(x,[5,25,75,95]); mad=np.median(np.abs(x-median)); residuals=x-weighted_mean
    rms=np.sqrt(np.mean(residuals**2)); reduced_chi2_like=np.sum(np.square(residuals/e))/len(x); median_abs_norm_resid=np.median(np.abs(residuals/e))
    return {f"{band}_n_obs":len(x),f"{band}_baseline_days":np.max(t)-np.min(t),f"{band}_mean_mag":mean,f"{band}_median_mag":median,f"{band}_weighted_mean_mag":weighted_mean,f"{band}_std_mag":np.std(x,ddof=1),f"{band}_mad_mag":mad,f"{band}_min_mag":np.min(x),f"{band}_max_mag":np.max(x),f"{band}_amplitude_mag":np.max(x)-np.min(x),f"{band}_p05_mag":q05,f"{band}_p25_mag":q25,f"{band}_p75_mag":q75,f"{band}_p95_mag":q95,f"{band}_iqr_mag":q75-q25,f"{band}_p95_p05_mag":q95-q05,f"{band}_mean_magerr":np.mean(e),f"{band}_median_magerr":np.median(e),f"{band}_rms_mag":rms,f"{band}_reduced_chi2_like":reduced_chi2_like,f"{band}_median_abs_norm_resid":median_abs_norm_resid}
