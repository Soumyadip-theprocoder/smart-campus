import { useState, useEffect, useRef } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';
import QRCodeGenerator from './QRCodeGenerator';
import './AttendancePage.css';

export default function AttendancePage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showScanner, setShowScanner] = useState(false);
  const [showQRGenerator, setShowQRGenerator] = useState(false);
  const [scanning, setScanning] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    subject_id: '',
  });
  const [subjects, setSubjects] = useState([]);

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

      const [attRes, subRes] = await Promise.all([
        api.get(`/api/attendance/?${params.toString()}`),
        api.get('/api/scheduler/subjects/')
      ]);
      setRecords(attRes.data.results || attRes.data || []);
      setSubjects(subRes.data.results || subRes.data || []);
    } catch (err) {
      console.error('Failed to load data:', err);
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

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Camera access denied:", err);
      alert("Could not access camera. Please allow permissions.");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  // Setup/teardown camera when scanner modal opens/closes
  useEffect(() => {
    if (showScanner) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera(); // Cleanup on unmount
  }, [showScanner]);

  const handleRunScan = async () => {
    setScanning(true);
    // Simulate some "scanning" time for UX
    await new Promise(resolve => setTimeout(resolve, 2000));
    try {
      const res = await api.post('/api/attendance/recognize/', { subject_id: filters.subject_id });
      alert(`Face ID Scanner ran successfully! Recognized ${res.data.count} students.`);
      setShowScanner(false);
      loadAttendance();
    } catch (e) {
      alert('Face ID Scan failed. See console.');
      console.error(e);
    } finally {
      setScanning(false);
    }
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
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Subject</label>
            <select
              className="form-input"
              value={filters.subject_id}
              onChange={(e) => handleFilterChange('subject_id', e.target.value)}
            >
              <option value="">All Subjects</option>
              {subjects.map(sub => (
                <option key={sub.id} value={sub.id}>{sub.code}</option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
            <button
              className="btn btn-primary"
              onClick={handleApplyFilters}
              id="btn-apply-filters"
            >
              Apply Filters
            </button>
            {filters.subject_id && (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn btn-secondary"
                  style={{ borderColor: 'var(--color-accent-emerald)', color: 'var(--color-accent-emerald)' }}
                  onClick={() => setShowScanner(true)}
                >
                  🤖 Face ID
                </button>
                <button
                  className="btn btn-secondary"
                  style={{ borderColor: 'var(--color-accent-purple)', color: 'var(--color-accent-purple)' }}
                  onClick={() => setShowQRGenerator(true)}
                >
                  📱 QR Fallback
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* QR Code Generator Modal */}
      {showQRGenerator && (
        <div className="scanner-modal-overlay" style={{
          position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
          background: 'rgba(0,0,0,0.8)', zIndex: 9999,
          display: 'flex', justifyContent: 'center', alignItems: 'center'
        }}>
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', maxWidth: '400px', width: '100%', position: 'relative' }}>
            <button 
              style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer' }}
              onClick={() => setShowQRGenerator(false)}
            >×</button>
            <h2 style={{ marginBottom: '1rem' }}>QR Code Fallback</h2>
            <QRCodeGenerator sessionData={{ subject_id: filters.subject_id, date: filters.date_from || new Date().toISOString().split('T')[0] }} />
          </div>
        </div>
      )}

      {/* Face ID Scanner Modal */}
      {showScanner && (
        <div className="scanner-modal-overlay" style={{
          position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
          background: 'rgba(0,0,0,0.8)', zIndex: 9999,
          display: 'flex', justifyContent: 'center', alignItems: 'center'
        }}>
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', maxWidth: '500px', width: '100%', position: 'relative' }}>
            <button 
              style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer' }}
              onClick={() => setShowScanner(false)}
            >×</button>
            <h2 style={{ marginBottom: '1rem' }}>Face ID Scanner</h2>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>Align face within the outline.</p>
            
            <div style={{ position: 'relative', width: '100%', height: '300px', backgroundColor: '#000', borderRadius: '12px', overflow: 'hidden' }}>
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                muted
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              
              {/* Face Outline Overlay */}
              <div style={{
                position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                width: '180px', height: '240px', border: `3px dashed ${scanning ? 'var(--color-accent-emerald)' : 'rgba(255,255,255,0.5)'}`,
                borderRadius: '50% 50% 40% 40%', pointerEvents: 'none',
                boxShadow: scanning ? '0 0 20px var(--color-accent-emerald)' : 'none',
                transition: 'all 0.3s ease'
              }}></div>

              {/* Scanning Animation line */}
              {scanning && (
                <div style={{
                  position: 'absolute', top: '20%', left: '0', width: '100%', height: '2px',
                  background: 'var(--color-accent-emerald)', boxShadow: '0 0 10px var(--color-accent-emerald)',
                  animation: 'scan-line 2s infinite linear'
                }}></div>
              )}
            </div>

            <button 
              className="btn btn-primary btn-lg" 
              style={{ width: '100%', marginTop: '1.5rem' }}
              onClick={handleRunScan}
              disabled={scanning}
            >
              {scanning ? 'Analyzing Face Data...' : 'Start Scan'}
            </button>
            <style>{`
              @keyframes scan-line {
                0% { top: 10%; }
                50% { top: 90%; }
                100% { top: 10%; }
              }
            `}</style>
          </div>
        </div>
      )}

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
