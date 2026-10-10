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
    name: initialData?.name || '',
    no_of_years: initialData?.no_of_years || 4,
    hod: initialData?.hod || '',
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name) {
      setError('Please provide a group name.');
      return;
    }
    const submitData = { ...form };
    if (!submitData.hod) {
      submitData.hod = null;
    }
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
        <label className="form-label">Name *</label>
        <input
          className="form-input"
          name="name"
          value={form.name}
          onChange={handleChange}
          placeholder="e.g. Section A, Machine Learning Enthusiasts"
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
        >
          <option value="">-- Select HOD (Optional) --</option>
          {faculties?.map(f => (
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

  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    setLoading(true);
    try {
      const [depRes, facRes] = await Promise.all([
        api.get('/api/scheduler/departments/'),
        api.get('/api/auth/faculty/')
      ]);
      setDepartments(depRes.data.results || depRes.data || []);
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
      fetchDepartments();
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
      fetchDepartments();
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
      key: 'name',
      label: 'Department Name',
      render: (val) => <div style={{ fontWeight: 600 }}>{val}</div>
    },
    {
      key: 'no_of_years',
      label: 'Program Years',
      render: (val) => val || '-'
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

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Departments</h1>
          <p>Manage flexible groupings for interdisciplinary classes, labs, and student batches.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-department" onClick={openCreateModal}>+ Add Department</button>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <DataTable
          columns={columns}
          data={departments}
          searchKey="name"
          emptyMessage="No departments created yet."
        />
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
