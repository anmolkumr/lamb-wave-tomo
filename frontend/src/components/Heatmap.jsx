import React from 'react';

function Heatmap({ data, gridShape, title }) {
  const [rows, cols] = gridShape;
  const field2D = [];
  
  // Reshape 1D array to 2D
  for (let i = 0; i < rows; i++) {
    field2D.push(data.slice(i * cols, (i + 1) * cols));
  }

  const min = Math.min(...data);
  const max = Math.max(...data);

  const getColor = (value) => {
    const normalized = (value - min) / (max - min || 1);
    
    // Color scheme: blue (low) → yellow → red (high)
    if (normalized < 0.5) {
      const t = normalized * 2;
      const r = Math.floor(t * 255);
      const g = Math.floor(t * 255);
      const b = 255;
      return `rgb(${r}, ${g}, ${b})`;
    } else {
      const t = (normalized - 0.5) * 2;
      const r = 255;
      const g = Math.floor((1 - t) * 255);
      const b = Math.floor((1 - t) * 255);
      return `rgb(${r}, ${g}, ${b})`;
    }
  };

  const cellSize = Math.min(400 / cols, 400 / rows);

  return (
    <div className="heatmap">
      <div className="heatmap-title">{title}</div>
      <svg width={cols * cellSize} height={rows * cellSize}>
        {field2D.map((row, i) =>
          row.map((value, j) => (
            <rect
              key={`${i}-${j}`}
              x={j * cellSize}
              y={i * cellSize}
              width={cellSize}
              height={cellSize}
              fill={getColor(value)}
              stroke="#333"
              strokeWidth="0.5"
            />
          ))
        )}
      </svg>
      <div className="colorbar">
        <span>Min: {min.toFixed(3)}</span>
        <span>Max: {max.toFixed(3)}</span>
      </div>
    </div>
  );
}

export default Heatmap;
