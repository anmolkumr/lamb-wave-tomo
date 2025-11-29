from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from mart3 import MART3Reconstructor
from simulation import generate_system, create_test_cases
from metrics import compute_metrics
import json

app = Flask(__name__)
CORS(app)

@app.route('/api/simulate_realistic', methods=['POST'])
def simulate_realistic():
    """
    Generate realistic projection data with experimental artifacts
    
    Input JSON:
    {
        "grid_size": 11,
        "case": "central_hole",
        "defect_params": {...},
        "noise_level": 0.05,
        "edge_effects": true,
        "anisotropy_factor": 0.0,
        "material_type": "aluminum"
    }
    """
    try:
        data = request.json
        grid_size = data.get('grid_size', 11)
        case = data.get('case', 'central_hole')
        defect_params = data.get('defect_params', {})
        
        # Realistic parameters
        noise_level = float(data.get('noise_level', 0.05))
        edge_effects = bool(data.get('edge_effects', True))
        anisotropy = float(data.get('anisotropy_factor', 0.0))
        material_type = data.get('material_type', 'aluminum')
        
        print(f"[Simulate Realistic] Material: {material_type}, Noise: {noise_level*100:.1f}%, Anisotropy: {anisotropy:.2f}")
        
        from realistic_simulation import generate_realistic_projections
        
        result = generate_realistic_projections(
            grid_size=grid_size,
            case=case,
            defect_params=defect_params,
            noise_level=noise_level,
            edge_effects=edge_effects,
            anisotropy_factor=anisotropy,
            material_type=material_type
        )
        
       
        response_data = {
            'weight_matrix': result['W'].tolist(),
            'projections': result['projections'].tolist(),
            'ground_truth': result['ground_truth'].tolist(),
            'grid_shape': result['grid_shape'],
            'num_rays': int(result['num_rays']),
            'num_subsets': 6,
            'realistic_params': result['realistic_params'],
            'ray_info': {
                'subset_labels': [int(x) for x in result['ray_info']['subset_labels']],
                'rays_per_subset': int(result['ray_info']['rays_per_subset'])
            }
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        import traceback
        print(f"[ERROR] Realistic simulation failed: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reconstruct', methods=['POST'])
def reconstruct():
    """Reconstruct 2D defect map using MART3"""
    try:
        data = request.json
        
        # Explicit conversion with error checking
        try:
            W = np.array(data['weight_matrix'], dtype=np.float64)
            projections = np.array(data['projections'], dtype=np.float64)
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': f'Failed to convert arrays: {str(e)}. Check JSON format.'
            }), 400
        
        # Validate array shapes
        if W.ndim != 2:
            return jsonify({
                'error': f'Weight matrix must be 2D, got shape {W.shape}'
            }), 400
        
        if projections.ndim != 1:
            return jsonify({
                'error': f'Projections must be 1D, got shape {projections.shape}'
            }), 400
        
        k = float(data.get('k', 0.01))
        max_iter = int(data.get('max_iterations', 100))
        rms_tol = float(data.get('rms_tolerance', 1e-4))
        grid_shape = data.get('grid_shape', [11, 11])
        
        # Validate inputs
        M, N = W.shape
        if len(projections) != M:
            return jsonify({
                'error': f'Projection length ({len(projections)}) must match weight matrix rows ({M})'
            }), 400
        
        if N != grid_shape[0] * grid_shape[1]:
            return jsonify({
                'error': f'Grid shape {grid_shape} must match weight matrix columns ({N})'
            }), 400
        
        print(f" Received: W shape={W.shape}, dtype={W.dtype}")
        print(f"Projections shape={projections.shape}, dtype={projections.dtype}")
        print(f"k={k}, max_iterations={max_iter}")
        
        # Run MART3 reconstruction
        reconstructor = MART3Reconstructor(
            W=W,
            projections=projections,
            k=k,
            max_iterations=max_iter,
            rms_tolerance=rms_tol,
            apply_non_negativity=True
        )
        
        result = reconstructor.reconstruct()
        
        # Compute error metrics if ground truth provided
        metrics = {}
        if 'ground_truth' in data and data['ground_truth'] is not None:
            gt = np.array(data['ground_truth'], dtype=np.float64)
            metrics = compute_metrics(gt, result['field'])
        
        return jsonify({
            'reconstructed': result['field'].tolist(),
            'iterations': result['iterations'],
            'metrics': metrics,
            'convergence': result['convergence_history'],
            'grid_shape': grid_shape,
            'stopped_reason': result['stopped_reason']
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Reconstruction failed:\n{error_trace}")
        return jsonify({'error': f'{str(e)}', 'trace': error_trace}), 500




@app.route('/api/simulate', methods=['POST'])
def simulate():
    """Generate synthetic projection data"""
    try:
        data = request.json
        grid_size = data.get('grid_size', 11)
        case = data.get('case', 'constant')
        defect_params = data.get('defect_params', {})
        
        print(f"[Simulate] Generating {grid_size}×{grid_size} {case} case...")
        
        # Generate weight matrix and ground truth
        system = generate_system(grid_size)
        ground_truth = create_test_cases(case, grid_size, defect_params)
        
        # Ensure proper numpy arrays with explicit dtype
        W = np.asarray(system['W'], dtype=np.float64)
        ground_truth = np.asarray(ground_truth, dtype=np.float64).flatten()
        
        # Compute projections (forward problem)
        projections = W @ ground_truth
        
        # Add noise 
        noise_level = data.get('noise_level', 0.0)
        if noise_level > 0:
            noise = np.random.normal(0, noise_level * np.mean(np.abs(projections)), len(projections))
            projections = projections + noise
        
        print(f"[Simulate] Generated: W shape={W.shape}, projections shape={projections.shape}")
        print(f"[Simulate] W dtype={W.dtype}, projections dtype={projections.dtype}")
        
        # FIX: Proper conversion to JSON-serializable format
        # Use .tolist() which converts numpy arrays to native Python lists
        response_data = {
            'weight_matrix': W.tolist(),  # Converts to [[float, float, ...], ...]
            'projections': projections.tolist(),  # Converts to [float, float, ...]
            'ground_truth': ground_truth.tolist(),  # Converts to [float, float, ...]
            'grid_shape': [int(grid_size), int(grid_size)],
            'num_rays': int(W.shape[0]),
            'num_subsets': 6,
            'ray_info': {
                'subset_labels': [int(x) for x in system['subset_labels']],
                'rays_per_subset': int(system['rays_per_subset'])
            }
        }
        
        # Debug: Check first element types
        print(f"[Simulate] weight_matrix[0][0] type: {type(response_data['weight_matrix'][0][0])}")
        print(f"[Simulate] projections[0] type: {type(response_data['projections'][0])}")
        
        return jsonify(response_data)
    
    except Exception as e:
        import traceback
        print(f"[ERROR] Simulation failed: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Lamb-Wave MART3 Reconstruction'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
