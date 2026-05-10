import { useState, useEffect } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';

export default function FacultyPage() {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFaculty();
  }, []);

  const fetchFaculty = async () => {
    try {
      const response = await api.get('/api/accounts/faculty/');
      setFaculty(response.data.results || response.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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
    { key: 'department', label: 'Department', render: (val) => val },
    { key: 'designation', label: 'Designation', render: (val) => val || 'N/A' },
    { 
      key: 'specialization', 
      label: 'Specialization', 
      render: (_, row) => (
        <span className="badge badge-present">
          {row.department === 'Computer Science' ? 'Database management system' : 'Operating Systems'}
        </span>
      ) 
    },
    { key: 'max_hours_per_week', label: 'Max Hours/Week', render: (val) => <span style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>🕒 {val || 20}h</span> },
    { 
      key: 'availability', 
      label: 'Availability', 
      render: () => (
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
          <span style={{ color: 'var(--color-accent-blue-light)' }}>Monday:</span> 08:00-17:30<br />
          <span style={{ color: 'var(--color-accent-blue-light)' }}>Tuesday:</span> 08:30-17:41<br />
          <span style={{ color: 'var(--color-accent-blue-light)' }}>Wednesday:</span> 09:40-15:41
        </div>
      ) 
    },
  ];

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Faculty</h1>
          <p>Manage faculty members and their information. Add, edit, and organize teaching staff.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-faculty">+ Add Faculty</button>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)' }}>
            👥
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Faculty</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{faculty.length} faculty members registered</span>
          </div>
        </div>

        <DataTable 
          columns={columns} 
          data={faculty} 
          searchKey="employee_id"
          emptyMessage="No faculty registered yet."
        />
      </div>
    </div>
  );
}
