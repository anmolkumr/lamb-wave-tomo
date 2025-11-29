import numpy as np
from typing import Dict

def compute_metrics(ground_truth: np.ndarray, reconstructed: np.ndarray) -> Dict[str, float]:
    """
    Compute error metrics as defined in paper
    
    EA (RMS error):
        √(Σ(f_orig - f_recon)² / N)
    
    EB (Average error):
        Σ|f_orig - f_recon| / N
    
    EC (Max absolute error):
        MAX|f_orig - f_recon|
    
    ED (Normalized absolute error):
        Σ|f_orig - f_recon| / Σ|f_orig|
    """
    gt = np.array(ground_truth).flatten()
    recon = np.array(reconstructed).flatten()
    
    diff = gt - recon
    abs_diff = np.abs(diff)
    
    rms = np.sqrt(np.mean(diff**2))
    average_error = np.mean(abs_diff)
    max_error = np.max(abs_diff)
    normalized_error = np.sum(abs_diff) / np.sum(np.abs(gt))
    
    return {
        'rms': float(rms),
        'average_error': float(average_error),
        'max_error': float(max_error),
        'normalized_error': float(normalized_error)
    }
