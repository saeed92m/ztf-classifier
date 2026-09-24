"""Frozen scientific feature schema for v0.2."""
V02_FEATURES=["g_baseline_days","g_ls_best_frequency","g_ls_best_period_days","g_ls_best_power","g_ls_fap","g_ls_max_period_days","g_ls_min_period_days","g_max_mag","g_mean_mag","g_mean_magerr","g_median_mag","g_median_magerr","g_min_mag","g_n_obs","g_p05_mag","g_p25_mag","g_p75_mag","g_p95_mag","g_variability_ratio","g_weighted_mean_mag","mean_color_gr","median_color_gr","r_baseline_days","r_ls_best_frequency","r_ls_best_period_days","r_ls_best_power","r_ls_fap","r_ls_max_period_days","r_ls_min_period_days","r_max_mag","r_mean_mag","r_mean_magerr","r_median_mag","r_median_magerr","r_min_mag","r_n_obs","r_p05_mag","r_p25_mag","r_p75_mag","r_p95_mag","r_variability_ratio","r_weighted_mean_mag"]
REMOVED_V02_FEATURES=[f"{b}_{s}" for b in ("g","r") for s in ("std_mag","mad_mag","amplitude_mag","iqr_mag","p95_p05_mag","rms_mag","reduced_chi2_like","median_abs_norm_resid","phase_amplitude","phase_robust_amplitude","phase_iqr","phase_skewness","phase_min_mag_phase","phase_max_mag_phase","phase_bright_fraction")]
assert len(V02_FEATURES)==42 and len(REMOVED_V02_FEATURES)==30
def select_v02_features(frame):
    missing=[c for c in V02_FEATURES if c not in frame.columns]
    if missing: raise KeyError(f"Missing v0.2 features: {missing}")
    return frame.loc[:,V02_FEATURES].copy()
