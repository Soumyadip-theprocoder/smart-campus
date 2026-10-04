import toast from 'react-hot-toast';
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

/* ─── Add Student Form ─────────────────────────────────────────── */
function AddStudentForm({ initialData, onSave, saving, departments = [] }) {
  const [form, setForm] = useState({
    first_name: initialData?.user?.first_name || '',
    last_name: initialData?.user?.last_name || '',
    email: initialData?.user?.email || '',
    username: initialData?.user?.username || '',
    password: '',
    enrollment_number: initialData?.enrollment_number || '',
    department: initialData?.department || '',
    semester: initialData?.semester || 1,
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, selectedOptions } = e.target;
    if (type === 'select-multiple') {
      const values = Array.from(selectedOptions, option => option.value);
      setForm(prev => ({ ...prev, [name]: values }));
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
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
    if (!form.email || !form.first_name || !form.last_name || !form.enrollment_number || !form.department) {
      setError('Please fill all required fields.');
      return;
    }

    onSave({
      email: form.email,
      username: form.username,
      password: form.password || undefined,
      first_name: form.first_name,
      last_name: form.last_name,
      role: 'student',
      enrollment_number: form.enrollment_number,
      department: form.department,
      semester: parseInt(form.semester) || 1,
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
          placeholder="e.g. john.doe@student.edu"
          required
        />
      </div>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Enrollment Number *</label>
          <input
            className="form-input"
            name="enrollment_number"
            value={form.enrollment_number}
            onChange={handleChange}
            placeholder="e.g. STU-001"
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
          <select
            className="form-select"
            name="department"
            value={form.department}
            onChange={handleChange}
            required
          >
            <option value="">Select a department...</option>
            {departments.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Semester</label>
          <input
            className="form-input"
            type="number"
            min="1"
            max="10"
            name="semester"
            value={form.semester}
            onChange={handleChange}
          />
        </div>
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : (initialData ? 'Save Changes' : 'Add Student')}
      </button>
    </form>
  );
}

/* ─── Edit Marks Form ─────────────────────────────────────────── */
function EditMarksForm({ initialData, onSave, saving }) {
  const [form, setForm] = useState({
    marks_10th: initialData?.marks_10th || '',
    marks_12th: initialData?.marks_12th || '',
    cgpa_semesters: initialData?.cgpa_semesters || {},
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleCgpaChange = (sem, value) => {
    setForm((prev) => ({
      ...prev,
      cgpa_semesters: {
        ...prev.cgpa_semesters,
        [sem]: value
      }
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    let parsedCgpa = { ...form.cgpa_semesters };
    const maxSem = (parseInt(initialData?.semester) || 1) - 1;
    
    // Clean up CGPA object: remove empty values and semesters >= current
    Object.keys(parsedCgpa).forEach(key => {
      if (parseInt(key) > maxSem || !parsedCgpa[key]) {
        delete parsedCgpa[key];
      } else {
        parsedCgpa[key] = parseFloat(parsedCgpa[key]);
      }
    });

    onSave({
      marks_10th: form.marks_10th ? parseFloat(form.marks_10th) : null,
      marks_12th: form.marks_12th ? parseFloat(form.marks_12th) : null,
      cgpa_semesters: parsedCgpa,
    });
  };

  const semesterCount = parseInt(initialData?.semester) || 1;

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">10th Marks (%)</label>
          <input
            className="form-input"
            type="number"
            step="0.01"
            name="marks_10th"
            value={form.marks_10th}
            onChange={handleChange}
            placeholder="e.g. 85.50"
          />
        </div>
        <div className="form-group">
          <label className="form-label">12th Marks (%)</label>
          <input
            className="form-input"
            type="number"
            step="0.01"
            name="marks_12th"
            value={form.marks_12th}
            onChange={handleChange}
            placeholder="e.g. 90.00"
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Semester-wise CGPA</label>
        {semesterCount > 1 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '0.75rem', marginTop: '0.5rem' }}>
            {Array.from({ length: semesterCount - 1 }, (_, i) => i + 1).map(sem => (
              <div key={sem}>
                <label style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem', display: 'block' }}>
                  Sem {sem} CGPA
                </label>
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  min="0"
                  max="10"
                  value={form.cgpa_semesters[sem] || ''}
                  onChange={(e) => handleCgpaChange(sem, e.target.value)}
                  placeholder="e.g. 8.5"
                />
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontStyle: 'italic', padding: '0.5rem 0' }}>
            N/A (Student is in 1st semester)
          </div>
        )}
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : 'Save Marks'}
      </button>
    </form>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function StudentsPage() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [editingMarks, setEditingMarks] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [stuRes, depRes] = await Promise.all([
        api.get('/api/auth/students/'),
        api.get('/api/scheduler/departments/')
      ]);
      setStudents(stuRes.data.results || stuRes.data || []);
      setDepartments(depRes.data.results || depRes.data || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  /* ── Add/Edit student via endpoint ───────────────────────── */
  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingStudent) {
        const payload = { ...formData };
        if (!payload.password) delete payload.password;
        await api.patch(`/api/auth/students/${editingStudent.id}/`, payload);
        toast.success('Student updated successfully');
      } else {
        if (!formData.password) formData.password = 'campus@123';
        await api.post('/api/auth/register/', formData);
        toast.success('Student added successfully');
      }
      setModalOpen(false);
      setEditingStudent(null);
      fetchData();
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
        toast.error(messages.join('\n') || 'Failed to save.');
      } else {
        toast.error('Failed to save. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMarks = async (marksData) => {
    setSaving(true);
    try {
      await api.patch(`/api/auth/students/${editingMarks.id}/`, marksData);
      toast.success('Marks updated successfully');
      setEditingMarks(null);
      fetchData();
    } catch (err) {
      console.error('Save failed:', err);
      toast.error('Failed to save marks. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  /* ── Delete student ──────────────────────────────────────────── */
  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      // Delete user (cascades to student profile)
      await api.delete(`/api/auth/students/${confirmDelete.id}/`);
      setConfirmDelete(null);
      fetchData();
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete student.');
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
    { key: 'enrollment_number', label: 'Enrollment No', render: (val) => <span className="badge badge-low">{val}</span> },
    { key: 'department', label: 'Department', render: (val, row) => departments.find(d => d.id === val)?.name || val },
    { key: 'semester', label: 'Semester', render: (val) => val || 'N/A' },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="action-btns">
          <button
            className="btn btn-sm btn-secondary"
            onClick={(e) => { e.stopPropagation(); setEditingStudent(row); setModalOpen(true); }}
          >
            Edit
          </button>
          <button
            className="btn btn-sm btn-secondary"
            onClick={(e) => { e.stopPropagation(); setEditingMarks(row); }}
          >
            Marks
          </button>
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
          <h1>Students</h1>
          <p>Manage student records. Add, edit, and organize students.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-student" onClick={() => { setEditingStudent(null); setModalOpen(true); }}>+ Add Student</button>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)' }}>
            👨‍🎓
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Students</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{students.length} students registered</span>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={students}
          searchKey="enrollment_number"
          emptyMessage="No students registered yet."
        />
      </div>

      {/* Add/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingStudent(null); }}
        title={editingStudent ? "Edit Student" : "Add Student"}
      >
        <AddStudentForm initialData={editingStudent} onSave={handleSave} saving={saving} departments={departments} />
      </Modal>

      {/* Edit Marks Modal */}
      <Modal
        open={!!editingMarks}
        onClose={() => setEditingMarks(null)}
        title={`Edit Marks - ${editingMarks?.user?.first_name} ${editingMarks?.user?.last_name}`}
      >
        {editingMarks && <EditMarksForm initialData={editingMarks} onSave={handleSaveMarks} saving={saving} />}
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
