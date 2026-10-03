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

/* ─── Add Group Form ───────────────────────────────────────────── */
function GroupForm({ initialData, onSave, saving }) {
  const [form, setForm] = useState({
    name: initialData?.name || '',
    description: initialData?.description || '',
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
    onSave(form);
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
        <label className="form-label">Description</label>
        <textarea
          className="form-input"
          name="description"
          value={form.description}
          onChange={handleChange}
          placeholder="Optional description"
          rows="3"
        />
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : (initialData ? 'Save Changes' : 'Add Group')}
      </button>
    </form>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function GroupsPage() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/auth/groups/');
      setGroups(response.data.results || response.data || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingGroup) {
        await api.put(`/api/auth/groups/${editingGroup.id}/`, formData);
        toast.success('Group updated successfully');
      } else {
        await api.post('/api/auth/groups/', formData);
        toast.success('Group created successfully');
      }
      setModalOpen(false);
      setEditingGroup(null);
      fetchGroups();
    } catch (err) {
      console.error('Save failed:', err);
      toast.error(err.response?.data?.name?.[0] || 'Failed to save group.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await api.delete(`/api/auth/groups/${confirmDelete.id}/`);
      setConfirmDelete(null);
      toast.success('Group deleted');
      fetchGroups();
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete group.');
    }
  };

  const openEditModal = (group) => {
    setEditingGroup(group);
    setModalOpen(true);
  };

  const openCreateModal = () => {
    setEditingGroup(null);
    setModalOpen(true);
  };

  const columns = [
    {
      key: 'name',
      label: 'Group Name',
      render: (val) => <div style={{ fontWeight: 600 }}>{val}</div>
    },
    { key: 'description', label: 'Description', render: (val) => val || <span style={{ color: 'var(--color-text-muted)' }}>No description</span> },
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
          <h1>Academic Groups</h1>
          <p>Manage flexible groupings for interdisciplinary classes, labs, and student batches.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-group" onClick={openCreateModal}>+ Add Group</button>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <DataTable
          columns={columns}
          data={groups}
          searchKey="name"
          emptyMessage="No groups created yet."
        />
      </div>

      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingGroup(null); }}
        title={editingGroup ? "Edit Group" : "Add Group"}
      >
        <GroupForm 
          initialData={editingGroup} 
          onSave={handleSave} 
          saving={saving} 
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
