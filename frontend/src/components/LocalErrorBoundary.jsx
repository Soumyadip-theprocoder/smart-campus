import React from 'react';

export default class LocalErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('LocalErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="empty-state" style={{ padding: '2rem', textAlign: 'center', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,50,50,0.2)' }}>
          <div className="empty-icon" style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚠️</div>
          <h3 style={{ color: 'var(--color-accent-red)' }}>Component Failed to Load</h3>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>An error occurred rendering this section. The rest of the page remains functional.</p>
          <button 
            className="btn btn-sm btn-secondary" 
            style={{ marginTop: '1rem' }}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
