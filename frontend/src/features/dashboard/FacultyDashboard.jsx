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


  useEffect(() => {
    loadFacultyData();
  }, []);

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
      const mySubjectIds = mySubjects.map(s => s.id);
      const myTimetable = (timetableRes.data.results || timetableRes.data || []).filter(
        t => mySubjectIds.includes(t.subject)
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
        <div className="page-header" style={{ marginBottom: '2rem' }}>
          <div className="skeleton" style={{ width: '250px', height: '36px', marginBottom: '8px' }} />
          <div className="skeleton" style={{ width: '350px', height: '20px' }} />
        </div>
        <div className="grid-3">
          {[1, 2, 3].map(i => (
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
            <div className="today-schedule">
              {todayClasses.map((cls, i) => (
                <div key={i} className="schedule-item">
                  <div className="schedule-time">
                    {cls.start_time?.substring(0, 5)} - {cls.end_time?.substring(0, 5)}
                  </div>
                  <div className="schedule-details">
                    <div className="schedule-subject">{cls.subject_code}</div>
                    <div className="schedule-meta">{cls.subject_name}</div>
                  </div>
                  <div className="schedule-location" style={{ textAlign: 'right' }}>
                    <div className="badge badge-low">{cls.room_number}</div>
                    <div className="schedule-meta">{cls.building}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <div className="glass-card animate-fade-in-up stagger-5" style={{ opacity: 0, padding: '1.5rem', animationDelay: '0.25s' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>
            My Subjects Overview
          </h3>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>Total Classes</th>
                  <th>Avg. Attendance</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {subjectAnalytics.map((subj, i) => (
                  <tr key={i}>
                    <td data-label="Subject">
                      <div style={{ fontWeight: 600 }}>{subj.code}</div>
                      <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>{subj.name}</div>
                    </td>
                    <td data-label="Total Classes">
                      {subj.recordsCount}
                    </td>
                    <td data-label="Avg. Attendance">
                      {subj.attendancePercentage}%
                    </td>
                    <td data-label="Status">
                      {parseFloat(subj.attendancePercentage) < 75.0 && subj.recordsCount > 0 ? (
                        <span className="badge badge-urgent">Low Attendance</span>
                      ) : (
                        <span className="badge badge-low">Healthy</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent Notices */}
      <div className="section" style={{ marginTop: '1.5rem' }}>
        <div className="glass-card animate-fade-in-up" style={{ opacity: 0, animationDelay: '0.35s', padding: '1.5rem' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>
            Recent Notices
          </h3>
          {notices.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon"><HiOutlineSpeakerphone /></div>
              <h3>No Recent Notices</h3>
              <p>Campus announcements will appear here.</p>
            </div>
          ) : (
            notices.map(notice => (
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
            ))
          )}
        </div>
      </div>
    </div>
  );
}
