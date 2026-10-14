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

/* ─── Room Form ────────────────────────────────────────────────── */
function RoomForm({ initial, amenitiesList, onSave, saving }) {
  const [form, setForm] = useState({
    room_number: initial?.room_number || '',
    building: initial?.building || '',
    room_type: initial?.room_type || 'lecture',
    capacity: initial?.capacity || 30,
    amenities: initial?.amenities || [],
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleAmenityChange = (amenityId) => {
    setForm(prev => {
      const isSelected = prev.amenities.includes(amenityId);
      return {
        ...prev,
        amenities: isSelected 
          ? prev.amenities.filter(id => id !== amenityId)
          : [...prev.amenities, amenityId]
      };
    });
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
      <div className="form-group" style={{ marginTop: '1rem' }}>
        <label className="form-label">Amenities</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
          {amenitiesList.map(a => (
            <label key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--color-bg-glass)', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={form.amenities.includes(a.id)}
                onChange={() => handleAmenityChange(a.id)}
              />
              {a.name}
            </label>
          ))}
        </div>
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
  const [amenitiesList, setAmenitiesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [ordering, setOrdering] = useState('room_number');

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  /* Debounce search input */
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  /* Load reference amenities once on mount */
  useEffect(() => {
    api.get('/api/scheduler/amenities/')
      .then(res => setAmenitiesList(res.data.results || res.data || []))
      .catch(() => setAmenitiesList([]));
  }, []);

  /* Fetch rooms with incremental pagination (infinite scroll) */
  const fetchRooms = async ({
    pageNum = page,
    searchQuery = debouncedSearch,
    orderingParam = ordering,
  } = {}) => {
    if (pageNum === 1) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }
    try {
      let url = `/api/scheduler/rooms/?page=${pageNum}`;
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
      if (orderingParam) url += `&ordering=${orderingParam}`;

      const res = await api.get(url);
      const data = res.data;
      const newResults = data.results || (Array.isArray(data) ? data : []);
      const count = data.count !== undefined ? data.count : (Array.isArray(data) ? data.length : newResults.length);

      if (pageNum === 1) {
        setRooms(newResults);
      } else {
        setRooms(prev => {
          const newIds = new Set(newResults.map(r => r.id));
          const filteredPrev = prev.filter(r => !newIds.has(r.id));
          return [...filteredPrev, ...newResults];
        });
      }
      setTotalCount(count);
    } catch (err) {
      console.error('Failed to load rooms:', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchRooms({
      pageNum: page,
      searchQuery: debouncedSearch,
      orderingParam: ordering,
    });
  }, [page, debouncedSearch, ordering]);

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
      setPage(1);
      fetchRooms({ pageNum: 1 });
    } catch (err) {
      console.error('Save failed:', err);
      toast.error(err.response?.data ? JSON.stringify(err.response.data) : 'Failed to save.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await api.delete(`/api/scheduler/rooms/${confirmDelete.id}/`);
      setConfirmDelete(null);
      setPage(1);
      fetchRooms({ pageNum: 1 });
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete. It may be in use by the timetable.');
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
      sortValue: (row) => typeLabels[row.room_type] || row.room_type || '',
      render: (val) => <span className={`badge ${val === 'lab' ? 'badge-present' : 'badge-low'}`}>{typeLabels[val] || val || 'Lecture Hall'}</span>
    },
    { 
      key: 'capacity', 
      label: 'Capacity', 
      sortValue: (row) => Number(row.capacity || 0),
      render: (val) => `👥 ${val}` 
    },
    {
      key: 'equipment',
      label: 'Equipment',
      sortable: false,
      render: (val) => {
        const equips = (val && val.length > 0) ? val : ['projector', 'whiteboard'];
        return (
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            <span className="badge badge-low">{equips[0]}</span>
            {equips.length > 1 && <span className="badge badge-low">{equips[1]}</span>}
            {equips.length > 2 && <span className="badge badge-secondary" style={{ background: 'var(--color-bg-glass)' }}>+{equips.length - 2}</span>}
          </div>
        );
      }
    },
    {
      key: 'amenities',
      label: 'Amenities',
      sortable: false,
      render: (val) => {
        if (!val || val.length === 0) return <span className="badge badge-low">None</span>;
        return (
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {val.map(id => {
              const am = amenitiesList.find(a => a.id === id);
              return <span key={id} className="badge badge-medium">{am ? am.name : id}</span>;
            })}
          </div>
        );
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      sortable: false,
      render: (_, row) => (
        <div className="action-btns">
          <button className="btn btn-sm btn-secondary" onClick={(e) => { e.stopPropagation(); openEdit(row); }}>Edit</button>
          <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); setConfirmDelete(row); }}>Delete</button>
        </div>
      )
    },
  ];

  if (loading && rooms.length === 0) {
    return <div className="loading-spinner"><div className="spinner" /></div>;
  }

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
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
              Showing {rooms.length} of {totalCount} rooms available in the system (infinite scroll enabled)
            </span>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={rooms}
          loading={loading || loadingMore}
          infiniteScroll={true}
          totalCount={totalCount}
          serverPage={page}
          pageSize={100}
          onPageChange={setPage}
          searchValue={search}
          onSearchChange={(val) => {
            setSearch(val);
            setPage(1);
          }}
          defaultSortKey="room_number"
          defaultSortDir="asc"
          onSortChange={({ sortKey, sortDir }) => {
            const backendSortMap = {
              room_number: 'room_number',
              room_type: 'room_type',
              capacity: 'capacity',
            };
            const field = backendSortMap[sortKey];
            if (field) {
              setOrdering(sortDir === 'desc' ? `-${field}` : field);
              setPage(1);
            }
          }}
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
          amenitiesList={amenitiesList}
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
