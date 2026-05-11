import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import StatCard from '../../components/StatCard';
import {
  HiOutlineCalendar,
  HiOutlineAcademicCap,
  HiOutlineSpeakerphone,
  HiOutlineUsers,
} from 'react-icons/hi';
import './StudentDashboard.css'; // Reuse existing styles

export default function FacultyDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [timetable, setTimetable] = useState([]);
  const [notices, setNotices] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  const [expandedSubject, setExpandedSubject] = useState(null);
  const [expandedStudent, setExpandedStudent] = useState(null);

  useEffect(() => {
    loadFacultyData();
  }, []);

  const getStudentAnalyticsForSubject = (subjectCode) => {
    const records = attendanceRecords.filter(a => a.subject_code === subjectCode);
    const studentMap = {};
    records.forEach(r => {
      if (!studentMap[r.student_name]) {
        studentMap[r.student_name] = { name: r.student_name, total: 0, present: 0 };
      }
      studentMap[r.student_name].total++;
      if (r.status === 'present') {
        studentMap[r.student_name].present++;
      }
    });
    return Object.values(studentMap)
      .map(s => ({
        ...s,
        percentage: s.total > 0 ? ((s.present / s.total) * 100).toFixed(1) : 0
      }))
      .sort((a, b) => b.percentage - a.percentage); // Sort highest attendance first
  };

  const loadFacultyData = async () => {
    setLoading(true);
    try {
      const [meRes, noticesRes, timetableRes, subjectsRes, attendanceRes] = await Promise.all([
        api.get('/api/auth/me/'),
        api.get('/api/communication/notices/').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/timetable/').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/subjects/').catch(() => ({ data: { results: [] } })),
        api.get('/api/attendance/').catch(() => ({ data: { results: [] } }))
      ]);

      setProfile(meRes.data);
      const facultyId = meRes.data.profile?.id;

      // Filter subjects taught by this faculty
      const mySubjects = (subjectsRes.data.results || subjectsRes.data || []).filter(
        s => s.faculty === facultyId
      );
      setSubjects(mySubjects);

      // Filter timetable for this faculty
      const myTimetable = (timetableRes.data.results || timetableRes.data || []).filter(
        t => t.faculty_name === `${user.first_name} ${user.last_name}`
      );
      setTimetable(myTimetable);

      // Calculate attendance analytics for my subjects
      const allAttendance = attendanceRes.data.results || attendanceRes.data || [];
      const mySubjectCodes = mySubjects.map(s => s.code);
      const myAttendance = allAttendance.filter(a => mySubjectCodes.includes(a.subject_code));
      setAttendanceRecords(myAttendance);

      setNotices((noticesRes.data.results || noticesRes.data || []).slice(0, 3));
      
    } catch (err) {
      console.error('Failed to load faculty data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Get today's day for schedule highlight
  const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const today = days[new Date().getDay()];
  const todayClasses = timetable.filter(t => t.day === today);

  // Generate analytics per subject
  const subjectAnalytics = subjects.map(subj => {
    const records = attendanceRecords.filter(a => a.subject_code === subj.code);
    const total = records.length;
    const present = records.filter(a => a.status === 'present').length;
    return {
      ...subj,
      attendancePercentage: total > 0 ? ((present / total) * 100).toFixed(1) : 0,
      recordsCount: total
    };
  });

  const totalClassesThisWeek = timetable.length;
  const avgAttendance = subjectAnalytics.length > 0 
    ? (subjectAnalytics.reduce((sum, s) => sum + parseFloat(s.attendancePercentage), 0) / subjectAnalytics.length).toFixed(1)
    : 0;

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
        <h1>Welcome, Prof. {user?.last_name}! 👋</h1>
        <p>
          {profile?.profile?.employee_id} · {profile?.profile?.department} · {profile?.profile?.designation}
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid-4">
        <StatCard
          icon={<HiOutlineAcademicCap />}
          label="My Subjects"
          value={subjects.length}
          gradient="blue"
          delay={1}
          onClick={() => navigate('/faculty/subjects')}
        />
        <StatCard
          icon={<HiOutlineCalendar />}
          label="Classes Today"
          value={todayClasses.length}
          gradient="purple"
          delay={2}
          onClick={() => navigate('/timetable')}
        />
        <StatCard
          icon={<HiOutlineUsers />}
          label="Avg. Class Attendance"
          value={`${avgAttendance}%`}
          gradient={avgAttendance >= 75 ? 'emerald' : 'orange'}
          delay={3}
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

      <div style={{ marginTop: '1.5rem' }}>
        {/* Today's Schedule Full-Width Table */}
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
