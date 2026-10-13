import toast from 'react-hot-toast';
import { useState, useEffect } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';
import EditMarksForm from '../../components/EditMarksForm';

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

  useEffect(() => {
    if (!initialData) {
      api.get('/auth/students/next-id/')
        .then(res => {
          if (res.data?.next_id) {
            setForm(prev => ({ ...prev, enrollment_number: prev.enrollment_number || res.data.next_id }));
          }
        })
        .catch(err => console.error('Error fetching next student ID', err));
    }
  }, [initialData]);

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
      username: email, // Use email as username to guarantee uniqueness
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
          <label className="form-label">
            Enrollment Number * {!initialData && <span style={{ fontSize: '0.8rem', color: 'var(--color-primary)' }}>(Auto-generated)</span>}
          </label>
          <input
            className="form-input"
            name="enrollment_number"
            value={form.enrollment_number}
            onChange={handleChange}
            placeholder="e.g. STU-2026-0001"
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
            placeholder="Default: student123"
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

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function StudentsPage() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('');

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [editingMarks, setEditingMarks] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    fetchData(page, search, departmentFilter, semesterFilter);
  }, [page, search, departmentFilter, semesterFilter]);

  const fetchData = async (pageNum = 1, searchQuery = '', deptFilter = '', semFilter = '') => {
    setLoading(true);
    try {
      let url = `/api/auth/students/?page=${pageNum}`;
      if (searchQuery) url += `&search=${searchQuery}`;
      if (deptFilter) url += `&department=${deptFilter}`;
      if (semFilter) url += `&semester=${semFilter}`;

      const [stuRes, depRes] = await Promise.all([
        api.get(url),
        api.get('/api/scheduler/departments/?all=true')
      ]);
      const newResults = stuRes.data.results || stuRes.data || [];
      if (pageNum === 1) {
        setStudents(newResults);
      } else {
        setStudents(prev => {
          const newIds = new Set(newResults.map(r => r.id));
          const filteredPrev = prev.filter(r => !newIds.has(r.id));
          return [...filteredPrev, ...newResults];
        });
      }
      setTotalCount(stuRes.data.count || (stuRes.data.results ? stuRes.data.results.length : (stuRes.data.length || 0)));
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
        if (!formData.password) formData.password = 'student123';
        await api.post('/api/auth/register/', formData);
        toast.success('Student added successfully');
      }
      setModalOpen(false);
      setEditingStudent(null);
      fetchData(page, search);
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
      fetchData(page, search);
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
      fetchData(page, search);
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
    {
      key: 'enrollment_number',
      label: 'Enrollment No',
      render: (val) => (
        <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
          {val}
        </span>
      )
    },
    {
      key: 'department',
      label: 'Department',
      render: (val) => {
        const d = departments.find(dep => String(dep.id) === String(val));
        if (!d) return val || 'General';
        return (
          <div>
            {d.dept_id && (
              <span className="badge badge-low" style={{ marginRight: '0.4rem', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                {d.dept_id}
              </span>
            )}
            <span style={{ fontWeight: 500 }}>{d.name}</span>
          </div>
        );
      }
    },
    {
      key: 'semester',
      label: 'Semester',
      render: (val) => (
        <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)', fontWeight: 600 }}>
          Sem {val || '1'}
        </span>
      )
    },
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

  if (loading && students.length === 0) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Students</h1>
          <p>Manage student records, enrollment credentials, academic marks, and department assignments.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-student" onClick={() => { setEditingStudent(null); setModalOpen(true); }}>+ Add Student</button>
      </div>

      {/* Quick Summary Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)', fontSize: '1.4rem' }}>
            👨‍🎓
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{totalCount}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Total Students</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--color-primary)', fontSize: '1.4rem' }}>
            🏛️
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{departments.length}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Active Departments</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)', fontSize: '1.4rem' }}>
            🎓
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>
              {students.filter(s => s.is_ta).length || 0}
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Teaching Assistants (TAs)</span>
          </div>
        </div>
      </div>

      {/* Filter Bar with Department Dropdown and Semester Tabs */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem', justifyContent: 'space-between' }}>
        <div className="tabs" style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.25rem', margin: 0 }}>
          <button 
            className={`btn btn-sm ${semesterFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setSemesterFilter(''); }}
          >
            All Semesters
          </button>
          {[1, 2, 3, 4, 5, 6, 7, 8].map(sem => (
            <button 
              key={sem}
              className={`btn btn-sm ${String(semesterFilter) === String(sem) ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => { setPage(1); setSemesterFilter(String(sem)); }}
            >
              Sem {sem}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <select
            className="form-input"
            style={{ width: 'auto', minWidth: '220px', padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
            value={departmentFilter}
            onChange={(e) => { setPage(1); setDepartmentFilter(e.target.value); }}
          >
            <option value="">-- All Departments --</option>
            {departments.map(d => (
              <option key={d.id} value={d.id}>
                {d.dept_id ? `[${d.dept_id}] ` : ''}{d.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)' }}>
            👨‍🎓
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Students</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{totalCount} students registered</span>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={students}
          searchKey="enrollment_number"
          emptyMessage="No students registered yet."
          infiniteScroll={true}
          totalCount={totalCount}
          serverPage={page}
          onPageChange={setPage}
          onSearchChange={(s) => { setPage(1); setSearch(s); }}
          pageSize={100}
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
