import numpy as np
from typing import Dict, Optional, List

class MART3Reconstructor:
    """
    MART3 (Multiplicative Algebraic Reconstruction Technique - Version 3)
    
    Paper Implementation:
    f_j^{new} = f_j^{old} * ∏_{i ∈ Nc_j} (φ_i / φ̃_i)^{k*w_{ij}}
    
    where:
    - f_j: field value at pixel j
    - φ_i: measured projection for ray i
    - φ̃_i: computed projection for ray i
    - w_{ij}: weight (intersection length) of ray i with pixel j
    - k: relaxation parameter (0.01-0.05 typical)
    - Nc_j: set of rays passing through pixel j
    """
    
    def __init__(
        self,
        W: np.ndarray,
        projections: np.ndarray,
        k: float = 0.01,
        max_iterations: int = 100,
        rms_tolerance: float = 1e-4,
        apply_non_negativity: bool = True,
        plateau_patience: int = 5
    ):
        # Convert to numpy arrays with explicit dtype
        self.W = np.asarray(W, dtype=np.float64)
        self.projections = np.asarray(projections, dtype=np.float64)
        self.k = float(k)
        self.max_iterations = int(max_iterations)
        self.rms_tolerance = float(rms_tolerance)
        self.apply_non_negativity = apply_non_negativity
        self.plateau_patience = int(plateau_patience)
        
        self.M, self.N = self.W.shape
        
        # Validate inputs
        assert len(self.projections) == self.M, \
            f"Projection length ({len(self.projections)}) must match weight matrix rows ({self.M})"
        assert 0 < k <= 0.1, \
            f"Relaxation parameter k ({k}) should be in (0, 0.1]"
        
        print(f"[MART3] Initialized: {self.M} rays, {self.N} pixels, k={self.k}")
        
        # Precompute ray-to-pixel mapping for efficiency
        self._build_ray_pixel_map()
    
    def _build_ray_pixel_map(self):
        """Precompute which rays pass through each pixel"""
        self.pixel_to_rays = {}
        for j in range(self.N):
            # Find all rays that intersect pixel j
            ray_indices = np.where(self.W[:, j] > 0)[0]
            self.pixel_to_rays[j] = ray_indices
    
    def _compute_projections(self, field: np.ndarray) -> np.ndarray:
        """Forward problem: compute projections from field"""
        field = np.asarray(field, dtype=np.float64)
        return self.W @ field
    
    def _compute_rms_error(self, computed_proj: np.ndarray) -> float:
        """Compute RMS error between measured and computed projections"""
        diff = self.projections - computed_proj
        return float(np.sqrt(np.mean(diff**2)))
    
    def _apply_mart3_update(self, field: np.ndarray) -> np.ndarray:
        """
        Single MART3 iteration
        
        For each pixel j:
        1. Find all rays passing through it (Nc_j)
        2. Compute correction term: ∏_{i ∈ Nc_j} (φ_i / φ̃_i)^{k*w_{ij}}
        3. Apply multiplicatively: f_j^{new} = f_j^{old} * correction
        """
        field_new = field.copy()
        
        # Compute current projections
        computed_proj = self._compute_projections(field)
        
        # Avoid division by zero
        computed_proj = np.maximum(computed_proj, 1e-10)
        
        # Update each pixel
        for j in range(self.N):
            ray_indices = self.pixel_to_rays[j]
            
            if len(ray_indices) == 0:
                continue  # No rays pass through this pixel
            
            # CRITICAL FIX: Compute correction factor (product over all rays)
            # Must ensure correction remains a scalar float
            correction = 1.0
            for i in ray_indices:
                w_ij = float(self.W[i, j])  # Ensure scalar
                ratio = float(self.projections[i]) / float(computed_proj[i])  # Ensure scalar
                
                # MART3 correction: (φ_i / φ̃_i)^{k*w_{ij}}
                # CRITICAL: Use float() to ensure scalar result
                exponent = self.k * w_ij
                correction_factor = ratio ** exponent
                
                # Ensure it's a scalar
                if isinstance(correction_factor, np.ndarray):
                    correction_factor = float(correction_factor.item())
                
                correction *= correction_factor
            
            # CRITICAL FIX: Ensure correction is a scalar before assignment
            if isinstance(correction, np.ndarray):
                correction = float(correction.item())
            
            # Apply multiplicative update
            field_new[j] = float(field[j]) * correction
            
            # Non-negativity constraint (as per paper)
            if self.apply_non_negativity:
                field_new[j] = max(field_new[j], 0.0)
        
        return field_new
    
    def reconstruct(self) -> Dict:
        """
        Run MART3 reconstruction with early stopping
        
        Returns:
        {
            'field': reconstructed field (N,),
            'iterations': number of iterations,
            'convergence_history': RMS error per iteration,
            'stopped_reason': 'max_iterations' | 'tolerance' | 'plateau'
        }
        """
        # Initialize field (uniform = 1.0 as per paper)
        field = np.ones(self.N, dtype=np.float64)
        
        convergence_history = []
        best_rms = float('inf')
        plateau_count = 0
        
        print(f"[MART3] Starting reconstruction...")
        
        for iteration in range(self.max_iterations):
            # Apply MART3 update
            field = self._apply_mart3_update(field)
            
            # Compute RMS error
            computed_proj = self._compute_projections(field)
            rms = self._compute_rms_error(computed_proj)
            convergence_history.append(float(rms))
            
            if iteration % 10 == 0 or iteration < 5:
                print(f"[MART3] Iteration {iteration+1}: RMS = {rms:.6f}")
            
            # Check for improvement
            if rms < best_rms - self.rms_tolerance:
                best_rms = rms
                plateau_count = 0
            else:
                plateau_count += 1
            
            # Early stopping on RMS plateau
            if plateau_count >= self.plateau_patience:
                print(f"[MART3] Stopped: RMS plateau detected ({plateau_count} iterations without improvement)")
                return {
                    'field': field,
                    'iterations': iteration + 1,
                    'convergence_history': convergence_history,
                    'stopped_reason': 'plateau',
                    'final_rms': float(rms)
                }
            
            # Early stopping on tolerance
            if rms < self.rms_tolerance:
                print(f"[MART3] Stopped: RMS tolerance reached ({rms:.6f} < {self.rms_tolerance})")
                return {
                    'field': field,
                    'iterations': iteration + 1,
                    'convergence_history': convergence_history,
                    'stopped_reason': 'tolerance',
                    'final_rms': float(rms)
                }
        
        print(f"[MART3] Stopped: Max iterations reached ({self.max_iterations})")
        return {
            'field': field,
            'iterations': self.max_iterations,
            'convergence_history': convergence_history,
            'stopped_reason': 'max_iterations',
            'final_rms': float(convergence_history[-1])
        }
