import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { HiOutlineLockClosed, HiOutlineMail } from 'react-icons/hi';
import api from '../../api/axios';
import './LoginPage.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showDemo, setShowDemo] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const handleTryDemo = async () => {
    setSeeding(true);
    try {
      await api.post('/api/auth/seed/');
      setShowDemo(true);
    } catch (err) {
      console.error('Failed to seed DB', err);
      // Still show demo on fail just in case DB is already seeded but API errors
      setShowDemo(true); 
    } finally {
      setSeeding(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const result = await login(email, password);
    if (result.success) {
      const role = result.user.role;
      if (role === 'admin') {
        navigate('/admin');
      } else if (role === 'student') {
        navigate('/student');
      } else if (role === 'faculty') {
        navigate('/faculty');
      } else {
        navigate('/timetable');
      }
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container animate-fade-in-up">
        <div className="login-logo">
          <div className="login-logo-icon">🎓</div>
          <h1>Smart Campus</h1>
          <p>Management System</p>
        </div>

        <div className="glass-card login-form">
          <h2 className="login-form-title">Welcome Back</h2>
          <p className="login-form-subtitle">Sign in to your account</p>

          {error && <div className="login-error" id="login-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="email">Email Address</label>
              <div className="input-with-icon">
                <HiOutlineMail className="input-icon" />
                <input
                  type="email"
                  id="email"
                  className="form-input"
                  placeholder="you@smartcampus.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="password">Password</label>
              <div className="input-with-icon">
                <HiOutlineLockClosed className="input-icon" />
                <input
                  type="password"
                  id="password"
                  className="form-input"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary login-btn"
              disabled={loading}
              id="login-submit-btn"
            >
              {loading ? (
                <span className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {showDemo ? (
            <div className="login-demo-credentials animate-fade-in-up">
              <p className="demo-title">Demo Credentials</p>
              <div className="demo-accounts">
                <button
                  className="demo-account"
                  onClick={() => { setEmail('admin@smartcampus.edu'); setPassword('admin123'); }}
                  type="button"
                >
                  <span className="demo-role">Admin</span>
                  <span className="demo-email">admin@smartcampus.edu</span>
                </button>
                <button
                  className="demo-account"
                  onClick={() => { setEmail('alice.brown@smartcampus.edu'); setPassword('student123'); }}
                  type="button"
                >
                  <span className="demo-role">Student</span>
                  <span className="demo-email">alice.brown@smartcampus.edu</span>
                </button>
                <button
                  className="demo-account"
                  onClick={() => { setEmail('john.smith@smartcampus.edu'); setPassword('faculty123'); }}
                  type="button"
                >
                  <span className="demo-role">Faculty</span>
                  <span className="demo-email">john.smith@smartcampus.edu</span>
                </button>
              </div>
            </div>
          ) : (
            <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={handleTryDemo}
                disabled={seeding}
              >
                {seeding ? (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> 
                    Seeding Demo Data...
                  </span>
                ) : (
                  'Try Demo'
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
