import { useState, useEffect } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';

/* ─── Tiny modal component ─────────────────────────────────────── */
function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content glass-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

/* ─── Confirm dialog ───────────────────────────────────────────── */
function ConfirmDialog({ open, onClose, onConfirm, message }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content glass-card confirm-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <p style={{ marginBottom: '1.5rem', color: 'var(--color-text-secondary)' }}>
          {message}
        </p>
        <div className="confirm-actions">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-danger" onClick={onConfirm}>Delete</button>
        </div>
      </div>
    </div>
  );
}

/* ─── Add Faculty Form ─────────────────────────────────────────── */
function AddFacultyForm({ onSave, saving }) {
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    username: '',
    password: '',
    employee_id: '',
    department: '',
    designation: 'Assistant Professor',
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  // Auto-generate username from email
  const handleEmailChange = (e) => {
    const email = e.target.value;
    setForm((prev) => ({
      ...prev,
      email,
      username: email.split('@')[0] || prev.username,
    }));
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.email || !form.first_name || !form.last_name || !form.employee_id || !form.department) {
      setError('Please fill all required fields.');
      return;
    }
    onSave({
      email: form.email,
      username: form.username,
      password: form.password || 'campus@123',
      first_name: form.first_name,
      last_name: form.last_name,
      role: 'faculty',
      employee_id: form.employee_id,
      department: form.department,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div style={{
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          borderRadius: '0.5rem',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#ef4444',
          fontSize: '0.85rem',
        }}>
          {error}
        </div>
      )}
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">First Name *</label>
          <input
            className="form-input"
            name="first_name"
            value={form.first_name}
            onChange={handleChange}
            placeholder="e.g. John"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Last Name *</label>
          <input
            className="form-input"
            name="last_name"
            value={form.last_name}
            onChange={handleChange}
            placeholder="e.g. Doe"
            required
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Email *</label>
        <input
          className="form-input"
          type="email"
          name="email"
          value={form.email}
          onChange={handleEmailChange}
          placeholder="e.g. john.doe@university.edu"
          required
        />
      </div>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Employee ID *</label>
          <input
            className="form-input"
            name="employee_id"
            value={form.employee_id}
            onChange={handleChange}
            placeholder="e.g. FAC-001"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Password</label>
          <input
            className="form-input"
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            placeholder="Default: campus@123"
          />
        </div>
      </div>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Department *</label>
          <input
            className="form-input"
            name="department"
            value={form.department}
            onChange={handleChange}
            placeholder="e.g. Computer Science"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Designation</label>
          <select
            className="form-select"
            name="designation"
            value={form.designation}
            onChange={handleChange}
          >
            <option value="Assistant Professor">Assistant Professor</option>
            <option value="Associate Professor">Associate Professor</option>
            <option value="Professor">Professor</option>
            <option value="HOD">HOD</option>
            <option value="Lecturer">Lecturer</option>
          </select>
        </div>
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : 'Add Faculty'}
      </button>
    </form>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function FacultyPage() {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchFaculty();
  }, []);

  const fetchFaculty = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/auth/faculty/');
      setFaculty(response.data.results || response.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  /* ── Add faculty via register endpoint ───────────────────────── */
  const handleSave = async (formData) => {
    setSaving(true);
    try {
      await api.post('/api/auth/register/', formData);
      setModalOpen(false);
      fetchFaculty();
    } catch (err) {
      console.error('Save failed:', err);
      const data = err.response?.data;
      if (data) {
        // Format error messages nicely
        const messages = [];
        Object.entries(data).forEach(([key, val]) => {
          const msg = Array.isArray(val) ? val.join(', ') : val;
          messages.push(`${key}: ${msg}`);
        });
        alert(messages.join('\n') || 'Failed to save.');
      } else {
        alert('Failed to save. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  /* ── Delete faculty ──────────────────────────────────────────── */
  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      // Delete user (cascades to faculty profile)
      await api.delete(`/api/auth/faculty/${confirmDelete.id}/`);
      setConfirmDelete(null);
      fetchFaculty();
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Failed to delete faculty member.');
    }
  };

  const columns = [
    {
      key: 'name',
      label: 'Name',
      render: (_, row) => (
        <div>
          <div style={{ fontWeight: 600 }}>{row.user?.first_name} {row.user?.last_name}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>✉️ {row.user?.email}</div>
        </div>
      )
    },
    { key: 'employee_id', label: 'Employee ID', render: (val) => <span className="badge badge-low">{val}</span> },
    { key: 'department', label: 'Department', render: (val) => val },
    { key: 'designation', label: 'Designation', render: (val) => val || 'N/A' },
    { key: 'max_hours_per_week', label: 'Max Hours/Week', render: (val) => <span style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>🕒 {val || 20}h</span> },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="action-btns">
          <button
            className="btn btn-sm btn-danger"
            onClick={(e) => { e.stopPropagation(); setConfirmDelete(row); }}
          >
            Delete
          </button>
        </div>
      )
    },
  ];

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Faculty</h1>
          <p>Manage faculty members and their information. Add, edit, and organize teaching staff.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-faculty" onClick={() => setModalOpen(true)}>+ Add Faculty</button>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)' }}>
            👥
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Faculty</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{faculty.length} faculty members registered</span>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={faculty}
          searchKey="employee_id"
          emptyMessage="No faculty registered yet."
        />
      </div>

      {/* Add Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Add Faculty"
      >
        <AddFacultyForm onSave={handleSave} saving={saving} />
      </Modal>

      {/* Confirm delete */}
      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        message={`Are you sure you want to delete ${confirmDelete?.user?.first_name} ${confirmDelete?.user?.last_name}? This action cannot be undone.`}
      />
    </div>
  );
}
