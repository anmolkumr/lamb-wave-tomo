import numpy as np
from geometry import generate_weight_matrix
from simulation import create_test_cases
from typing import Dict

def generate_realistic_projections(
    grid_size: int = 11,
    case: str = 'central_hole',
    defect_params: Dict = {},
    noise_level: float = 0.05,
    edge_effects: bool = True,
    anisotropy_factor: float = 0.0,
    material_type: str = 'aluminum'
) -> Dict:
    """
    Generate projections with realistic experimental artifacts
    
    Based on paper Section 6 Discussion:
    - Noise from coupling variations
    - Edge reflections
    - Material anisotropy (CFRP composites)
    - Mode conversion artifacts
    
    Args:
        grid_size: N for N×N grid
        case: 'constant', 'impulse', 'central_hole', 'off_center_rect'
        defect_params: case-specific parameters
        noise_level: Gaussian noise std (0.0-0.2 typical, 0.05 = 5%)
        edge_effects: Add edge reflection artifacts
        anisotropy_factor: Material anisotropy (0.0-0.3, 0=isotropic, 0.15=CFRP)
        material_type: 'aluminum', 'cfrp', or 'steel'
    
    Returns:
        Dict with W, projections, ground_truth, and metadata
    """
    
    # Generate system
    system = generate_weight_matrix(grid_size)
    W = system['W']
    
    # Generate ground truth
    ground_truth = create_test_cases(case, grid_size, defect_params)
    
    # Compute ideal projections
    projections = W @ ground_truth
    
    print(f"[Realistic] Starting realistic simulation for {material_type}...")
    print(f"[Realistic] Base projections: min={projections.min():.3f}, max={projections.max():.3f}")
    
    # 1. ADD GAUSSIAN NOISE (coupling variations, sensor noise)
    if noise_level > 0:
        signal_std = np.std(projections)
        noise = np.random.normal(0, noise_level * signal_std, len(projections))
        projections = projections + noise
        snr_db = 20 * np.log10(1 / noise_level) if noise_level > 0 else np.inf
        print(f"[Realistic] Added {noise_level*100:.1f}% Gaussian noise (SNR: {snr_db:.1f} dB)")
    
    # 2. ADD EDGE REFLECTION ARTIFACTS
    if edge_effects:
        N = grid_size
        edge_count = 0
        for ray_idx in range(len(projections)):
            ray_weights = W[ray_idx, :]
            active_pixels = np.where(ray_weights > 0)[0]
            
            if len(active_pixels) > 0:
                rows = active_pixels // N
                cols = active_pixels % N
                
                edge_dist = np.min([
                    np.min(rows), np.min(cols),
                    N - 1 - np.max(rows), N - 1 - np.max(cols)
                ])
                
                if edge_dist <= 2:
                    edge_attenuation = 0.9 + 0.05 * np.random.randn()
                    projections[ray_idx] *= edge_attenuation
                    edge_count += 1
        
        print(f"[Realistic] Added edge reflection artifacts ({edge_count} rays affected)")
    
    # 3. ADD ANISOTROPY EFFECTS (for CFRP composites)
    if anisotropy_factor > 0:
        subset_labels = system['subset_labels']
        
        for subset_id in range(6):
            subset_mask = np.array(subset_labels) == subset_id
            direction_bias = 1.0 + anisotropy_factor * (np.random.rand() - 0.5) * 2
            projections[subset_mask] *= direction_bias
        
        print(f"[Realistic] Added material anisotropy (factor: {anisotropy_factor:.2f})")
    
    # 4. ADD MODE CONVERSION ARTIFACTS
    num_affected = int(0.1 * len(projections))
    affected_rays = np.random.choice(len(projections), num_affected, replace=False)
    mode_conversion_noise = 0.02 * np.mean(np.abs(projections)) * np.random.randn(num_affected)
    projections[affected_rays] += mode_conversion_noise
    print(f"[Realistic] Added mode conversion artifacts ({num_affected} rays)")
    
    # 5. QUANTIZATION (digitizer effects)
    bit_depth = 16
    max_val = np.max(np.abs(projections))
    if max_val > 0:
        quantized = np.round(projections / max_val * (2**bit_depth - 1)) * max_val / (2**bit_depth - 1)
        projections = quantized
        print(f"[Realistic] Applied {bit_depth}-bit quantization")
    
    print(f"[Realistic] Final projections: min={projections.min():.3f}, max={projections.max():.3f}")
    
    return {
        'W': W,
        'projections': projections,
        'ground_truth': ground_truth,
        'grid_shape': [grid_size, grid_size],
        'num_rays': len(projections),
        'num_subsets': 6,
        'realistic_params': {
            'noise_level': noise_level,
            'edge_effects': edge_effects,
            'anisotropy_factor': anisotropy_factor,
            'material_type': material_type
        },
        'ray_info': {
            'subset_labels': system['subset_labels'],
            'rays_per_subset': system['rays_per_subset']
        }
    }


# Material presets
MATERIAL_PRESETS = {
    'aluminum': {
        'noise_level': 0.05,
        'anisotropy_factor': 0.0,
        'description': 'Isotropic aluminum alloy (6061-T6)'
    },
    'cfrp': {
        'noise_level': 0.08,
        'anisotropy_factor': 0.15,
        'description': 'Carbon fiber reinforced polymer (anisotropic)'
    },
    'steel': {
        'noise_level': 0.04,
        'anisotropy_factor': 0.02,
        'description': 'Low-carbon steel (mildly anisotropic)'
    }
}


if __name__ == '__main__':
    print("="*60)
    print("Testing Realistic Projection Generation")
    print("="*60)
    
    for material, params in MATERIAL_PRESETS.items():
        print(f"\n{material.upper()}: {params['description']}")
        data = generate_realistic_projections(
            grid_size=11,
            case='central_hole',
            defect_params={'shape': 'rectangle', 'width': 3, 'height': 3},
            noise_level=params['noise_level'],
            edge_effects=True,
            anisotropy_factor=params['anisotropy_factor'],
            material_type=material
        )
    
    print("\n✅ Realistic simulation tests complete!")
