import { useState, useEffect, useRef } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import './NoticeDashboard.css';

export default function NoticeDashboard() {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [openMenuId, setOpenMenuId] = useState(null);
  const menuRef = useRef(null);
  const [form, setForm] = useState({
    title: '',
    content: '',
    priority: 'medium',
    target_audience: 'all',
    send_email: false,
  });
  const [submitting, setSubmitting] = useState(false);
  const { isAdmin } = useAuth();

  useEffect(() => {
    loadNotices();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpenMenuId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadNotices = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/communication/notices/');
      setNotices(response.data.results || response.data || []);
    } catch (err) {
      console.error('Failed to load notices:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const response = await api.post('/api/communication/notices/create/', form);
      setShowForm(false);
      setForm({
        title: '', content: '', priority: 'medium',
        target_audience: 'all', send_email: false,
      });
      loadNotices();

      if (response.data.emails_sent > 0) {
        alert(`Notice created and ${response.data.emails_sent} emails sent!`);
      }
    } catch (err) {
      alert('Failed to create notice.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this notice? This action cannot be undone.')) {
      return;
    }
    try {
      await api.delete(`/api/communication/notices/${id}/delete/`);
      setNotices(prev => prev.filter(n => n.id !== id));
      setOpenMenuId(null);
    } catch (err) {
      console.error('Failed to delete notice:', err);
      alert('Failed to delete notice. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Notice Board</h1>
          <p>Campus announcements and important updates</p>
        </div>
        {isAdmin && (
          <button
            className="btn btn-primary"
            onClick={() => setShowForm(!showForm)}
            id="btn-toggle-notice-form"
          >
            {showForm ? 'Cancel' : '+ Add Notification'}
          </button>
        )}
      </div>

      {/* Create Notice Form */}
      {showForm && isAdmin && (
        <div className="glass-card create-notice-form animate-fade-in-up" style={{ opacity: 0 }}>
          <h3 style={{ marginBottom: '1.25rem', fontWeight: 600 }}>Create Notice</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="notice-title">Title</label>
              <input
                type="text"
                id="notice-title"
                className="form-input"
                placeholder="Enter notice title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="notice-content">Content</label>
              <textarea
                id="notice-content"
                className="form-textarea"
                placeholder="Enter notice content..."
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
                required
                rows={4}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="notice-priority">Priority</label>
                <select
                  id="notice-priority"
                  className="form-select"
                  value={form.priority}
                  onChange={(e) => setForm({ ...form, priority: e.target.value })}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="notice-audience">Target Audience</label>
                <select
                  id="notice-audience"
                  className="form-select"
                  value={form.target_audience}
                  onChange={(e) => setForm({ ...form, target_audience: e.target.value })}
                >
                  <option value="all">All</option>
                  <option value="students">Students Only</option>
                  <option value="faculty">Faculty Only</option>
                </select>
              </div>
            </div>

            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.send_email}
                  onChange={(e) => setForm({ ...form, send_email: e.target.checked })}
                />
                <span>Send email notification</span>
              </label>
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="btn btn-success"
                disabled={submitting}
                id="btn-submit-notice"
              >
                {submitting ? 'Publishing...' : 'Publish Notice'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Notices List */}
      <div className="notices-list" style={{ marginTop: showForm ? '1.5rem' : 0 }}>
        {notices.length === 0 ? (
          <div className="glass-card" style={{ padding: '3rem' }}>
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>No Notices</h3>
              <p>There are no announcements at this time.</p>
            </div>
          </div>
        ) : (
          notices.map((notice, i) => {
            const isError = notice.priority === 'urgent' || notice.priority === 'high';
            const isMenuOpen = openMenuId === notice.id;
            return (
              <div
                key={notice.id}
                className={`notice-card priority-${notice.priority} animate-fade-in-up`}
                style={{
                  opacity: 0,
                  animationDelay: `${i * 0.05}s`,
                  background: 'transparent',
                  border: `1px solid ${isError ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                  borderLeft: `3px solid ${isError ? 'var(--color-accent-red)' : 'var(--color-accent-emerald)'}`,
                  borderRadius: 'var(--radius-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '1rem 1.25rem'
                }}
              >
                <div style={{ flex: 1 }}>
                  <div className="notice-header" style={{ marginBottom: '0.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ color: isError ? 'var(--color-accent-red)' : 'var(--color-accent-emerald)' }}>
                        {isError ? '⚠️' : '✅'}
                      </span>
                      <span className="notice-title" style={{ fontSize: '1rem' }}>{notice.title}</span>
                      <span
                        className="badge"
                        style={{
                          background: isError ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)',
                          color: isError ? 'var(--color-accent-red)' : 'var(--color-accent-emerald)',
                          padding: '2px 8px',
                          fontSize: '0.65rem',
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px'
                        }}
                      >
                        {notice.priority}
                      </span>
                    </div>
                  </div>
                  <p className="notice-content" style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', margin: 0, marginBottom: '0.25rem' }}>
                    {notice.content}
                  </p>
                  <div className="notice-meta" style={{ fontSize: '0.75rem' }}>
                    {new Date(notice.created_at).toLocaleString('en-GB')}
                    {notice.target_audience && notice.target_audience !== 'all' && (
                      <span style={{ marginLeft: '0.75rem', opacity: 0.7 }}>
                        👥 {notice.target_audience}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions Dropdown — Admin only */}
                {isAdmin && (
                  <div style={{ position: 'relative' }} ref={isMenuOpen ? menuRef : null}>
                    <button
                      onClick={() => setOpenMenuId(isMenuOpen ? null : notice.id)}
                      style={{
                        background: 'none',
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '6px',
                        padding: '0.35rem 0.5rem',
                        cursor: 'pointer',
                        color: 'var(--color-text-muted)',
                        fontSize: '1.1rem',
                        lineHeight: 1,
                        transition: 'all 0.2s ease',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                      title="Actions"
                      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
                    >
                      ⋮
                    </button>

                    {isMenuOpen && (
                      <div
                        style={{
                          position: 'absolute',
                          right: 0,
                          top: 'calc(100% + 4px)',
                          background: 'var(--color-bg-elevated, #1e1e2e)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                          zIndex: 100,
                          minWidth: '160px',
                          overflow: 'hidden',
                          animation: 'fadeIn 0.15s ease',
                        }}
                      >
                        <button
                          onClick={() => {
                            handleDelete(notice.id);
                          }}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            width: '100%',
                            padding: '0.65rem 1rem',
                            border: 'none',
                            background: 'none',
                            color: 'var(--color-accent-red)',
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            textAlign: 'left',
                            transition: 'background 0.15s ease',
                          }}
                          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(239,68,68,0.1)'}
                          onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
                        >
                          🗑️ Delete Notice
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
