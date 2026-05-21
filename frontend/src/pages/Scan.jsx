import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { scans } from '../api.js';
import { DISCLAIMER } from '../constants.js';
import ErrorAlert from '../components/ErrorAlert.jsx';
import ResultBadge from '../components/ResultBadge.jsx';
import ProbabilityBars from '../components/ProbabilityBars.jsx';

//states
export default function Scan() {
  const [upload, setUpload] = useState(null); // { file, preview } | null
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  //clean up blob URL
  useEffect(() => {
    const url = upload?.preview;
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [upload?.preview]);

  //select file
  function selectFile(file) {
    if (upload?.preview) URL.revokeObjectURL(upload.preview);
    setUpload({ file, preview: URL.createObjectURL(file) });
    setResult(null);
    setError(null);
  }

  //select file manuel
  function handleFileSelect(e) {
    const f = e.target.files?.[0];
    if (f) selectFile(f);
  }

  //select file drag&drop
  function handleDrop(e) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f?.type.startsWith('image/')) selectFile(f);
  }

  //Send analyze to the backend.
  async function handleAnalyze() {
    if (!upload) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await scans.predict(upload.file));
    } catch (err) {
      setError(err.message || 'Connection error');
    } finally {
      setLoading(false);
    }
  }

  //Clear all state
  function handleReset() {
    if (upload?.preview) URL.revokeObjectURL(upload.preview);
    setUpload(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  return (
    <div className="container">
      <header className="header">
        <h1>NeuroScan</h1>
        <p className="subtitle">Brain Tumor Classifier</p>
      </header>

      <main className="main">
        {!upload && (
          <>
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
            <div className="disclaimer">{DISCLAIMER}</div>
          </>
        )}

        {upload && (
          <div className="card">
            <div className="preview-section">
              <img src={upload.preview} alt="MRI preview" className="preview" />
              <div className="filename">{upload.file.name}</div>
            </div>

            <div className="actions">
              <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading}>
                {loading ? <><span className="spinner"></span>Analyzing...</> : 'Analyze'}
              </button>
              <button className="btn btn-secondary" onClick={handleReset} disabled={loading}>
                Clear
              </button>
            </div>

            <ErrorAlert error={error} />

            {result && (
              <div className="result">
                <ResultBadge scan={result} />
                <ProbabilityBars probabilities={result.all_probabilities} />
                <div className="result-actions">
                  <button
                    className="btn btn-secondary"
                    onClick={() => navigate(`/scans/${result.scan_id}`)}
                  >
                    View Full Details
                  </button>
                </div>
                <div className="disclaimer">{DISCLAIMER}</div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
