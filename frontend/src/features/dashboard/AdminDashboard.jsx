import toast from 'react-hot-toast';
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import StatCard from '../../components/StatCard';
import DataTable from '../../components/DataTable';
import {
  HiOutlineUsers,
  HiOutlineClipboardCheck,
  HiOutlineCalendar,
  HiOutlineSpeakerphone,
  HiOutlineRefresh,
  HiOutlineMail,
  HiOutlinePlusCircle,
  HiOutlineDownload,
} from 'react-icons/hi';
import { Suspense, lazy } from 'react';
import LocalErrorBoundary from '../../components/LocalErrorBoundary';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloadingCsv, setDownloadingCsv] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [atRiskStudents, setAtRiskStudents] = useState([]);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [dispatchingAlerts, setDispatchingAlerts] = useState(false);
  const navigate = useNavigate();

  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    loadDashboardData();
    return () => {
      isMounted.current = false;
    };
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [overviewRes, noticesRes] = await Promise.all([
        api.get('/api/analytics/overview/').catch(() => ({ data: {} })),
        api.get('/api/communication/notices/').catch(() => ({ data: { results: [] } }))
      ]);

      if (isMounted.current) {
        setSummary(overviewRes.data);
        setNotices((noticesRes.data.results || noticesRes.data || []).slice(0, 5));
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  };

  const loadRiskAssessment = async () => {
    setLoadingRisk(true);
    try {
      const res = await api.get('/api/attendance/risk-assessment/');
      if (isMounted.current) {
        setAtRiskStudents(res.data || []);
      }
    } catch (err) {
      toast.error('Failed to load risk assessment data.');
    } finally {
      if (isMounted.current) {
        setLoadingRisk(false);
      }
    }
  };

  useEffect(() => {
    loadRiskAssessment();
  }, []);

  const handleGenerateTimetable = async () => {
    setIsGenerating(true);
    try {
      const response = await api.post('/api/scheduler/generate/');
      if (response.data.task_id) {
        const taskId = response.data.task_id;
        let isComplete = false;
        let attempts = 0;
        const maxAttempts = 30; // 60 seconds max
        
        while (!isComplete && attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 2000));
          attempts++;
          
          try {
            const statusRes = await api.get(`/api/scheduler/task-status/${taskId}/`);
            if (statusRes.data.status === 'completed') {
              isComplete = true;
              toast.success('Timetable generated successfully!');
            } else if (statusRes.data.status === 'failed') {
              isComplete = true;
              toast.error('Failed to generate timetable: ' + statusRes.data.error);
            }
          } catch (statusErr) {
             console.error('Error checking task status', statusErr);
             // don't abort completely on one failed status check
          }
        }
        if (!isComplete && isMounted.current) {
          toast.error('Timetable generation timed out. Please check again later.');
        }
      } else {
        if (isMounted.current) {
          toast.success(response.data.message || 'Timetable generated successfully!');
        }
      }
    } catch (err) {
      if (isMounted.current) {
        toast.error(err.response?.data?.error || 'Failed to generate timetable.');
      }
    } finally {
      if (isMounted.current) {
        setIsGenerating(false);
      }
    }
  };

  const handleSendAlerts = async () => {
    setDispatchingAlerts(true);
    try {
      const response = await api.post('/api/attendance/alerts/dispatch/');
      toast.success(response.data.message || 'Alert dispatch task successfully queued in the background');
    } catch (err) {
      toast.error('Failed to send alerts.');
    } finally {
      setDispatchingAlerts(false);
    }
  };

  const handleDownloadCsv = async () => {
    setDownloadingCsv(true);
    try {
      const response = await api.get('/api/attendance/export/admin/csv/', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'attendance_report.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download CSV:', error);
      toast.error('Failed to download CSV report.');
    } finally {
      setDownloadingCsv(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="page-header" style={{ marginBottom: '2rem' }}>
          <div className="skeleton" style={{ width: '250px', height: '36px', marginBottom: '8px' }} />
          <div className="skeleton" style={{ width: '350px', height: '20px' }} />
        </div>
        <div className="grid-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton skeleton-card" style={{ height: '116px' }} />
          ))}
        </div>
        <div className="grid-2" style={{ marginTop: '1.5rem' }}>
          <div className="skeleton skeleton-card" style={{ height: '300px' }} />
          <div className="skeleton skeleton-card" style={{ height: '300px' }} />
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>Admin Dashboard</h1>
          <p>Overview of campus activities and management</p>
        </div>
        <div>
          <button className="btn btn-secondary" onClick={handleDownloadCsv} disabled={downloadingCsv}>
            <HiOutlineDownload className="btn-icon" /> {downloadingCsv ? 'Exporting...' : 'Export CSV'}
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid-4">
        <StatCard
          icon={<HiOutlineUsers />}
          label="Total Students"
          value={summary?.total_students || 0}
          change="+12 this semester"
          gradient="blue"
          delay={1}
        />
        <StatCard
          icon={<HiOutlineUsers />}
          label="Total Faculty"
          value={summary?.total_faculty || 0}
          gradient="emerald"
          delay={2}
        />
        <StatCard
          icon={<HiOutlineCalendar />}
          label="Active Classes Today"
          value={summary?.today_active_classes || 0}
          gradient="red"
          delay={3}
        />
        <StatCard
          icon={<HiOutlineClipboardCheck />}
          label="Overall Campus Attendance"
          value={`${summary?.overall_attendance || 0}%`}
          gradient="purple"
          delay={4}
        />
      </div>

      {/* Quick Actions & Navigation */}
      <div className="grid-1" style={{ marginTop: '1.5rem' }}>
        {/* Quick Actions */}
        <div className="glass-card animate-fade-in-up stagger-5" style={{ opacity: 0 }}>
          <div style={{ padding: '1.5rem 1.5rem 0.75rem' }}>
            <h3 className="section-title">Quick Actions</h3>
          </div>
          <div className="quick-actions">
            <button
              className="quick-action-btn"
              onClick={handleGenerateTimetable}
              id="btn-generate-timetable"
              disabled={isGenerating}
            >
              <span className="action-icon"><HiOutlineRefresh className={isGenerating ? 'spin' : ''} /></span>
              {isGenerating ? 'Generating...' : 'Generate Timetable'}
            </button>
            <button
              className="quick-action-btn"
              onClick={handleSendAlerts}
              id="btn-send-alerts"
              disabled={dispatchingAlerts}
            >
              <span className="action-icon"><HiOutlineMail className={dispatchingAlerts ? 'spin' : ''} /></span>
              {dispatchingAlerts ? 'Dispatching...' : 'Dispatch ML Warning Alerts'}
            </button>
            <button
              className="quick-action-btn"
              onClick={() => navigate('/notices')}
              id="btn-create-notice"
            >
              <span className="action-icon"><HiOutlinePlusCircle /></span>
              New Notice
            </button>
            <button
              className="quick-action-btn"
              onClick={() => navigate('/admin/attendance')}
              id="btn-view-attendance"
            >
              <span className="action-icon"><HiOutlineClipboardCheck /></span>
              View Attendance
            </button>
          </div>
        </div>
      </div>

      {/* Recent Notices */}
      <div className="section" style={{ marginTop: '1.5rem' }}>
        <div className="glass-card animate-fade-in-up" style={{ opacity: 0, animationDelay: '0.35s' }}>
          <div style={{ padding: '1.5rem 1.5rem 0' }}>
            <div className="section-header">
              <h3 className="section-title">Recent Notices</h3>
              <button className="btn btn-sm btn-secondary" onClick={() => navigate('/notices')}>
                View All
              </button>
            </div>
          </div>
          <div style={{ padding: '1rem 1.5rem 1.5rem' }}>
            {notices.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon"><HiOutlineSpeakerphone /></div>
                <h3>No Recent Notices</h3>
                <p>Campus announcements will appear here.</p>
              </div>
            ) : (
              notices.map(notice => (
                <div
                  key={notice.id}
                  className={`notice-card priority-${notice.priority}`}
                >
                  <div className="notice-header">
                    <span className="notice-title">{notice.title}</span>
                    <span className={`badge badge-${notice.priority}`}>
                      {notice.priority_display || notice.priority}
                    </span>
                  </div>
                  <p className="notice-content">
                    {notice.content?.substring(0, 120)}
                    {notice.content?.length > 120 ? '...' : ''}
                  </p>
                  <div className="notice-meta">
                    By {notice.posted_by_name} · {new Date(notice.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Predictive Absenteeism Risk Panel */}
      <div className="section" style={{ marginTop: '1.5rem' }}>
        <div className="glass-card animate-fade-in-up" style={{ opacity: 0, animationDelay: '0.45s' }}>
          <div style={{ padding: '1.5rem 1.5rem 0' }}>
            <div className="section-header">
              <h3 className="section-title">Predictive Absenteeism Risk</h3>
              <button 
                className="btn btn-sm btn-primary" 
                onClick={handleSendAlerts}
                disabled={dispatchingAlerts || atRiskStudents.length === 0}
              >
                <HiOutlineMail className="btn-icon" />
                {dispatchingAlerts ? 'Dispatching...' : 'Dispatch Warning Alerts'}
              </button>
            </div>
          </div>
          <div style={{ padding: '1rem 1.5rem 1.5rem' }}>
            {loadingRisk ? (
              <div className="loading-spinner"><div className="spinner" /></div>
            ) : atRiskStudents.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon"><HiOutlineClipboardCheck /></div>
                <h3>No Students at Risk</h3>
                <p>The AI engine found no students at risk of severe absenteeism.</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Enrollment</th>
                      <th>Subject</th>
                      <th>Current %</th>
                      <th>Risk Probability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {atRiskStudents.map((student, i) => (
                      <tr key={i}>
                        <td>{student.student_name}</td>
                        <td>{student.enrollment_number}</td>
                        <td>{student.subject_name}</td>
                        <td>
                          <span className={`badge ${student.current_pct < 75 ? 'badge-high' : 'badge-medium'}`}>
                            {student.current_pct}%
                          </span>
                        </td>
                        <td>
                          <span className="badge badge-high">
                            {(student.risk_probability * 100).toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
