import { useState, useRef } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000';

const CLASS_INFO = {
  glioma:      { label: 'Glioma',       color: '#e74c3c' },
  meningioma:  { label: 'Meningioma',   color: '#e67e22' },
  notumor:     { label: 'No Tumor',   color: '#27ae60' },
  pituitary:   { label: 'Pituitary',     color: '#9b59b6' },
};

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  function handleFileSelect(e) {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError(null);
  }

  function handleDrop(e) {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && dropped.type.startsWith('image/')) {
      setFile(dropped);
      setPreview(URL.createObjectURL(dropped));
      setResult(null);
      setError(null);
    }
  }

  async function handleAnalyze() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Hata: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Connection Error');
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  return (
    <div className="container">
      <header className="header">
        <h1>NeuroScan</h1>
        <p className="subtitle">Brain Tumor Classifier</p>
        {result && (
          <p className="header-confidence">
          Güven Skoru: %{(result.confidence * 100).toFixed(2)}
          </p>
        )}
      </header>

      <main className="main">
        {!preview && (
          <div
            className="dropzone"
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
          >
            <div className="dropzone-icon">📁</div>
            <p className="dropzone-text">Choose or Drag MRI</p>
            <p className="dropzone-hint">JPG, JPEG OR PNG</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/jpg,image/png"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>
        )}

        {preview && (
          <div className="card">
            <div className="preview-section">
              <img src={preview} alt="MRI preview" className="preview" />
              <div className="filename">{file?.name}</div>
            </div>

            <div className="actions">
              <button
                className="btn btn-primary"
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Analyzing...
                  </>
                ) : (
                  'Analyze'
                )}
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleReset}
                disabled={loading}
              >
                Temizle
              </button>
            </div>

            {error && (
              <div className="alert alert-error">
                <strong>Error:</strong> {error}
              </div>
            )}

            {result && (
              <div className="result">
                <div
                  className={`result-badge ${result.has_tumor ? 'bad' : 'good'}`}
                  style={{ borderColor: CLASS_INFO[result.prediction]?.color }}
                >
                  <div className="result-label">Predict</div>
                  <div className="result-value">
                    {CLASS_INFO[result.prediction]?.label || result.prediction}
                  </div>
                  <div className="result-confidence">
                    Güven: %{(result.confidence * 100).toFixed(2)}
                  </div>
                </div>

                <div className="probabilities">
                  <h3>All Probabilities</h3>
                  {Object.entries(result.all_probabilities || {})
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

                <div className="disclaimer">
                  !!! This tool is an academic demo project. It does not replace real treatment or diagnosis !!!
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="footer">
        ResNet50V2 · Transfer Learning · Nickparvar Dataset
      </footer>
    </div>
  );
}