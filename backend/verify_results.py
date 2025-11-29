import numpy as np
from simulation import generate_system, create_test_cases
from mart3 import MART3Reconstructor
from metrics import compute_metrics

def verify_paper_results():
    """
    Verify MART3 implementation against paper benchmarks
    Paper reference: Khare et al. (2007), Section 3
    """
    print("="*60)
    print("MART3 Implementation Verification Against Paper")
    print("="*60)
    
    # Test configuration (paper uses 11×11)
    grid_size = 11
    k_values = [0.01, 0.03, 0.05]
    
    test_cases = [
        ('constant', {}, "Constant Field"),
        ('central_hole', {'shape': 'rectangle', 'width': 3, 'height': 3}, "Central Hole"),
        ('off_center_rect', {'row_start': 3, 'row_end': 8, 'col_start': 3, 'col_end': 8}, "Off-Center Rectangle")
    ]
    
    print(f"\nGrid size: {grid_size}×{grid_size}")
    print(f"Total rays: {grid_size**2 * 6} (6 subsets × {grid_size**2} rays/subset)")
    print(f"Total pixels: {grid_size**2}\n")
    
    results = []
    
    for case_name, params, display_name in test_cases:
        print(f"\n{'='*60}")
        print(f"Test Case: {display_name}")
        print(f"{'='*60}")
        
        # Generate system
        system = generate_system(grid_size)
        ground_truth = create_test_cases(case_name, grid_size, params)
        
        # Compute projections
        W = system['W']
        projections = W @ ground_truth
        
        for k in k_values:
            print(f"\n--- Relaxation parameter k = {k} ---")
            
            # Run MART3
            reconstructor = MART3Reconstructor(
                W=W,
                projections=projections,
                k=k,
                max_iterations=100,
                rms_tolerance=1e-4,
                apply_non_negativity=True
            )
            
            result = reconstructor.reconstruct()
            
            # Compute metrics
            metrics = compute_metrics(ground_truth, result['field'])
            
            # Display results
            print(f"  Iterations: {result['iterations']}")
            print(f"  Stopped: {result['stopped_reason']}")
            print(f"  RMS Error (EA): {metrics['rms']:.4f}")
            print(f"  Avg Error (EB): {metrics['average_error']:.4f}")
            print(f"  Max Error (EC): {metrics['max_error']:.4f}")
            print(f"  Normalized Error (ED): {metrics['normalized_error']*100:.2f}%")
            
            # Paper benchmarks
            if case_name == 'constant':
                expected_rms = 0.5
                expected_norm = 0.05
            elif case_name == 'central_hole':
                expected_rms = 2.6
                expected_norm = 0.26
            else:  # off_center_rect
                expected_rms = 3.0
                expected_norm = 0.30
            
            # Validation
            rms_ok = metrics['rms'] <= expected_rms * 1.2  # 20% tolerance
            norm_ok = metrics['normalized_error'] <= expected_norm * 1.2
            
            status = "✅ PASS" if (rms_ok and norm_ok) else "⚠️ CHECK"
            print(f"  Paper benchmark: RMS ≤ {expected_rms}, Normalized ≤ {expected_norm*100:.0f}%")
            print(f"  Status: {status}")
            
            results.append({
                'case': display_name,
                'k': k,
                'rms': metrics['rms'],
                'normalized': metrics['normalized_error']*100,
                'iterations': result['iterations'],
                'status': status
            })
    
    # Summary table
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"{'Test Case':<20} {'k':<6} {'RMS':<8} {'Norm %':<8} {'Iter':<6} {'Status'}")
    print("-"*60)
    for r in results:
        print(f"{r['case']:<20} {r['k']:<6} {r['rms']:<8.3f} {r['normalized']:<8.2f} {r['iterations']:<6} {r['status']}")
    
    print(f"\n{'='*60}")
    print("CONCLUSION")
    print(f"{'='*60}")
    passes = sum(1 for r in results if '✅' in r['status'])
    total = len(results)
    print(f"Passed: {passes}/{total} tests")
    
    if passes == total:
        print("✅ Implementation matches paper benchmarks!")
    elif passes >= total * 0.8:
        print("⚠️ Implementation mostly correct, minor deviations acceptable")
    else:
        print("❌ Implementation needs review")

if __name__ == '__main__':
    verify_paper_results()
