const API_BASE = 'http://localhost:5000/api';

export async function generateSimulation(config) {
  const response = await fetch(`${API_BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Simulation failed');
  }

  return response.json();
}

export async function runReconstruction(data) {
  const response = await fetch(`${API_BASE}/reconstruct`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Reconstruction failed');
  }

  return response.json();
}
