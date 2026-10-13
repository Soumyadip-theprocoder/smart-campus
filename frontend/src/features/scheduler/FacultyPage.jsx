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

/* ─── Add Faculty Form ─────────────────────────────────────────── */
function AddFacultyForm({ initialData, onSave, saving, departments = [] }) {
  const [form, setForm] = useState({
    first_name: initialData?.user?.first_name || '',
    last_name: initialData?.user?.last_name || '',
    email: initialData?.user?.email || '',
    username: initialData?.user?.username || '',
    password: '',
    employee_id: initialData?.employee_id || '',
    department: initialData?.department || '',
    designation: initialData?.designation || 'Assistant Professor',
    set_as_hod: initialData?.is_hod || false,
  });
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (!initialData) {
      api.get('/auth/faculty/next-id/')
        .then(res => {
          if (res.data?.next_id) {
            setForm(prev => ({ ...prev, employee_id: prev.employee_id || res.data.next_id }));
          }
        })
        .catch(err => console.error('Error fetching next faculty ID', err));
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value, type, checked, selectedOptions } = e.target;
    if (type === 'checkbox') {
      setForm(prev => ({ ...prev, [name]: checked }));
    } else if (type === 'select-multiple') {
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
    if (!form.email || !form.first_name || !form.last_name || !form.employee_id || !form.department) {
      setError('Please fill all required fields.');
      return;
    }
    onSave({
      email: form.email,
      username: form.username,
      password: form.password || undefined,
      first_name: form.first_name,
      last_name: form.last_name,
      role: 'faculty',
      employee_id: form.employee_id,
      department: form.department,
      designation: form.designation,
      is_hod: form.set_as_hod, // for register
      set_as_hod: form.set_as_hod, // for update
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
          <label className="form-label">
            Employee ID * {!initialData && <span style={{ fontSize: '0.8rem', color: 'var(--color-primary)' }}>(Auto-generated)</span>}
          </label>
          <input
            className="form-input"
            name="employee_id"
            value={form.employee_id}
            onChange={handleChange}
            placeholder="e.g. FAC-2026-0001"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Password</label>
          <div style={{ position: 'relative' }}>
            <input
              className="form-input"
              type={showPassword ? "text" : "password"}
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Default: faculty123"
              style={{ width: '100%', paddingRight: '2.5rem' }}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              style={{
                position: 'absolute',
                right: '0.5rem',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--color-text-muted)',
                padding: '0.25rem',
                fontSize: '1.2rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              title={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>
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
            <option value="Lecturer">Lecturer</option>
          </select>
        </div>
      </div>
      <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <input
          type="checkbox"
          id="set_as_hod"
          name="set_as_hod"
          checked={form.set_as_hod}
          onChange={handleChange}
          style={{ width: '1rem', height: '1rem', cursor: 'pointer' }}
          disabled={!form.department}
        />
        <label htmlFor="set_as_hod" style={{ cursor: 'pointer', margin: 0, fontWeight: 500 }}>
          Make this faculty the Head of Department (HOD)
        </label>
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : (initialData ? 'Save Changes' : 'Add Faculty')}
      </button>
    </form>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function FacultyPage() {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingFaculty, setEditingFaculty] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    fetchData(page, search, departmentFilter, roleFilter);
  }, [page, search, departmentFilter, roleFilter]);

  const fetchData = async (pageNum = 1, searchQuery = '', deptFilter = '', rFilter = '') => {
    setLoading(true);
    try {
      let url = `/api/auth/faculty/?page=${pageNum}`;
      if (searchQuery) url += `&search=${searchQuery}`;
      if (deptFilter) url += `&department=${deptFilter}`;
      if (rFilter === 'hod') url += `&is_hod=true`;
      if (rFilter === 'faculty') url += `&is_hod=false`;

      const [facRes, depRes] = await Promise.all([
        api.get(url),
        api.get('/api/scheduler/departments/?all=true')
      ]);
      const newResults = facRes.data.results || facRes.data || [];
      if (pageNum === 1) {
        setFaculty(newResults);
      } else {
        setFaculty(prev => {
          const newIds = new Set(newResults.map(r => r.id));
          const filteredPrev = prev.filter(r => !newIds.has(r.id));
          return [...filteredPrev, ...newResults];
        });
      }
      setTotalCount(facRes.data.count || (facRes.data.results ? facRes.data.results.length : (facRes.data.length || 0)));
      setDepartments(depRes.data.results || depRes.data || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  /* ── Add/Edit faculty via endpoint ───────────────────────── */
  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingFaculty) {
        const payload = { ...formData };
        if (!payload.password) delete payload.password;
        await api.put(`/api/auth/faculty/${editingFaculty.id}/`, payload);
        toast.success('Faculty updated successfully');
      } else {
        if (!formData.password) formData.password = 'faculty123';
        await api.post('/api/auth/register/', formData);
        toast.success('Faculty added successfully');
      }
      setModalOpen(false);
      setEditingFaculty(null);
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

  /* ── Delete faculty ──────────────────────────────────────────── */
  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      // Delete user (cascades to faculty profile)
      await api.delete(`/api/auth/faculty/${confirmDelete.id}/`);
      setConfirmDelete(null);
      fetchData(page, search);
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete faculty member.');
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
      key: 'employee_id',
      label: 'Employee ID',
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
    { key: 'designation', label: 'Designation', render: (val, row) => (
      <span>
        {val || 'N/A'} {row.is_hod && <span className="badge badge-high" style={{marginLeft: '0.5rem'}}>HOD</span>}
      </span>
    ) },
    { key: 'max_hours_per_week', label: 'Max Hours/Week', render: (val) => <span style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>🕒 {val || 20}h</span> },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="action-btns">
          <button
            className="btn btn-sm btn-secondary"
            onClick={(e) => { e.stopPropagation(); setEditingFaculty(row); setModalOpen(true); }}
          >
            Edit
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

  if (loading && faculty.length === 0) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Faculty</h1>
          <p>Manage teaching staff, workload limits, department assignments, and designated heads (HODs).</p>
        </div>
        <button className="btn btn-primary" id="btn-add-faculty" onClick={() => { setEditingFaculty(null); setModalOpen(true); }}>+ Add Faculty</button>
      </div>

      {/* Quick Summary Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)', fontSize: '1.4rem' }}>
            👥
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{totalCount}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Total Faculty</span>
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
          <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: 'var(--color-accent-amber)', fontSize: '1.4rem' }}>
            🎖️
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>
              {faculty.filter(f => f.is_hod).length || departments.filter(d => d.hod).length || 0}
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Heads of Department (HODs)</span>
          </div>
        </div>
      </div>

      {/* Filter Bar with Role Tabs and Department Dropdown */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem', justifyContent: 'space-between' }}>
        <div className="tabs" style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.25rem', margin: 0 }}>
          <button 
            className={`btn btn-sm ${roleFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setRoleFilter(''); }}
          >
            All Faculty
          </button>
          <button 
            className={`btn btn-sm ${roleFilter === 'hod' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setRoleFilter('hod'); }}
          >
            🎖️ HODs Only
          </button>
          <button 
            className={`btn btn-sm ${roleFilter === 'faculty' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setRoleFilter('faculty'); }}
          >
            Faculty Staff
          </button>
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
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)' }}>
            👥
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Faculty</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{totalCount} faculty members registered</span>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={faculty}
          searchKey="employee_id"
          emptyMessage="No faculty registered yet."
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
        onClose={() => { setModalOpen(false); setEditingFaculty(null); }}
        title={editingFaculty ? "Edit Faculty" : "Add Faculty"}
      >
        <AddFacultyForm initialData={editingFaculty} onSave={handleSave} saving={saving} departments={departments} />
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
