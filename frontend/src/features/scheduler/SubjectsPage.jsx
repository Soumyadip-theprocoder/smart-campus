import { useState, useEffect } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubjects();
  }, []);

  const fetchSubjects = async () => {
    try {
      const response = await api.get('/api/scheduler/subjects/');
      setSubjects(response.data.results || response.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { key: 'code', label: 'Course Code', render: (val) => <span className="badge badge-low">{val}</span> },
    { key: 'name', label: 'Course Name', render: (val) => <strong>{val}</strong> },
    { key: 'department', label: 'Department', render: () => 'Computer Science' },
    { key: 'credits', label: 'Credits', render: (val) => <span className="badge badge-low">{val}</span> },
    { 
      key: 'subject_type', 
      label: 'Type', 
      render: (val) => <span className={`badge ${val === 'lab' ? 'badge-present' : 'badge-low'}`}>{val || 'lecture'}</span> 
    },
    { key: 'sessions_per_week', label: 'Hours per Week', render: (val) => <span className="badge badge-medium">{val}</span> },
    { key: 'semester', label: 'Semester', render: () => <span className="badge badge-medium">Sem 1</span> },
    { key: 'year', label: 'Year', render: () => <span className="badge" style={{ background: 'rgba(236, 72, 153, 0.15)', color: 'var(--color-accent-pink)' }}>2025</span> },
    { key: 'prereq', label: 'Prereq', render: () => <span style={{ color: 'var(--color-text-muted)' }}>None</span> },
  ];

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Courses</h1>
          <p>Manage academic courses and their details. Add, edit, and organize course information efficiently.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-course">+ Add Course</button>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)' }}>
            📖
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Courses</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{subjects.length} courses registered in the system</span>
          </div>
        </div>

        <DataTable 
          columns={columns} 
          data={subjects} 
          searchKey="name"
          emptyMessage="No courses registered yet."
        />
      </div>
    </div>
  );
}
