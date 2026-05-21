import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { scans } from '../api.js';
import { CLASS_INFO } from '../constants.js';
import LoadingSpinner from '../components/LoadingSpinner.jsx';
import ErrorAlert from '../components/ErrorAlert.jsx';

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    scans.list()
      .then(setItems)
      .catch((err) => setError(err.message || 'Failed to load scans'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container">
      <header className="header">
        <h1>Scan History</h1>
        <p className="subtitle">Your previous MRI analyses</p>
      </header>

      <main className="main">
        <ErrorAlert error={error} />

        {items.length === 0 && !error && (
          <div className="empty-state">
            <p>No scans yet.</p>
            <Link to="/scan" className="btn btn-primary">
              Upload your first MRI
            </Link>
          </div>
        )}

        {items.length > 0 && (
          <div className="history-list">
            {items.map((scan) => {
              const info = CLASS_INFO[scan.tumor_class] || { label: scan.tumor_class, color: '#666' };
              const date = new Date(scan.upload_date);
              return (
                <Link
                  key={scan.scan_id}
                  to={`/scans/${scan.scan_id}`}
                  className="history-item"
                >
                  <div
                    className="history-icon"
                    style={{ background: info.color }}
                  >
                    {scan.has_tumor ? '⚠' : '✓'}
                  </div>
                  <div className="history-content">
                    <div className="history-title">
                      {info.label}
                      <span className="history-confidence">
                        %{(scan.confidence * 100).toFixed(1)}
                      </span>
                    </div>
                    <div className="history-meta">
                      <span>{scan.original_filename}</span>
                      <span>·</span>
                      <span>{date.toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="history-arrow">→</div>
                </Link>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
