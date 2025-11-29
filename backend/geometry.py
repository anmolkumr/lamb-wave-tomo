import numpy as np
from typing import Dict, Tuple, List

def generate_weight_matrix(grid_size: int) -> Dict:
    """
    Generate weight matrix for modified cross-hole geometry
    """
    N = grid_size
    num_pixels = N * N
    rays_per_subset = N * N
    num_subsets = 6
    total_rays = rays_per_subset * num_subsets
    
    # FIX: Initialize with explicit dtype
    W = np.zeros((total_rays, num_pixels), dtype=np.float64)
    
    # Define sensor positions along edges
    sensor_coords = _get_sensor_positions(N)
    
    # Define 6 subsets (transmitter → receiver pairs)
    subsets = [
        ('left', 'right'),
        ('top', 'bottom'),
        ('right', 'top'),
        ('right', 'bottom'),
        ('left', 'top'),
        ('left', 'bottom')
    ]
    
    ray_idx = 0
    subset_labels = []
    
    print(f"[Geometry] Generating weight matrix for {N}×{N} grid...")
    
    for subset_id, (tx_edge, rx_edge) in enumerate(subsets):
        tx_sensors = sensor_coords[tx_edge]
        rx_sensors = sensor_coords[rx_edge]
        
        # Generate all TX-RX pairs for this subset
        for tx_pos in tx_sensors:
            for rx_pos in rx_sensors:
                # Compute ray weights
                weights = _compute_ray_weights(tx_pos, rx_pos, N)
                
                # FIX: Ensure weights is a 1D numpy array with correct dtype
                weights = np.asarray(weights, dtype=np.float64).flatten()
                
                if weights.shape[0] != num_pixels:
                    raise ValueError(f"Weight array has wrong size: {weights.shape[0]} != {num_pixels}")
                
                W[ray_idx, :] = weights
                subset_labels.append(subset_id)
                ray_idx += 1
        
        print(f"[Geometry] Subset {subset_id} ({tx_edge}→{rx_edge}): {len(tx_sensors)*len(rx_sensors)} rays")
    
    print(f"[Geometry] Generated {total_rays} rays for {num_pixels} pixels")
    
    return {
        'W': W,
        'subset_labels': subset_labels,
        'rays_per_subset': rays_per_subset,
        'num_subsets': num_subsets,
        'sensor_positions': sensor_coords
    }


def _get_sensor_positions(N: int) -> Dict[str, List[Tuple[float, float]]]:
    """Get sensor coordinates for modified cross-hole geometry"""
    positions = np.linspace(0.5, N - 0.5, N)
    
    return {
        'left': [(0.0, float(y)) for y in positions],
        'right': [(float(N), float(y)) for y in positions],
        'top': [(float(x), float(N)) for x in positions],
        'bottom': [(float(x), 0.0) for x in positions]
    }


def _compute_ray_weights(
    tx: Tuple[float, float],
    rx: Tuple[float, float],
    grid_size: int
) -> np.ndarray:
    """
    Compute intersection lengths (weights) of straight ray with all pixels
    """
    N = grid_size
    
    # FIX: Initialize with explicit dtype and shape
    weights = np.zeros(N * N, dtype=np.float64)
    
    # Extract coordinates
    tx_x, tx_y = float(tx[0]), float(tx[1])
    rx_x, rx_y = float(rx[0]), float(rx[1])
    
    # Ray direction
    dx = rx_x - tx_x
    dy = rx_y - tx_y
    ray_length = np.sqrt(dx**2 + dy**2)
    
    if ray_length < 1e-10:
        return weights  # Degenerate ray
    
    # Normalize direction
    dx /= ray_length
    dy /= ray_length
    
    # Trace ray through grid
    num_steps = max(int(ray_length * N * 3), 100)
    step_size = ray_length / num_steps
    
    for step in range(num_steps):
        t = step * step_size
        x = tx_x + t * dx
        y = tx_y + t * dy
        
        # Get pixel indices
        i = int(y)  # Row
        j = int(x)  # Column
        
        # Check bounds
        if 0 <= i < N and 0 <= j < N:
            pixel_idx = i * N + j
            # FIX: Direct float accumulation (not array)
            weights[pixel_idx] += step_size
    
    return weights


def visualize_geometry(grid_size: int = 11):
    """Helper to visualize sensor placement"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not installed. Skipping visualization.")
        return
    
    sensor_coords = _get_sensor_positions(grid_size)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Draw grid
    for i in range(grid_size + 1):
        ax.axhline(i, color='gray', linewidth=0.5, alpha=0.3)
        ax.axvline(i, color='gray', linewidth=0.5, alpha=0.3)
    
    # Draw sensors
    colors = {'left': 'red', 'right': 'blue', 'top': 'green', 'bottom': 'orange'}
    for edge, positions in sensor_coords.items():
        xs, ys = zip(*positions)
        ax.scatter(xs, ys, c=colors[edge], s=100, marker='o', label=edge, zorder=5)
    
    # Draw sample rays
    for tx in sensor_coords['left'][:3]:
        for rx in sensor_coords['right'][:3]:
            ax.plot([tx[0], rx[0]], [tx[1], rx[1]], 'k-', alpha=0.2, linewidth=0.5)
    
    ax.set_xlim(-0.5, grid_size + 0.5)
    ax.set_ylim(-0.5, grid_size + 0.5)
    ax.set_aspect('equal')
    ax.legend()
    ax.set_title(f'Modified Cross-Hole Geometry ({grid_size}×{grid_size})')
    plt.tight_layout()
    plt.savefig('geometry_visualization.png', dpi=150)
    print("Saved geometry_visualization.png")
