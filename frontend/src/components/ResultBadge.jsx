import { CLASS_INFO } from '../constants.js';

//badge 
export default function ResultBadge({ scan }) {
  const info = CLASS_INFO[scan.tumor_class] || { label: scan.tumor_class, color: '#666' };
  return (
    <div
      className={`result-badge ${scan.has_tumor ? 'bad' : 'good'}`}
      style={{ borderColor: info.color }}
    >
      <div className="result-label">Prediction</div>
      <div className="result-value">{info.label}</div>
      <div className="result-confidence">
        Confidence: %{(scan.confidence * 100).toFixed(2)}
      </div>
    </div>
  );
}
