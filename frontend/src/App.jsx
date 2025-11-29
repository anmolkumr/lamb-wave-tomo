import React, { useState } from 'react';
import Reconstructor from './components/Reconstructor';
import Simulator from './components/Simulator';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('simulator');

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔬 Lamb-Wave Tomography System</h1>
        <p>MART3 Reconstruction with Modified Cross-Hole Geometry</p>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'simulator' ? 'active' : ''}
          onClick={() => setActiveTab('simulator')}
        >
          📊 Simulator
        </button>
        <button
          className={activeTab === 'reconstructor' ? 'active' : ''}
          onClick={() => setActiveTab('reconstructor')}
        >
          🔄 Reconstructor
        </button>
      </nav>

      <main className="content">
        {activeTab === 'simulator' && <Simulator />}
        {activeTab === 'reconstructor' && <Reconstructor />}
      </main>

      <footer className="app-footer">
        <p>Based on: Khare et al. (2007) - Defect Detection in Carbon-Fiber Composites Using Lamb-Wave Tomographic Methods</p>
      </footer>
    </div>
  );
}

export default App;
