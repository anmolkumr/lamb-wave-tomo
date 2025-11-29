import numpy as np
from geometry import generate_weight_matrix
from typing import Dict

def generate_system(grid_size: int = 11) -> Dict:
    """
    Generate complete forward system (weight matrix + metadata)
    
    Returns geometry system as described in paper
    """
    return generate_weight_matrix(grid_size)


def create_test_cases(
    case: str,
    grid_size: int = 11,
    params: Dict = {}
) -> np.ndarray:
    """
    Generate synthetic test fields matching paper's validation cases
    
    Cases:
    1. constant: uniform field (value=1.0)
    2. impulse: single pixel defect
    3. central_hole: circular/rectangular hole in center
    4. off_center_rect: off-diagonal rectangular defect
    
    Args:
        case: test case name
        grid_size: N for N×N grid
        params: case-specific parameters
    
    Returns:
        field: (N²,) flattened array
    """
    N = grid_size
    field_2d = np.ones((N, N))  # Default: constant field
    
    if case == 'constant':
        # Already initialized to 1.0
        pass
    
    elif case == 'impulse':
        # Single pixel at specified location (default: center)
        row = params.get('row', N // 2)
        col = params.get('col', N // 2)
        value = params.get('value', 0.0)  # Defect = lower value
        field_2d[row, col] = value
    
    elif case == 'central_hole':
        # Circular or rectangular hole in center
        shape = params.get('shape', 'circle')
        radius = params.get('radius', N // 4)
        value = params.get('value', 0.0)
        
        center_row = N // 2
        center_col = N // 2
        
        if shape == 'circle':
            for i in range(N):
                for j in range(N):
                    dist = np.sqrt((i - center_row)**2 + (j - center_col)**2)
                    if dist <= radius:
                        field_2d[i, j] = value
        
        elif shape == 'rectangle':
            width = params.get('width', N // 3)
            height = params.get('height', N // 3)
            
            row_start = center_row - height // 2
            row_end = center_row + height // 2
            col_start = center_col - width // 2
            col_end = center_col + width // 2
            
            field_2d[row_start:row_end, col_start:col_end] = value
    
    elif case == 'off_center_rect':
        # Off-diagonal rectangular defect (as in paper Fig 11c)
        row_start = params.get('row_start', N // 4)
        row_end = params.get('row_end', 3 * N // 4)
        col_start = params.get('col_start', N // 4)
        col_end = params.get('col_end', 3 * N // 4)
        value = params.get('value', 0.0)
        
        field_2d[row_start:row_end, col_start:col_end] = value
    
    else:
        raise ValueError(f"Unknown test case: {case}")
    
    # Flatten to 1D array
    return field_2d.flatten()


def add_noise(projections: np.ndarray, snr_db: float = 20) -> np.ndarray:
    """Add Gaussian noise to projections"""
    signal_power = np.mean(projections**2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = np.random.normal(0, np.sqrt(noise_power), len(projections))
    return projections + noise
