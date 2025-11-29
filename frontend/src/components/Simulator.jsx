import React, { useState } from 'react';
import { generateSimulation } from '../api';
import Heatmap from './Heatmap';

function Simulator() {
  const [config, setConfig] = useState({
    grid_size: 11,
    case: 'central_hole',
    noise_level: 0.0,
    defect_params: {
      shape: 'rectangle',
      radius: 2,
      width: 3,
      height: 3,
      value: 0.0
    }
  });

  // NEW: Realistic simulation toggle
  const [realisticMode, setRealisticMode] = useState(false);
  const [realisticConfig, setRealisticConfig] = useState({
    material_type: 'aluminum',
    noise_level: 0.05,
    edge_effects: true,
    anisotropy_factor: 0.0
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const materialPresets = {
    aluminum: {
      noise_level: 0.05,
      anisotropy_factor: 0.0,
      description: 'Isotropic aluminum (Fig 11 in paper)'
    },
    cfrp: {
      noise_level: 0.08,
      anisotropy_factor: 0.15,
      description: 'CFRP composite (Fig 12 in paper)'
    },
    steel: {
      noise_level: 0.04,
      anisotropy_factor: 0.02,
      description: 'Mild steel'
    },
    custom: {
      noise_level: realisticConfig.noise_level,
      anisotropy_factor: realisticConfig.anisotropy_factor,
      description: 'Custom parameters'
    }
  };

  const handleMaterialChange = (material) => {
    const preset = materialPresets[material];
    setRealisticConfig({
      ...realisticConfig,
      material_type: material,
      noise_level: preset.noise_level,
      anisotropy_factor: preset.anisotropy_factor
    });
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      let data;
      
      if (realisticMode) {
        // Call realistic simulation endpoint
        const response = await fetch('http://localhost:5000/api/simulate_realistic', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...config,
            ...realisticConfig
          })
        });
        
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Realistic simulation failed');
        }
        
        data = await response.json();
      } else {
        // Standard simulation
        data = await generateSimulation(config);
      }
      
      setResult(data);
      
      // Auto-download JSON
      const filename = realisticMode 
        ? `realistic_${realisticConfig.material_type}_${config.case}_${config.grid_size}x${config.grid_size}.json`
        : `simulation_${config.case}_${config.grid_size}x${config.grid_size}.json`;
      
      downloadJSON(data, filename);
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = (data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="simulator">
      <div className="controls">
        <h2>Generate Synthetic Projections</h2>

        {/* Realistic Mode Toggle */}
        <div className="form-group realistic-toggle">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={realisticMode}
              onChange={(e) => setRealisticMode(e.target.checked)}
            />
            <span className="toggle-text">
              🔬 Realistic Mode (Experimental Artifacts)
            </span>
          </label>
          {realisticMode && (
            <small className="toggle-hint">
              Adds noise, edge effects, and material anisotropy to match real Lamb wave data
            </small>
          )}
        </div>

        {/* Realistic Parameters (shown only in realistic mode) */}
        {realisticMode && (
          <div className="realistic-params">
            <h3 style={{fontSize: '1rem', marginBottom: '1rem'}}>Experimental Artifacts</h3>
            
            <div className="form-group">
              <label>Material Type:</label>
              <select
                value={realisticConfig.material_type}
                onChange={(e) => handleMaterialChange(e.target.value)}
              >
                <option value="aluminum">Aluminum (Isotropic)</option>
                <option value="cfrp">CFRP Composite (Anisotropic)</option>
                <option value="steel">Steel (Mild Anisotropy)</option>
                <option value="custom">Custom Parameters</option>
              </select>
              <small>{materialPresets[realisticConfig.material_type].description}</small>
            </div>

            <div className="form-group">
              <label>Noise Level (σ): {(realisticConfig.noise_level * 100).toFixed(1)}%</label>
              <input
                type="range"
                min="0"
                max="0.2"
                step="0.01"
                value={realisticConfig.noise_level}
                onChange={(e) => setRealisticConfig({
                  ...realisticConfig,
                  noise_level: parseFloat(e.target.value),
                  material_type: 'custom'
                })}
              />
              <small>Coupling variations & sensor noise (0-20%)</small>
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={realisticConfig.edge_effects}
                  onChange={(e) => setRealisticConfig({
                    ...realisticConfig,
                    edge_effects: e.target.checked
                  })}
                />
                Edge Reflection Artifacts
              </label>
              <small>Boundary reflections affect near-edge rays</small>
            </div>

            <div className="form-group">
              <label>Anisotropy Factor: {realisticConfig.anisotropy_factor.toFixed(2)}</label>
              <input
                type="range"
                min="0"
                max="0.3"
                step="0.01"
                value={realisticConfig.anisotropy_factor}
                onChange={(e) => setRealisticConfig({
                  ...realisticConfig,
                  anisotropy_factor: parseFloat(e.target.value),
                  material_type: 'custom'
                })}
              />
              <small>Directional wave speed (0=isotropic, 0.15=CFRP)</small>
            </div>
          </div>
        )}

        {/* Standard Parameters */}
        <div className="standard-params" style={{marginTop: realisticMode ? '1.5rem' : '0'}}>
          {realisticMode && <h3 style={{fontSize: '1rem', marginBottom: '1rem'}}>Specimen Configuration</h3>}
          
          <div className="form-group">
            <label>Grid Size (N×N):</label>
            <input
              type="number"
              min="5"
              max="50"
              value={config.grid_size}
              onChange={(e) => setConfig({ ...config, grid_size: parseInt(e.target.value) })}
            />
          </div>

          <div className="form-group">
            <label>Test Case:</label>
            <select
              value={config.case}
              onChange={(e) => setConfig({ ...config, case: e.target.value })}
            >
              <option value="constant">Constant Field</option>
              <option value="impulse">Impulse (Single Pixel)</option>
              <option value="central_hole">Central Hole</option>
              <option value="off_center_rect">Off-Center Rectangle</option>
            </select>
          </div>

          {config.case === 'central_hole' && (
            <>
              <div className="form-group">
                <label>Shape:</label>
                <select
                  value={config.defect_params.shape}
                  onChange={(e) => setConfig({
                    ...config,
                    defect_params: { ...config.defect_params, shape: e.target.value }
                  })}
                >
                  <option value="circle">Circle</option>
                  <option value="rectangle">Rectangle</option>
                </select>
              </div>

              {config.defect_params.shape === 'circle' ? (
                <div className="form-group">
                  <label>Radius (pixels):</label>
                  <input
                    type="number"
                    min="1"
                    max={Math.floor(config.grid_size / 2)}
                    value={config.defect_params.radius}
                    onChange={(e) => setConfig({
                      ...config,
                      defect_params: { ...config.defect_params, radius: parseInt(e.target.value) }
                    })}
                  />
                </div>
              ) : (
                <>
                  <div className="form-group">
                    <label>Width (pixels):</label>
                    <input
                      type="number"
                      min="1"
                      max={config.grid_size}
                      value={config.defect_params.width}
                      onChange={(e) => setConfig({
                        ...config,
                        defect_params: { ...config.defect_params, width: parseInt(e.target.value) }
                      })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Height (pixels):</label>
                    <input
                      type="number"
                      min="1"
                      max={config.grid_size}
                      value={config.defect_params.height}
                      onChange={(e) => setConfig({
                        ...config,
                        defect_params: { ...config.defect_params, height: parseInt(e.target.value) }
                      })}
                    />
                  </div>
                </>
              )}
            </>
          )}
        </div>

        <button onClick={handleGenerate} disabled={loading} className="btn-primary">
          {loading ? '⏳ Generating...' : '🚀 Generate Simulation'}
        </button>
      </div>

      {result && (
        <div className="results">
          <h3>Generated System</h3>
          
          {realisticMode && result.realistic_params && (
            <div className="realistic-info">
              <h4>Experimental Artifacts Applied:</h4>
              <div className="artifact-list">
                <div className="artifact-item">
                  <span className="artifact-icon">🔊</span>
                  <span>Noise: {(result.realistic_params.noise_level * 100).toFixed(1)}%</span>
                </div>
                {result.realistic_params.edge_effects && (
                  <div className="artifact-item">
                    <span className="artifact-icon">🌊</span>
                    <span>Edge Reflections</span>
                  </div>
                )}
                {result.realistic_params.anisotropy_factor > 0 && (
                  <div className="artifact-item">
                    <span className="artifact-icon">⚡</span>
                    <span>Anisotropy: {result.realistic_params.anisotropy_factor.toFixed(2)}</span>
                  </div>
                )}
                <div className="artifact-item">
                  <span className="artifact-icon">🎛️</span>
                  <span>Mode Conversion</span>
                </div>
                <div className="artifact-item">
                  <span className="artifact-icon">💾</span>
                  <span>16-bit Quantization</span>
                </div>
              </div>
            </div>
          )}
          
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Grid Size:</span>
              <span className="stat-value">{result.grid_shape[0]} × {result.grid_shape[1]}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Total Rays:</span>
              <span className="stat-value">{result.num_rays}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Subsets:</span>
              <span className="stat-value">{result.num_subsets}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Mode:</span>
              <span className="stat-value">{realisticMode ? '🔬 Realistic' : '✨ Ideal'}</span>
            </div>
          </div>

          <div className="heatmap-container">
            <h4>Ground Truth Field</h4>
            <Heatmap
              data={result.ground_truth}
              gridShape={result.grid_shape}
              title="Ground Truth"
            />
          </div>

          <div className="download-info">
            ✅ Simulation data auto-downloaded as JSON. Use in Reconstructor tab!
          </div>
        </div>
      )}
    </div>
  );
}

export default Simulator;
