import numpy as np
import json

# Simulate what happens
W = np.random.rand(5, 3).astype(np.float64)
print("Original W:")
print(f"  Shape: {W.shape}")
print(f"  Dtype: {W.dtype}")
print(f"  Type: {type(W)}")

# Convert to JSON (what /simulate does)
W_list = W.tolist()
print("\nAfter .tolist():")
print(f"  Type: {type(W_list)}")
print(f"  Element type: {type(W_list[0][0])}")

# Simulate JSON round-trip
json_str = json.dumps({'weight_matrix': W_list})
data = json.loads(json_str)

# Convert back (what /reconstruct does)
W_recovered = np.array(data['weight_matrix'], dtype=np.float64)
print("\nAfter JSON round-trip:")
print(f"  Shape: {W_recovered.shape}")
print(f"  Dtype: {W_recovered.dtype}")
print(f"  Match: {np.allclose(W, W_recovered)}")
