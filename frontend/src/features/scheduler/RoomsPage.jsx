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

/* ─── Room Form ────────────────────────────────────────────────── */
function RoomForm({ initial, onSave, saving }) {
  const [form, setForm] = useState({
    room_number: initial?.room_number || '',
    building: initial?.building || '',
    room_type: initial?.room_type || 'lecture',
    capacity: initial?.capacity || 30,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({ ...form, capacity: parseInt(form.capacity) });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Room Number *</label>
          <input
            className="form-input"
            name="room_number"
            value={form.room_number}
            onChange={handleChange}
            placeholder="e.g. LH-103"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Capacity</label>
          <input
            className="form-input"
            type="number"
            name="capacity"
            value={form.capacity}
            onChange={handleChange}
            min="1"
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Building / Location *</label>
        <input
          className="form-input"
          name="building"
          value={form.building}
          onChange={handleChange}
          placeholder="e.g. Main Block"
          required
        />
      </div>
      <div className="form-group">
        <label className="form-label">Room Type</label>
        <select
          className="form-select"
          name="room_type"
          value={form.room_type}
          onChange={handleChange}
        >
          <option value="lecture">Lecture Hall</option>
          <option value="lab">Laboratory</option>
          <option value="seminar">Seminar Room</option>
        </select>
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : initial?.id ? 'Update Room' : 'Add Room'}
      </button>
    </form>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function RoomsPage() {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/scheduler/rooms/');
      setRooms(response.data.results || response.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  /* ── CRUD ─────────────────────────────────────────────────────── */
  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingItem?.id) {
        await api.put(`/api/scheduler/rooms/${editingItem.id}/`, formData);
      } else {
        await api.post('/api/scheduler/rooms/', formData);
      }
      setModalOpen(false);
      setEditingItem(null);
      fetchRooms();
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
      await api.delete(`/api/scheduler/rooms/${confirmDelete.id}/`);
      setConfirmDelete(null);
      fetchRooms();
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Failed to delete. It may be in use by the timetable.');
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

  const typeLabels = { lecture: 'Lecture Hall', lab: 'Laboratory', seminar: 'Seminar Room' };

  const columns = [
    {
      key: 'room_number',
      label: 'Room Details',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600 }}>{val}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{row.building}</div>
        </div>
      )
    },
    {
      key: 'room_type',
      label: 'Type',
      render: (val) => <span className={`badge ${val === 'lab' ? 'badge-present' : 'badge-low'}`}>{typeLabels[val] || val || 'Lecture Hall'}</span>
    },
    { key: 'capacity', label: 'Capacity', render: (val) => `👥 ${val}` },
    {
      key: 'equipment',
      label: 'Equipment',
      render: (val) => {
        const equips = (val && val.length > 0) ? val : ['projector', 'whiteboard'];
        return (
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            <span className="badge badge-low">{equips[0]}</span>
            {equips.length > 1 && <span className="badge badge-low">{equips[1]}</span>}
            {equips.length > 2 && <span className="badge badge-secondary" style={{ background: 'rgba(255,255,255,0.1)' }}>+{equips.length - 2}</span>}
          </div>
        );
      }
    },
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
          <h1>Rooms</h1>
          <p>Manage classrooms, labs, and other facilities. Add, organize, and track room information.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-room" onClick={openAdd}>+ Add Room</button>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)' }}>
            🏢
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Rooms</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{rooms.length} rooms available in the system</span>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={rooms}
          searchKey="room_number"
          emptyMessage="No rooms registered yet."
        />
      </div>

      {/* Add/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingItem(null); }}
        title={editingItem?.id ? 'Edit Room' : 'Add Room'}
      >
        <RoomForm
          initial={editingItem}
          onSave={handleSave}
          saving={saving}
        />
      </Modal>

      {/* Confirm delete */}
      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        message={`Are you sure you want to delete room "${confirmDelete?.room_number}"? This action cannot be undone.`}
      />
    </div>
  );
}
