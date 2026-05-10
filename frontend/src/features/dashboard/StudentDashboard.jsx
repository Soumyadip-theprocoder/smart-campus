import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import StatCard from '../../components/StatCard';
import {
  HiOutlineClipboardCheck,
  HiOutlineCalendar,
  HiOutlineAcademicCap,
  HiOutlineSpeakerphone,
} from 'react-icons/hi';
import './StudentDashboard.css';

export default function StudentDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [report, setReport] = useState([]);
  const [notices, setNotices] = useState([]);
  const [timetable, setTimetable] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStudentData();
  }, []);

  const loadStudentData = async () => {
    setLoading(true);
    try {
      const [meRes, noticesRes, timetableRes] = await Promise.all([
        api.get('/api/auth/me/'),
        api.get('/api/communication/notices/').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/timetable/').catch(() => ({ data: { results: [] } })),
      ]);

      setProfile(meRes.data);

      // Load attendance report if we have a student profile
      if (meRes.data.profile?.id) {
        try {
          const reportRes = await api.get(
            `/api/attendance/report/${meRes.data.profile.id}/`
          );
          setReport(reportRes.data);
        } catch {
          // No attendance data yet
        }
      }

      setNotices((noticesRes.data.results || noticesRes.data || []).slice(0, 3));
      setTimetable((timetableRes.data.results || timetableRes.data || []).slice(0, 5));
    } catch (err) {
      console.error('Failed to load student data:', err);
    } finally {
      setLoading(false);
    }
  };

  const overallAttendance = report.length > 0
    ? (report.reduce((sum, r) => sum + r.percentage, 0) / report.length).toFixed(1)
    : 0;

  const totalClasses = report.reduce((sum, r) => sum + r.total_classes, 0);
  const classesAttended = report.reduce((sum, r) => sum + r.classes_attended, 0);

  // Get today's day for schedule highlight
  const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const today = days[new Date().getDay()];
  const todayClasses = timetable.filter(t => t.day === today);

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
        <h1>Welcome, {user?.first_name}! 👋</h1>
        <p>
          {profile?.profile?.enrollment_number} · {profile?.profile?.department} · Semester {profile?.profile?.semester}
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid-4">
        <StatCard
          icon={<HiOutlineClipboardCheck />}
          label="Attendance"
          value={`${overallAttendance}%`}
          gradient={overallAttendance >= 75 ? 'emerald' : 'red'}
          delay={1}
          onClick={() => navigate('/student/attendance')}
        />
        <StatCard
          icon={<HiOutlineAcademicCap />}
          label="Classes Attended"
          value={classesAttended}
          change={`of ${totalClasses} total`}
          gradient="blue"
          delay={2}
          onClick={() => navigate('/student/class-attendance')}
        />
        <StatCard
          icon={<HiOutlineCalendar />}
          label="Today's Classes"
          value={todayClasses.length}
          gradient="purple"
          delay={3}
          onClick={() => navigate('/timetable')}
        />
        <StatCard
          icon={<HiOutlineSpeakerphone />}
          label="Notices"
          value={notices.length}
          gradient="orange"
          delay={4}
          onClick={() => navigate('/notices')}
        />
      </div>

      <div className="grid-2" style={{ marginTop: '1.5rem' }}>
        {/* Attendance by Subject */}
        <div className="glass-card animate-fade-in-up stagger-5" style={{ opacity: 0, padding: '1.5rem' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>
            Attendance by Subject
          </h3>
          {report.length === 0 ? (
            <div className="empty-state">
              <p>No attendance records yet.</p>
            </div>
          ) : (
            <div className="subject-attendance-list">
              {report.map((r, i) => (
                <div className="subject-attendance-item" key={i}>
                  <div className="subject-info">
                    <span className="subject-code">{r.subject_code}</span>
                    <span className="subject-name">{r.subject_name}</span>
                  </div>
                  <div className="subject-progress">
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${r.percentage}%`,
                          background: r.percentage >= 75
                            ? 'var(--gradient-emerald)'
                            : 'var(--gradient-sunset)',
                        }}
                      />
                    </div>
                    <span className={`progress-text ${r.percentage < 75 ? 'low' : ''}`}>
                      {r.percentage}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Today's Schedule */}
        <div className="glass-card animate-fade-in-up stagger-5" style={{ opacity: 0, padding: '1.5rem' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>
            Today's Schedule
          </h3>
          {todayClasses.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📚</div>
              <h3>No classes today</h3>
              <p>Enjoy your day off!</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                    <th style={{ padding: '0.5rem' }}>Time</th>
                    <th style={{ padding: '0.5rem' }}>Subject</th>
                    <th style={{ padding: '0.5rem' }}>Faculty</th>
                    <th style={{ padding: '0.5rem' }}>Location</th>
                  </tr>
                </thead>
                <tbody>
                  {todayClasses.map((cls, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '0.75rem 0.5rem', whiteSpace: 'nowrap', color: 'var(--color-accent-blue-light)' }}>
                        {cls.start_time?.substring(0, 5)} - {cls.end_time?.substring(0, 5)}
                      </td>
                      <td style={{ padding: '0.75rem 0.5rem' }}>
                        <div style={{ fontWeight: 600 }}>{cls.subject_code}</div>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>{cls.subject_name}</div>
                      </td>
                      <td style={{ padding: '0.75rem 0.5rem' }}>{cls.faculty_name}</td>
                      <td style={{ padding: '0.75rem 0.5rem' }}>
                        <div className="badge badge-low">{cls.room_number}</div>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', marginTop: '0.25rem' }}>{cls.building}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Recent Notices */}
      <div className="section" style={{ marginTop: '1.5rem' }}>
        <div className="glass-card animate-fade-in-up" style={{ opacity: 0, animationDelay: '0.35s', padding: '1.5rem' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>
            Recent Notices
          </h3>
          {notices.map(notice => (
            <div key={notice.id} className={`notice-card priority-${notice.priority}`}>
              <div className="notice-header">
                <span className="notice-title">{notice.title}</span>
                <span className={`badge badge-${notice.priority}`}>
                  {notice.priority_display || notice.priority}
                </span>
              </div>
              <p className="notice-content">
                {notice.content?.substring(0, 150)}
                {notice.content?.length > 150 ? '...' : ''}
              </p>
              <div className="notice-meta">
                {new Date(notice.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
