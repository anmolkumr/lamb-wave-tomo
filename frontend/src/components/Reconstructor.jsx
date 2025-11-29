import React, { useState } from 'react';
import { runReconstruction } from '../api';
import Heatmap from './Heatmap';

function Reconstructor() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [params, setParams] = useState({
    k: 0.01,
    max_iterations: 100,
    rms_tolerance: 0.0001,
    plateau_patience: 5
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileUpload = (e) => {
    const files = e.target.files;
    
    // FIX: Check if files exist and has at least one file
    if (!files || files.length === 0) {
      console.error('No file selected');
      return;
    }
    
    const uploadedFile = files[0];
    
    // FIX: Validate it's actually a file
    if (!(uploadedFile instanceof File)) {
      console.error('Invalid file object');
      alert('Please select a valid file');
      return;
    }

    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target.result);
        
        // Validate JSON structure
        if (!json.weight_matrix || !json.projections || !json.grid_shape) {
          throw new Error('Invalid JSON structure. Missing required fields: weight_matrix, projections, or grid_shape');
        }
        
        setData(json);
        setFile(uploadedFile.name);
        console.log('File loaded successfully:', uploadedFile.name);
      } catch (error) {
        console.error('JSON parse error:', error);
        alert('Invalid JSON file: ' + error.message);
      }
    };
    
    reader.onerror = (error) => {
      console.error('FileReader error:', error);
      alert('Error reading file');
    };
    
    // Read as text
    reader.readAsText(uploadedFile);
  };

  const handleReconstruct = async () => {
    if (!data) {
      alert('Please upload a JSON file first');
      return;
    }

    setLoading(true);
    try {
      const reconstructionData = {
        weight_matrix: data.weight_matrix,
        projections: data.projections,
        grid_shape: data.grid_shape,
        ground_truth: data.ground_truth, // Optional for error metrics
        ...params
      };

      const reconstructed = await runReconstruction(reconstructionData);
      setResult(reconstructed);
    } catch (error) {
      console.error('Reconstruction error:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="reconstructor">
      <div className="controls">
        <h2>MART3 Reconstruction</h2>

        <div className="form-group">
          <label>Upload Projection JSON:</label>
          <input 
            type="file" 
            accept=".json,application/json" 
            onChange={handleFileUpload}
            key={file} // Force re-render on file change
          />
          {file && <span className="file-name">📄 {file}</span>}
        </div>

        <div className="form-group">
          <label>Relaxation Parameter (k):</label>
          <input
            type="number"
            min="0.001"
            max="0.1"
            step="0.001"
            value={params.k}
            onChange={(e) => setParams({ ...params, k: parseFloat(e.target.value) })}
          />
          <small>Paper recommends: 0.01-0.05</small>
        </div>

        <div className="form-group">
          <label>Max Iterations:</label>
          <input
            type="number"
            min="10"
            max="500"
            value={params.max_iterations}
            onChange={(e) => setParams({ ...params, max_iterations: parseInt(e.target.value) })}
          />
        </div>

        <div className="form-group">
          <label>RMS Tolerance:</label>
          <input
            type="number"
            min="0.00001"
            max="0.01"
            step="0.00001"
            value={params.rms_tolerance}
            onChange={(e) => setParams({ ...params, rms_tolerance: parseFloat(e.target.value) })}
          />
        </div>

        <div className="form-group">
          <label>Plateau Patience:</label>
          <input
            type="number"
            min="1"
            max="20"
            value={params.plateau_patience}
            onChange={(e) => setParams({ ...params, plateau_patience: parseInt(e.target.value) })}
          />
          <small>Stop if no improvement for N iterations</small>
        </div>

        <button onClick={handleReconstruct} disabled={loading || !data} className="btn-primary">
          {loading ? '⏳ Reconstructing...' : '🔄 Run MART3'}
        </button>
        
        {data && (
          <div className="data-info">
            ✅ Data loaded: {data.num_rays} rays, {data.grid_shape[0]}×{data.grid_shape[1]} grid
          </div>
        )}
      </div>

      {result && (
        <div className="results">
          <h3>Reconstruction Results</h3>

          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Iterations:</span>
              <span className="stat-value">{result.iterations}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Final RMS:</span>
              <span className="stat-value">{result.metrics.rms?.toFixed(4) || 'N/A'}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Avg Error:</span>
              <span className="stat-value">{result.metrics.average_error?.toFixed(4) || 'N/A'}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Normalized Error:</span>
              <span className="stat-value">{(result.metrics.normalized_error * 100)?.toFixed(2) || 'N/A'}%</span>
            </div>
          </div>

          <div className="heatmap-grid">
            {data.ground_truth && (
              <div className="heatmap-container">
                <h4>Ground Truth</h4>
                <Heatmap
                  data={data.ground_truth}
                  gridShape={result.grid_shape}
                  title="Ground Truth"
                />
              </div>
            )}

            <div className="heatmap-container">
              <h4>Reconstructed</h4>
              <Heatmap
                data={result.reconstructed}
                gridShape={result.grid_shape}
                title="MART3 Reconstruction"
              />
            </div>
          </div>

          <div className="convergence-chart">
            <h4>Convergence History</h4>
            <ConvergencePlot data={result.convergence} />
          </div>
        </div>
      )}
    </div>
  );
}

function ConvergencePlot({ data }) {
  if (!data || data.length === 0) {
    return <div>No convergence data available</div>;
  }

  const maxVal = Math.max(...data);
  const minVal = Math.min(...data);
  const range = maxVal - minVal || 1; // Prevent division by zero

  return (
    <div className="convergence-plot">
      <svg width="100%" height="200" viewBox="0 0 500 200">
        <polyline
          points={data.map((val, idx) => {
            const x = (idx / (data.length - 1)) * 480 + 10;
            const y = 180 - ((val - minVal) / range) * 160;
            return `${x},${y}`;
          }).join(' ')}
          fill="none"
          stroke="var(--color-primary)"
          strokeWidth="2"
        />
        <text x="10" y="15" fontSize="12" fill="var(--color-text)">RMS: {maxVal.toFixed(4)}</text>
        <text x="10" y="195" fontSize="12" fill="var(--color-text)">RMS: {minVal.toFixed(4)}</text>
        <text x="450" y="195" fontSize="12" fill="var(--color-text)">Iter: {data.length}</text>
      </svg>
    </div>
  );
}

export default Reconstructor;