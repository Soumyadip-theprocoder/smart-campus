import { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import DataTable from '../../components/DataTable';
import StatCard from '../../components/StatCard';
import { HiOutlineClipboardCheck, HiOutlineAcademicCap, HiOutlineXCircle } from 'react-icons/hi';

export default function StudentAttendancePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [report, setReport] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAttendanceData();
  }, []);

  const loadAttendanceData = async () => {
    setLoading(true);
    try {
      const meRes = await api.get('/api/auth/me/');
      setProfile(meRes.data);

      if (meRes.data.profile?.id) {
        const studentId = meRes.data.profile.id;
        
        const [reportRes, logsRes] = await Promise.all([
          api.get(`/api/attendance/report/${studentId}/`),
          api.get('/api/attendance/')
        ]);

        setReport(reportRes.data);
        setLogs(logsRes.data.results || logsRes.data || []);
      }
    } catch (err) {
      console.error('Failed to load attendance data:', err);
    } finally {
      setLoading(false);
    }
  };

  const overallAttendance = report.length > 0
    ? (report.reduce((sum, r) => sum + r.percentage, 0) / report.length).toFixed(1)
    : 0;
  
  const totalClasses = report.reduce((sum, r) => sum + r.total_classes, 0);
  const classesAttended = report.reduce((sum, r) => sum + r.classes_attended, 0);

  const columns = [
    { key: 'date', label: 'Date', render: (val) => new Date(val).toLocaleDateString('en-GB', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' }) },
    { key: 'subject_name', label: 'Subject', render: (_, row) => <strong>{row.subject_code} - {row.subject_name}</strong> },
    { 
      key: 'status', 
      label: 'Status', 
      render: (val) => (
        <span className={`badge ${val === 'present' ? 'badge-present' : 'badge-urgent'}`}>
          {val.toUpperCase()}
        </span>
      ) 
    },
    { key: 'method', label: 'Recorded Via', render: (val) => <span className="badge badge-low">{val.replace('_', ' ')}</span> }
  ];

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>My Attendance Analytics</h1>
        <p>Detailed view of your class attendance and subject-wise performance</p>
      </div>

      <div className="grid-3" style={{ marginBottom: '2rem' }}>
        <StatCard
          icon={<HiOutlineClipboardCheck />}
          label="Overall Attendance"
          value={`${overallAttendance}%`}
          gradient={overallAttendance >= 75 ? 'emerald' : 'red'}
        />
        <StatCard
          icon={<HiOutlineAcademicCap />}
          label="Total Classes Attended"
          value={classesAttended}
          change={`Out of ${totalClasses}`}
          gradient="blue"
          delay={1}
        />
        <StatCard
          icon={<HiOutlineXCircle />}
          label="Total Absences"
          value={totalClasses - classesAttended}
          gradient="orange"
          delay={2}
        />
      </div>

      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
          <h3 className="section-title" style={{ marginBottom: '1.5rem' }}>Subject-wise Breakdown</h3>
          
          {report.length === 0 ? (
             <div className="empty-state"><p>No attendance data found.</p></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {report.map((r, i) => (
                <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <strong>{r.subject_code}</strong>
                    <span style={{ color: r.percentage >= 75 ? 'var(--color-accent-emerald)' : 'var(--color-accent-red)' }}>
                      {r.percentage}% ({r.classes_attended}/{r.total_classes})
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'var(--color-bg-input)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ 
                      width: `${r.percentage}%`, 
                      height: '100%', 
                      background: r.percentage >= 75 ? 'var(--gradient-emerald)' : 'var(--gradient-sunset)',
                      transition: 'width 1s ease-in-out'
                    }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="glass-card animate-fade-in-up stagger-1" style={{ padding: '1.5rem' }}>
           <h3 className="section-title" style={{ marginBottom: '1rem' }}>Attendance Insights</h3>
           <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', color: 'var(--color-text-secondary)', fontSize: '0.95rem' }}>
              <div style={{ padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', borderLeft: '3px solid var(--color-accent-blue)', borderRadius: '4px' }}>
                💡 <strong>Tip:</strong> You need to maintain a minimum of 75% attendance in each subject to be eligible for end-semester exams.
              </div>
              
              {report.filter(r => r.percentage < 75).length > 0 && (
                <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderLeft: '3px solid var(--color-accent-red)', borderRadius: '4px' }}>
                  ⚠️ <strong>Warning:</strong> You are currently falling short of the 75% requirement in {report.filter(r => r.percentage < 75).map(r => r.subject_code).join(', ')}.
                </div>
              )}
              
              {overallAttendance >= 90 && (
                <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderLeft: '3px solid var(--color-accent-emerald)', borderRadius: '4px' }}>
                  🌟 <strong>Great job!</strong> Your overall attendance is outstanding. Keep up the consistency!
                </div>
              )}
           </div>
        </div>
      </div>

      <div className="glass-card animate-fade-in-up stagger-2" style={{ padding: '1.5rem' }}>
        <h3 className="section-title" style={{ marginBottom: '1rem' }}>Detailed Daily Log</h3>
        <DataTable 
          columns={columns} 
          data={logs} 
          searchKey="subject_code"
          emptyMessage="No daily attendance logs found."
        />
      </div>
    </div>
  );
}
