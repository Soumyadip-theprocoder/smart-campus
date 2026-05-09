import { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import './ManageTimetablePage.css';

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

/* ─── Confirmation dialog ──────────────────────────────────────── */
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

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function ManageTimetablePage() {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('subjects');

  /* Shared state */
  const [subjects, setSubjects] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [timeslots, setTimeslots] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  /* ── Load all data ──────────────────────────────────────────────── */
  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [subRes, roomRes, tsRes, facRes] = await Promise.all([
        api.get('/api/scheduler/subjects/'),
        api.get('/api/scheduler/rooms/'),
        api.get('/api/scheduler/timeslots/'),
        api.get('/api/auth/faculty/'),
      ]);
      setSubjects(subRes.data.results || subRes.data || []);
      setRooms(roomRes.data.results || roomRes.data || []);
      setTimeslots(tsRes.data.results || tsRes.data || []);
      setFaculty(facRes.data.results || facRes.data || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  /* ── CRUD helpers ───────────────────────────────────────────────── */
  const getEndpoint = (tab) => {
    const map = { subjects: 'subjects', rooms: 'rooms', timeslots: 'timeslots' };
    return `/api/scheduler/${map[tab]}`;
  };

  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingItem?.id) {
        await api.put(`${getEndpoint(activeTab)}/${editingItem.id}/`, formData);
      } else {
        await api.post(`${getEndpoint(activeTab)}/`, formData);
      }
      setModalOpen(false);
      setEditingItem(null);
      loadAll();
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
      await api.delete(`${getEndpoint(activeTab)}/${confirmDelete.id}/`);
      setConfirmDelete(null);
      loadAll();
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

  /* ── Tabs ───────────────────────────────────────────────────────── */
  const tabs = [
    { key: 'subjects', label: 'Subjects', icon: '📚', count: subjects.length },
    { key: 'rooms', label: 'Rooms & Locations', icon: '🏛️', count: rooms.length },
    { key: 'timeslots', label: 'Time Slots', icon: '🕒', count: timeslots.length },
  ];

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Manage Timetable Resources</h1>
          <p>Add and manage subjects, rooms, and time slots used in scheduling</p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={openAdd} id="btn-add-resource">
            + Add {activeTab === 'subjects' ? 'Subject' : activeTab === 'rooms' ? 'Room' : 'Time Slot'}
          </button>
        )}
      </div>

      {/* Tab bar */}
      <div className="manage-tabs animate-fade-in-up" style={{ opacity: 0 }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`manage-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
            id={`tab-${tab.key}`}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
            <span className="tab-count">{tab.count}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="glass-card animate-fade-in-up stagger-2" style={{ opacity: 0, padding: 0, overflow: 'hidden' }}>
        {activeTab === 'subjects' && (
          <SubjectsTable
            subjects={subjects}
            onEdit={openEdit}
            onDelete={setConfirmDelete}
            isAdmin={isAdmin}
          />
        )}
        {activeTab === 'rooms' && (
          <RoomsTable
            rooms={rooms}
            onEdit={openEdit}
            onDelete={setConfirmDelete}
            isAdmin={isAdmin}
          />
        )}
        {activeTab === 'timeslots' && (
          <TimeSlotsTable
            timeslots={timeslots}
            onEdit={openEdit}
            onDelete={setConfirmDelete}
            isAdmin={isAdmin}
          />
        )}
      </div>

      {/* Add/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingItem(null); }}
        title={editingItem?.id
          ? `Edit ${activeTab === 'subjects' ? 'Subject' : activeTab === 'rooms' ? 'Room' : 'Time Slot'}`
          : `Add ${activeTab === 'subjects' ? 'Subject' : activeTab === 'rooms' ? 'Room' : 'Time Slot'}`
        }
      >
        {activeTab === 'subjects' && (
          <SubjectForm
            initial={editingItem}
            faculty={faculty}
            onSave={handleSave}
            saving={saving}
          />
        )}
        {activeTab === 'rooms' && (
          <RoomForm initial={editingItem} onSave={handleSave} saving={saving} />
        )}
        {activeTab === 'timeslots' && (
          <TimeSlotForm initial={editingItem} onSave={handleSave} saving={saving} />
        )}
      </Modal>

      {/* Confirm delete */}
      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        message={`Are you sure you want to delete this? This action cannot be undone.`}
      />
    </div>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Table Components
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

function SubjectsTable({ subjects, onEdit, onDelete, isAdmin }) {
  if (subjects.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📚</div>
        <h3>No Subjects Added</h3>
        <p>Add subjects to start building your timetable.</p>
      </div>
    );
  }

  return (
    <div className="data-table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Faculty</th>
            <th>Credits</th>
            <th>Capacity</th>
            <th>Sessions/Week</th>
            {isAdmin && <th style={{ textAlign: 'right' }}>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {subjects.map((s) => (
            <tr key={s.id}>
              <td>
                <span className="code-badge">{s.code}</span>
              </td>
              <td style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>{s.name}</td>
              <td>{s.faculty_name}</td>
              <td><span className="num-pill">{s.credits}</span></td>
              <td><span className="num-pill">{s.required_capacity}</span></td>
              <td><span className="num-pill">{s.sessions_per_week}</span></td>
              {isAdmin && (
                <td style={{ textAlign: 'right' }}>
                  <div className="action-btns">
                    <button className="btn btn-sm btn-secondary" onClick={() => onEdit(s)}>Edit</button>
                    <button className="btn btn-sm btn-danger" onClick={() => onDelete(s)}>Delete</button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RoomsTable({ rooms, onEdit, onDelete, isAdmin }) {
  const typeLabels = { lecture: 'Lecture Hall', lab: 'Laboratory', seminar: 'Seminar Room' };
  const typeColors = {
    lecture: 'var(--gradient-primary)',
    lab: 'var(--gradient-emerald)',
    seminar: 'var(--gradient-pink)',
  };

  if (rooms.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🏛️</div>
        <h3>No Rooms Added</h3>
        <p>Add rooms and locations to start building your timetable.</p>
      </div>
    );
  }

  return (
    <div className="data-table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Room Number</th>
            <th>Building / Location</th>
            <th>Type</th>
            <th>Capacity</th>
            {isAdmin && <th style={{ textAlign: 'right' }}>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {rooms.map((r) => (
            <tr key={r.id}>
              <td>
                <span className="code-badge">{r.room_number}</span>
              </td>
              <td style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>
                <span className="building-label">📍 {r.building}</span>
              </td>
              <td>
                <span className="type-badge" style={{ background: typeColors[r.room_type] }}>
                  {typeLabels[r.room_type] || r.room_type}
                </span>
              </td>
              <td><span className="num-pill">{r.capacity} seats</span></td>
              {isAdmin && (
                <td style={{ textAlign: 'right' }}>
                  <div className="action-btns">
                    <button className="btn btn-sm btn-secondary" onClick={() => onEdit(r)}>Edit</button>
                    <button className="btn btn-sm btn-danger" onClick={() => onDelete(r)}>Delete</button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TimeSlotsTable({ timeslots, onEdit, onDelete, isAdmin }) {
  const dayLabels = {
    MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday',
    THU: 'Thursday', FRI: 'Friday', SAT: 'Saturday',
  };
  const dayColors = {
    MON: '#3b82f6', TUE: '#10b981', WED: '#f59e0b',
    THU: '#8b5cf6', FRI: '#ec4899', SAT: '#06b6d4',
  };

  if (timeslots.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🕒</div>
        <h3>No Time Slots</h3>
        <p>Define time slots for scheduling classes.</p>
      </div>
    );
  }

  /* Group by day */
  const grouped = {};
  timeslots.forEach((ts) => {
    const day = ts.day;
    if (!grouped[day]) grouped[day] = [];
    grouped[day].push(ts);
  });

  return (
    <div className="timeslot-groups">
      {Object.entries(grouped).map(([day, slots]) => (
        <div className="timeslot-day-group" key={day}>
          <div className="day-header">
            <span className="day-dot" style={{ background: dayColors[day] }} />
            <span className="day-label">{dayLabels[day] || day}</span>
            <span className="day-count">{slots.length} slots</span>
          </div>
          <div className="slot-cards">
            {slots.map((ts) => (
              <div className="slot-card" key={ts.id}>
                <div className="slot-time">
                  {ts.start_time?.substring(0, 5)} — {ts.end_time?.substring(0, 5)}
                </div>
                {isAdmin && (
                  <div className="action-btns">
                    <button className="btn-icon" onClick={() => onEdit(ts)} title="Edit">✏️</button>
                    <button className="btn-icon btn-icon-danger" onClick={() => onDelete(ts)} title="Delete">🗑️</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Form Components
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

function SubjectForm({ initial, faculty, onSave, saving }) {
  const [form, setForm] = useState({
    code: initial?.code || '',
    name: initial?.name || '',
    faculty: initial?.faculty || '',
    credits: initial?.credits || 3,
    required_capacity: initial?.required_capacity || 30,
    sessions_per_week: initial?.sessions_per_week || 3,
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
          <label className="form-label">Subject Code *</label>
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
        <label className="form-label">Subject Name *</label>
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
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : initial?.id ? 'Update Subject' : 'Add Subject'}
      </button>
    </form>
  );
}

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

function TimeSlotForm({ initial, onSave, saving }) {
  const [form, setForm] = useState({
    day: initial?.day || 'MON',
    start_time: initial?.start_time?.substring(0, 5) || '09:00',
    end_time: initial?.end_time?.substring(0, 5) || '10:00',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label">Day *</label>
        <select
          className="form-select"
          name="day"
          value={form.day}
          onChange={handleChange}
          required
        >
          <option value="MON">Monday</option>
          <option value="TUE">Tuesday</option>
          <option value="WED">Wednesday</option>
          <option value="THU">Thursday</option>
          <option value="FRI">Friday</option>
          <option value="SAT">Saturday</option>
        </select>
      </div>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Start Time *</label>
          <input
            className="form-input"
            type="time"
            name="start_time"
            value={form.start_time}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">End Time *</label>
          <input
            className="form-input"
            type="time"
            name="end_time"
            value={form.end_time}
            onChange={handleChange}
            required
          />
        </div>
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : initial?.id ? 'Update Time Slot' : 'Add Time Slot'}
      </button>
    </form>
  );
}
