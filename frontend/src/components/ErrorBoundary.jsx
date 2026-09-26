import React from 'react';
import { HiOutlineExclamationCircle } from 'react-icons/hi';
import './ErrorBoundary.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--color-bg-primary)', textAlign: 'center', padding: '2rem' }}>
          <HiOutlineExclamationCircle className="error-icon" style={{ fontSize: '4rem', color: 'var(--color-accent-red)', marginBottom: '1.5rem' }} />
          <h1 style={{ marginBottom: '1rem' }}>Something went wrong.</h1>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: '2rem', maxWidth: '400px' }}>
            We encountered an unexpected error. Please try refreshing the page. If the problem persists, let us know.
          </p>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button 
              className="btn btn-primary" 
              onClick={() => window.location.reload()}
            >
              Refresh Page
            </button>
            <button 
              className="btn btn-secondary" 
              onClick={() => window.location.href = 'mailto:support@smartcampus.edu?subject=Application Error'}
            >
              Report Issue
            </button>
          </div>
        </div>
      );
    }

    return this.props.children; 
  }
}

export default ErrorBoundary;
