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

/* ─── Course / Subject Form ────────────────────────────────────── */
function CourseForm({ initial, faculty, onSave, saving }) {
  const [form, setForm] = useState({
    code: initial?.code || '',
    name: initial?.name || '',
    faculty: initial?.faculty || '',
    credits: initial?.credits || 3,
    required_capacity: initial?.required_capacity || 30,
    sessions_per_week: initial?.sessions_per_week || 3,
    subject_type: initial?.subject_type || 'lecture',
    description: initial?.description || '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      ...form,
      faculty: parseInt(form.faculty),
      credits: parseInt(form.credits),
      required_capacity: parseInt(form.required_capacity),
      sessions_per_week: parseInt(form.sessions_per_week),
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Course Code *</label>
          <input
            className="form-input"
            name="code"
            value={form.code}
            onChange={handleChange}
            placeholder="e.g. CS305"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Credits</label>
          <input
            className="form-input"
            type="number"
            name="credits"
            value={form.credits}
            onChange={handleChange}
            min="1"
            max="10"
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Course Name *</label>
        <input
          className="form-input"
          name="name"
          value={form.name}
          onChange={handleChange}
          placeholder="e.g. Operating Systems"
          required
        />
      </div>
      <div className="form-group">
        <label className="form-label">Faculty *</label>
        <select
          className="form-select"
          name="faculty"
          value={form.faculty}
          onChange={handleChange}
          required
        >
          <option value="">Select faculty member</option>
          {faculty.map((f) => (
            <option key={f.id} value={f.id}>
              {f.user?.first_name} {f.user?.last_name} — {f.department}
            </option>
          ))}
        </select>
      </div>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Type</label>
          <select
            className="form-select"
            name="subject_type"
            value={form.subject_type}
            onChange={handleChange}
          >
            <option value="lecture">Lecture</option>
            <option value="lab">Laboratory</option>
            <option value="seminar">Seminar</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Required Capacity</label>
          <input
            className="form-input"
            type="number"
            name="required_capacity"
            value={form.required_capacity}
            onChange={handleChange}
            min="1"
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Sessions / Week</label>
        <input
          className="form-input"
          type="number"
          name="sessions_per_week"
          value={form.sessions_per_week}
          onChange={handleChange}
          min="1"
          max="7"
        />
      </div>
      <div className="form-group">
        <label className="form-label">Description</label>
        <textarea
          className="form-input"
          name="description"
          value={form.description}
          onChange={handleChange}
          placeholder="Optional course description"
          rows={3}
          style={{ resize: 'vertical' }}
        />
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : initial?.id ? 'Update Course' : 'Add Course'}
      </button>
    </form>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function SubjectsPage() {
  const [subjects, setSubjects] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [subRes, facRes] = await Promise.all([
        api.get('/api/scheduler/subjects/'),
        api.get('/api/auth/faculty/'),
      ]);
      setSubjects(subRes.data.results || subRes.data || []);
      setFaculty(facRes.data.results || facRes.data || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  /* ── CRUD ─────────────────────────────────────────────────────── */
  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingItem?.id) {
        await api.put(`/api/scheduler/subjects/${editingItem.id}/`, formData);
      } else {
        await api.post('/api/scheduler/subjects/', formData);
      }
      setModalOpen(false);
      setEditingItem(null);
      fetchAll();
    } catch (err) {
      console.error('Save failed:', err);
      alert(err.response?.data ? JSON.stringify(err.response.data) : 'Failed to save.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await api.delete(`/api/scheduler/subjects/${confirmDelete.id}/`);
      setConfirmDelete(null);
      fetchAll();
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Failed to delete. It may be in use.');
    }
  };

  const openAdd = () => {
    setEditingItem(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditingItem(item);
    setModalOpen(true);
  };

  const columns = [
    { key: 'code', label: 'Course Code', render: (val) => <span className="badge badge-low">{val}</span> },
    { key: 'name', label: 'Course Name', render: (val) => <strong>{val}</strong> },
    { key: 'faculty_name', label: 'Faculty', render: (val) => val || 'N/A' },
    { key: 'credits', label: 'Credits', render: (val) => <span className="badge badge-low">{val}</span> },
    {
      key: 'subject_type',
      label: 'Type',
      render: (val) => <span className={`badge ${val === 'lab' ? 'badge-present' : 'badge-low'}`}>{val || 'lecture'}</span>
    },
    { key: 'sessions_per_week', label: 'Sessions/Week', render: (val) => <span className="badge badge-medium">{val}</span> },
    { key: 'required_capacity', label: 'Capacity', render: (val) => <span className="badge badge-medium">{val}</span> },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="action-btns">
          <button className="btn btn-sm btn-secondary" onClick={(e) => { e.stopPropagation(); openEdit(row); }}>Edit</button>
          <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); setConfirmDelete(row); }}>Delete</button>
        </div>
      )
    },
  ];

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Courses</h1>
          <p>Manage academic courses and their details. Add, edit, and organize course information efficiently.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-course" onClick={openAdd}>+ Add Course</button>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)' }}>
            📖
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Courses</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{subjects.length} courses registered in the system</span>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={subjects}
          searchKey="name"
          emptyMessage="No courses registered yet."
        />
      </div>

      {/* Add/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingItem(null); }}
        title={editingItem?.id ? 'Edit Course' : 'Add Course'}
      >
        <CourseForm
          initial={editingItem}
          faculty={faculty}
          onSave={handleSave}
          saving={saving}
        />
      </Modal>

      {/* Confirm delete */}
      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        message="Are you sure you want to delete this course? This action cannot be undone."
      />
    </div>
  );
}
