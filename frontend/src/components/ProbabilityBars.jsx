import { CLASS_INFO } from '../constants.js';

export default function ProbabilityBars({ probabilities }) {
  return (
    <div className="probabilities">
      <h3>All Probabilities</h3>
      {Object.entries(probabilities || {})
        .sort((a, b) => b[1] - a[1])
        .map(([name, prob]) => (
          <div key={name} className="prob-row">
            <div className="prob-label">
              <span>{CLASS_INFO[name]?.label || name}</span>
              <span>%{(prob * 100).toFixed(2)}</span>
            </div>
            <div className="prob-bar-bg">
              <div
                className="prob-bar-fill"
                style={{
                  width: `${prob * 100}%`,
                  background: CLASS_INFO[name]?.color || '#666',
                }}
              />
            </div>
          </div>
        ))}
    </div>
  );
}
