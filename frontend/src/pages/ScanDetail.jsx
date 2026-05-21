import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { scans } from '../api.js';
import { DISCLAIMER } from '../constants.js';
import LoadingSpinner from '../components/LoadingSpinner.jsx';
import ErrorAlert from '../components/ErrorAlert.jsx';
import ResultBadge from '../components/ResultBadge.jsx';
import ProbabilityBars from '../components/ProbabilityBars.jsx';
import ConfirmModal from '../components/ConfirmModal.jsx';

//states
export default function ScanDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  //get scan
  useEffect(() => {
    let mounted = true;
    scans.get(id)
      .then((data) => { if (mounted) setScan(data); })
      .catch((err) => { if (mounted) setError(err.message || 'Failed to load scan'); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [id]);

  //delete scan
  async function handleDeleteConfirm() {
    setShowDeleteModal(false);
    setDeleting(true);
    try {
      await scans.delete(id);
      navigate('/history');
    } catch (err) {
      setError(err.message || 'Failed to delete scan');
      setDeleting(false);
    }
  }

  //download scan pdf
  function handleDownloadPdf() {
    window.open(scans.reportUrl(id), '_blank');
  }

  if (loading) return <LoadingSpinner />;

  if (error || !scan) {
    return (
      <div className="container">
        <header className="header">
          <h1>Scan Not Found</h1>
        </header>
        <main className="main">
          <ErrorAlert error={error || 'Scan does not exist'} />
          <Link to="/history" className="btn btn-secondary">
            ← Back to History
          </Link>
        </main>
      </div>
    );
  }

  const date = new Date(scan.upload_date);

  return (
    <>
      <div className="container">
        <header className="header">
          <Link to="/history" className="back-link">← History</Link>
          <h1>Scan Detail</h1>
          <p className="subtitle">{date.toLocaleString()}</p>
        </header>

        <main className="main">
          <div className="card">
            <div className="filename" style={{ marginBottom: '1rem', textAlign: 'center' }}>
              {scan.original_filename}
            </div>

            <div className="result">
              <ResultBadge scan={scan} />
              <ProbabilityBars probabilities={scan.all_probabilities} />

              <div className="result-actions">
                <button className="btn btn-primary" onClick={handleDownloadPdf}>
                  Download PDF Report
                </button>
                <button
                  className="btn btn-danger"
                  onClick={() => setShowDeleteModal(true)}
                  disabled={deleting}
                >
                  {deleting ? 'Deleting...' : 'Delete Scan'}
                </button>
              </div>

              <div className="disclaimer">{DISCLAIMER}</div>
            </div>
          </div>
        </main>
      </div>

      {showDeleteModal && (
        <ConfirmModal
          title="Scan'ı Sil"
          message={`"${scan.original_filename}" dosyasını silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.`}
          confirmText="Sil"
          danger
          onConfirm={handleDeleteConfirm}
          onCancel={() => setShowDeleteModal(false)}
        />
      )}
    </>
  );
}
