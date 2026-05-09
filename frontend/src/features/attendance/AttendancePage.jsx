import { useState, useEffect } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';
import './AttendancePage.css';

export default function AttendancePage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    subject_id: '',
  });

  useEffect(() => {
    loadAttendance();
  }, []);

  const loadAttendance = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.subject_id) params.append('subject_id', filters.subject_id);

      const response = await api.get(`/api/attendance/?${params.toString()}`);
      setRecords(response.data.results || response.data || []);
    } catch (err) {
      console.error('Failed to load attendance:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleApplyFilters = () => {
    loadAttendance();
  };

  const columns = [
    { key: 'enrollment_number', label: 'Enrollment #' },
    { key: 'student_name', label: 'Student' },
    { key: 'subject_code', label: 'Subject' },
    { key: 'date', label: 'Date' },
    {
      key: 'status',
      label: 'Status',
      render: (val) => (
        <span className={`badge badge-${val}`}>
          {val.charAt(0).toUpperCase() + val.slice(1)}
        </span>
      ),
    },
    {
      key: 'method',
      label: 'Method',
      render: (val) => (
        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
          {val === 'face_recognition' ? '🤖 AI' : '✍️ Manual'}
        </span>
      ),
    },
    {
      key: 'marked_at',
      label: 'Marked At',
      render: (val) => new Date(val).toLocaleString(),
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Attendance Records</h1>
        <p>View and manage student attendance data</p>
      </div>

      {/* Filters */}
      <div className="glass-card attendance-filters animate-fade-in-up" style={{ opacity: 0 }}>
        <div className="filters-row">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">From Date</label>
            <input
              type="date"
              className="form-input"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              id="filter-date-from"
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">To Date</label>
            <input
              type="date"
              className="form-input"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              id="filter-date-to"
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button
              className="btn btn-primary"
              onClick={handleApplyFilters}
              id="btn-apply-filters"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      {/* Records Table */}
      <div className="glass-card animate-fade-in-up stagger-2" style={{ opacity: 0, marginTop: '1.5rem', padding: '1.5rem' }}>
        {loading ? (
          <div className="loading-spinner"><div className="spinner" /></div>
        ) : (
          <DataTable
            columns={columns}
            data={records}
            emptyMessage="No attendance records found. Adjust your filters or mark attendance first."
          />
        )}
      </div>
    </div>
  );
}
