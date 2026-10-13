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

/* ─── Add Department Form ───────────────────────────────────────────── */
function DepartmentForm({ initialData, onSave, saving, faculties }) {
  const [form, setForm] = useState({
    dept_id: initialData?.dept_id || '',
    program_type: initialData?.program_type || '',
    core_department: initialData?.core_department || '',
    no_of_years: initialData?.no_of_years || 4,
    hod: initialData?.hod || '',
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (!initialData) {
      api.get('/scheduler/departments/next-id/')
        .then(res => {
          if (res.data?.next_id) {
            setForm(prev => ({ ...prev, dept_id: prev.dept_id || res.data.next_id }));
          }
        })
        .catch(err => console.error('Error fetching next department ID', err));
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.core_department) {
      setError('Please provide a core department name.');
      return;
    }
    const submitData = { ...form };
    if (!submitData.hod) {
      submitData.hod = null;
    }
    if (!submitData.dept_id) {
      delete submitData.dept_id;
    }
    
    // Maintain the unique 'name' field for backward compatibility
    submitData.name = submitData.program_type 
      ? `${submitData.program_type} in ${submitData.core_department}`
      : submitData.core_department;
      
    onSave(submitData);
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
      <div className="form-group">
        <label className="form-label">
          Department ID {!initialData && <span style={{ fontSize: '0.8rem', color: 'var(--color-primary)' }}>(Auto-generated)</span>}
        </label>
        <input
          className="form-input"
          name="dept_id"
          value={form.dept_id}
          onChange={handleChange}
          placeholder="e.g. DEP-0001"
        />
      </div>
      <div className="form-group">
        <label className="form-label">Degree / Program Type</label>
        <select
          className="form-input"
          name="program_type"
          value={form.program_type}
          onChange={handleChange}
        >
          <option value="">-- None (e.g. Core Dept) --</option>
          <option value="B.Sc">B.Sc</option>
          <option value="M.Sc">M.Sc</option>
          <option value="B.Tech">B.Tech</option>
          <option value="M.Tech">M.Tech</option>
          <option value="BBA">BBA</option>
          <option value="MBA">MBA</option>
          <option value="BCA">BCA</option>
          <option value="MCA">MCA</option>
          <option value="B.A.">B.A.</option>
          <option value="M.A.">M.A.</option>
          <option value="Ph.D">Ph.D</option>
        </select>
      </div>
      <div className="form-group">
        <label className="form-label">Department Discipline *</label>
        <input
          className="form-input"
          name="core_department"
          value={form.core_department}
          onChange={handleChange}
          placeholder="e.g. Civil, Mechanical, Computer Science"
          required
        />
      </div>
      <div className="form-group">
        <label className="form-label">Program Years</label>
        <input
          type="number"
          className="form-input"
          name="no_of_years"
          value={form.no_of_years}
          onChange={handleChange}
          min="1"
          required
        />
      </div>
      <div className="form-group">
        <label className="form-label">Head of Department</label>
        <select
          className="form-input"
          name="hod"
          value={form.hod || ''}
          onChange={handleChange}
          disabled={!initialData || !faculties?.some(f => f.department === initialData.id)}
        >
          <option value="">
            {!initialData 
              ? "-- Save department first to add HOD --" 
              : !faculties?.some(f => f.department === initialData.id)
                ? "-- No faculty in this department --"
                : "-- Select HOD (Optional) --"}
          </option>
          {faculties
            ?.filter(f => initialData ? f.department === initialData.id : false)
            .map(f => (
            <option key={f.id} value={f.id}>
              {f.user?.first_name} {f.user?.last_name} ({f.employee_id})
            </option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : (initialData ? 'Save Changes' : 'Add Department')}
      </button>
    </form>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function DepartmentsPage() {
  const [departments, setDepartments] = useState([]);
  const [faculties, setFaculties] = useState([]);
  const [loading, setLoading] = useState(true);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  
  const [programFilter, setProgramFilter] = useState('');

  // Fetch unique program types for the tabs (in a real app, might come from an endpoint)
  const availablePrograms = ['B.Sc', 'M.Sc', 'B.Tech', 'M.Tech', 'BBA', 'MBA', 'BCA', 'MCA', 'B.A.', 'M.A.', 'Ph.D'];

  useEffect(() => {
    fetchDepartments(page, search, programFilter);
  }, [page, search, programFilter]);

  const fetchDepartments = async (pageNum = 1, searchQuery = '', pFilter = '') => {
    setLoading(true);
    try {
      let url = `/api/scheduler/departments/?page=${pageNum}`;
      if (searchQuery) url += `&search=${searchQuery}`;
      if (pFilter) url += `&program_type=${pFilter}`;
      
      const [depRes, facRes] = await Promise.all([
        api.get(url),
        api.get('/api/auth/faculty/?all=true')
      ]);
      const newResults = depRes.data.results || depRes.data || [];
      if (pageNum === 1) {
        setDepartments(newResults);
      } else {
        setDepartments(prev => {
          const newIds = new Set(newResults.map(r => r.id));
          const filteredPrev = prev.filter(r => !newIds.has(r.id));
          return [...filteredPrev, ...newResults];
        });
      }
      setTotalCount(depRes.data.count || (depRes.data.results ? depRes.data.results.length : (depRes.data.length || 0)));
      setFaculties(facRes.data.results || facRes.data || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load departments');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingDepartment) {
        await api.put(`/api/scheduler/departments/${editingDepartment.id}/`, formData);
        toast.success('Department updated successfully');
      } else {
        await api.post('/api/scheduler/departments/', formData);
        toast.success('Department created successfully');
      }
      setModalOpen(false);
      setEditingDepartment(null);
      fetchDepartments(page, search, programFilter);
    } catch (err) {
      console.error('Save failed:', err);
      toast.error(err.response?.data?.name?.[0] || 'Failed to save department.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await api.delete(`/api/scheduler/departments/${confirmDelete.id}/`);
      setConfirmDelete(null);
      toast.success('Department deleted');
      fetchDepartments(page, search, programFilter);
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete department.');
    }
  };

  const openEditModal = (department) => {
    setEditingDepartment(department);
    setModalOpen(true);
  };

  const openCreateModal = () => {
    setEditingDepartment(null);
    setModalOpen(true);
  };

  const columns = [
    {
      key: 'dept_id',
      label: 'Dept ID',
      render: (val) => val ? (
        <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
          {val}
        </span>
      ) : '-'
    },
    {
      key: 'program_type',
      label: 'Degree',
      render: (val) => val ? <span className="badge" style={{ backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary-dark)' }}>{val}</span> : <span style={{color:'var(--color-text-tertiary)'}}>General</span>
    },
    {
      key: 'core_department',
      label: 'Department',
      render: (val, row) => <div style={{ fontWeight: 600, fontSize: '1.05rem' }}>{val || row.name}</div>
    },
    {
      key: 'no_of_years',
      label: 'Program Years',
      render: (val) => val || '-'
    },
    {
      key: 'faculty_count',
      label: 'Faculty',
      render: (val) => <span className="badge badge-low">👥 {val || 0}</span>
    },
    {
      key: 'student_count',
      label: 'Students',
      render: (val) => <span className="badge badge-medium">👨‍🎓 {val || 0}</span>
    },
    {
      key: 'hod',
      label: 'Head of Dept',
      render: (val) => {
        const hod = faculties.find(f => f.id === val);
        return hod ? `${hod.user?.first_name} ${hod.user?.last_name}` : '-';
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="action-btns">
          <button
            className="btn btn-sm btn-secondary"
            onClick={(e) => { e.stopPropagation(); openEditModal(row); }}
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

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Departments</h1>
          <p>Manage academic departments, degree programs, and head of department assignments.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-department" onClick={openCreateModal}>+ Add Department</button>
      </div>

      {/* Quick Summary Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--color-primary)', fontSize: '1.4rem' }}>
            🏛️
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{totalCount}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Total Departments</span>
          </div>
        </div>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)', fontSize: '1.4rem' }}>
            👥
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{faculties.length}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Total Faculty</span>
          </div>
        </div>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)', fontSize: '1.4rem' }}>
            👨‍🎓
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>
              {departments.reduce((sum, d) => sum + (d.student_count || 0), 0)}
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Enrolled Students</span>
          </div>
        </div>
      </div>

      <div className="tabs" style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
        <button 
          className={`btn btn-sm ${programFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => { setPage(1); setProgramFilter(''); }}
        >
          All Degrees
        </button>
        {availablePrograms.map(prog => (
          <button 
            key={prog}
            className={`btn btn-sm ${programFilter === prog ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setProgramFilter(prog); }}
          >
            {prog}
          </button>
        ))}
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--color-primary)' }}>
            🏛️
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Departments</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{totalCount} academic departments registered</span>
          </div>
        </div>
        {loading && departments.length === 0 ? (
           <div className="loading-spinner" style={{ margin: '3rem auto' }}><div className="spinner" /></div>
        ) : (
          <DataTable
            columns={columns}
            data={departments}
            searchKey="name"
            emptyMessage={programFilter ? `No ${programFilter} departments found.` : "No departments created yet."}
            infiniteScroll={true}
            totalCount={totalCount}
            serverPage={page}
            onPageChange={setPage}
            onSearchChange={(s) => { setPage(1); setSearch(s); }}
            pageSize={100}
          />
        )}
      </div>

      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingDepartment(null); }}
        title={editingDepartment ? "Edit Department" : "Add Department"}
      >
        <DepartmentForm 
          initialData={editingDepartment} 
          onSave={handleSave} 
          saving={saving} 
          faculties={faculties}
        />
      </Modal>

      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        message={`Are you sure you want to delete ${confirmDelete?.name}?`}
      />
    </div>
  );
}
