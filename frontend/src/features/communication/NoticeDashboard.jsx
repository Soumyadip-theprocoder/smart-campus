import { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import './NoticeDashboard.css';

export default function NoticeDashboard() {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
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

  const priorityIcons = {
    low: '💡', medium: '📢', high: '⚠️', urgent: '🚨',
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
            {showForm ? 'Cancel' : '+ New Notice'}
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
          notices.map((notice, i) => (
            <div
              key={notice.id}
              className={`glass-card notice-card priority-${notice.priority} animate-fade-in-up`}
              style={{ opacity: 0, animationDelay: `${i * 0.05}s` }}
            >
              <div className="notice-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>{priorityIcons[notice.priority] || '📢'}</span>
                  <span className="notice-title">{notice.title}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className={`badge badge-${notice.priority}`}>
                    {notice.priority_display || notice.priority}
                  </span>
                  {notice.email_sent && (
                    <span className="badge badge-low" title="Email sent">📧</span>
                  )}
                </div>
              </div>
              <p className="notice-content">{notice.content}</p>
              <div className="notice-meta">
                Posted by {notice.posted_by_name} · {new Date(notice.created_at).toLocaleDateString('en-US', {
                  year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
                })}
                {notice.target_audience !== 'all' && (
                  <span> · For: {notice.target_audience}</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
