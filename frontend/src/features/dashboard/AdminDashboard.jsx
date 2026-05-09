import { useState, useEffect } from 'react';
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
} from 'react-icons/hi';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [summaryRes, noticesRes] = await Promise.all([
        api.get('/api/attendance/summary/').catch(() => ({ data: {} })),
        api.get('/api/communication/notices/').catch(() => ({ data: { results: [] } })),
      ]);

      setSummary(summaryRes.data);
      setNotices((noticesRes.data.results || noticesRes.data || []).slice(0, 5));
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateTimetable = async () => {
    try {
      const response = await api.post('/api/scheduler/generate/');
      alert(response.data.message || 'Timetable generated successfully!');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to generate timetable.');
    }
  };

  const handleSendAlerts = async () => {
    try {
      const response = await api.post('/api/communication/alerts/attendance/');
      alert(response.data.message || 'Alerts sent!');
    } catch (err) {
      alert('Failed to send alerts.');
    }
  };

  // Mock attendance chart data
  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
  const chartData = [85, 92, 78, 88, 95];

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Admin Dashboard</h1>
        <p>Overview of campus activities and management</p>
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
          icon={<HiOutlineClipboardCheck />}
          label="Present Today"
          value={summary?.today_present || 0}
          gradient="emerald"
          delay={2}
        />
        <StatCard
          icon={<HiOutlineClipboardCheck />}
          label="Absent Today"
          value={summary?.today_absent || 0}
          gradient="red"
          delay={3}
        />
        <StatCard
          icon={<HiOutlineCalendar />}
          label="Attendance Rate"
          value={`${summary?.overall_attendance_rate || 0}%`}
          gradient="purple"
          delay={4}
        />
      </div>

      {/* Charts & Quick Actions */}
      <div className="grid-2" style={{ marginTop: '1.5rem' }}>
        {/* Attendance Chart */}
        <div className="glass-card dashboard-chart animate-fade-in-up stagger-5" style={{ opacity: 0 }}>
          <div className="section-header">
            <h3 className="section-title">Weekly Attendance</h3>
          </div>
          <div className="attendance-bar-chart">
            {weekDays.map((day, i) => (
              <div className="attendance-bar" key={day}>
                <div className="bar-value">{chartData[i]}%</div>
                <div className="bar" style={{ height: `${chartData[i] * 1.4}px` }} />
                <div className="bar-label">{day}</div>
              </div>
            ))}
          </div>
        </div>

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
            >
              <span className="action-icon"><HiOutlineRefresh /></span>
              Generate Timetable
            </button>
            <button
              className="quick-action-btn"
              onClick={handleSendAlerts}
              id="btn-send-alerts"
            >
              <span className="action-icon"><HiOutlineMail /></span>
              Send Alerts
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
                <p>No notices yet.</p>
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
    </div>
  );
}
