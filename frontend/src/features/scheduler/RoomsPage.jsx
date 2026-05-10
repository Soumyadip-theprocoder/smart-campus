import { useState, useEffect } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';

export default function RoomsPage() {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    try {
      const response = await api.get('/api/scheduler/rooms/');
      setRooms(response.data.results || response.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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
      render: (val) => <span className={`badge ${val === 'lab' ? 'badge-present' : 'badge-low'}`}>{val || 'Lecture Hall'}</span> 
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
      key: 'available_days', 
      label: 'Available Days', 
      render: () => (
        <div style={{ display: 'flex', gap: '4px' }}>
          <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc' }}>Mon</span>
          <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc' }}>Tue</span>
          <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc' }}>Wed</span>
        </div>
      )
    },
    { 
      key: 'actions', 
      label: 'Actions', 
      render: () => (
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-sm btn-secondary">Edit</button>
          <button className="btn btn-sm btn-danger">Delete</button>
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
        <button className="btn btn-primary" id="btn-add-room">+ Add Room</button>
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
    </div>
  );
}
