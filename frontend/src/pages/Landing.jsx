import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="landing">
      <div className="landing-hero">
        <div className="landing-badge">AI-Powered Brain MRI Analysis</div>
        <h1 className="landing-title">
          Neuro<span className="landing-title-accent">Scan</span>
        </h1>
        <p className="landing-subtitle">
          Upload brain MRI scans and get instant AI-driven tumor classification with confidence scores and detailed probability breakdowns.
        </p>
        <div className="landing-actions">
          <Link to="/register" className="btn btn-primary landing-cta">
            Register
          </Link>
          <Link to="/login" className="btn btn-secondary landing-cta">
            Sign In
          </Link>
        </div>
      </div>

      <p className="landing-disclaimer">
        For research and educational purposes only. Not a substitute for professional medical diagnosis.
      </p>
    </div>
  );
}
