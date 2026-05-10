import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { HiOutlineLockClosed, HiOutlineMail } from 'react-icons/hi';
import './LoginPage.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const result = await login(email, password);
    if (result.success) {
      const role = result.user.role;
      if (role === 'admin') {
        navigate('/admin/courses');
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

          <div className="login-demo-credentials">
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
        </div>
      </div>
    </div>
  );
}
