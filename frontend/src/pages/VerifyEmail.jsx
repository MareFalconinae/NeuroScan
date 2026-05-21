import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { auth as authApi } from '../api.js';
import ErrorAlert from '../components/ErrorAlert.jsx';

export default function VerifyEmail() {
  const location = useLocation();
  const navigate = useNavigate();
  const { verifyEmail } = useAuth();

  const email = location.state?.email || '';

  const [code, setCode] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMsg, setResendMsg] = useState(null);

  if (!email) {
    navigate('/register', { replace: true });
    return null;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await verifyEmail({ email, code });
      navigate('/scan', { replace: true });
    } catch (err) {
      setError(err.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setError(null);
    setResendMsg(null);
    setResendLoading(true);
    try {
      await authApi.resendVerification({ email });
      setResendMsg('New code sent. Check your email.');
    } catch (err) {
      setError(err.message || 'Could not resend code');
    } finally {
      setResendLoading(false);
    }
  }

  return (
    <div className="auth-container">
      <div className="card auth-card">
        <h1 className="auth-title">Verify Your Email</h1>
        <p className="auth-subtitle">
          We sent a 6-digit code to <strong>{email}</strong>
        </p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label className="auth-label">
            Verification Code
            <input
              type="text"
              required
              inputMode="numeric"
              pattern="\d{6}"
              maxLength={6}
              placeholder="000000"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              disabled={loading}
              autoFocus
              style={{ letterSpacing: '0.3em', fontSize: '1.4rem', textAlign: 'center' }}
            />
          </label>

          <ErrorAlert error={error} />

          {resendMsg && (
            <p style={{ color: 'var(--good)', fontSize: '0.875rem', textAlign: 'center' }}>
              {resendMsg}
            </p>
          )}

          <button
            type="submit"
            className="btn btn-primary auth-submit"
            disabled={loading || code.length !== 6}
          >
            {loading ? (
              <><span className="spinner"></span>Verifying...</>
            ) : (
              'Verify Email'
            )}
          </button>
        </form>

        <p className="auth-switch">
          Didn't receive the code?{' '}
          <button
            type="button"
            onClick={handleResend}
            disabled={resendLoading}
            style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: 0 }}
          >
            {resendLoading ? 'Sending...' : 'Resend'}
          </button>
        </p>
      </div>
    </div>
  );
}
