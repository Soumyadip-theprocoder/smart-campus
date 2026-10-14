import toast from 'react-hot-toast';
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
  HiOutlineDocumentDownload,
} from 'react-icons/hi';
import { Suspense, lazy } from 'react';
import LocalErrorBoundary from '../../components/LocalErrorBoundary';
const StudentAttendanceChart = lazy(() => import('./StudentAttendanceChart'));
import FaceRegistrationModal from '../accounts/FaceRegistrationModal';
import EditMarksForm from '../../components/EditMarksForm';
import './StudentDashboard.css';

export default function StudentDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [report, setReport] = useState([]);
  const [notices, setNotices] = useState([]);
  const [timetable, setTimetable] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [electives, setElectives] = useState([]);
  const [baskets, setBaskets] = useState([]);
  const [activeSwitchGroup, setActiveSwitchGroup] = useState(null);
  const [savingElective, setSavingElective] = useState(false);
  const [loading, setLoading] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  useEffect(() => {
    loadStudentData();
  }, []);

  const loadStudentData = async () => {
    setLoading(true);
    try {
      const [meRes, noticesRes, timetableRes, enrollRes, basketsRes] = await Promise.allSettled([
        api.get('/api/auth/me/'),
        api.get('/api/communication/notices/'),
        api.get('/api/scheduler/timetable/'),
        api.get('/api/scheduler/electives/enrollments/'),
        api.get('/api/scheduler/electives/baskets/'),
      ]);

      if (meRes.status === 'fulfilled') {
        setProfile(meRes.value.data);

        // Load attendance report if we have a student profile
        if (meRes.value.data.profile?.id) {
          try {
            const reportRes = await api.get(
              `/api/attendance/report/${meRes.value.data.profile.id}/`
            );
            setReport(reportRes.data);

            const forecastRes = await api.get(`/api/attendance/forecast/${meRes.value.data.profile.id}/`);
            if (forecastRes.data && forecastRes.data.forecasted_cgpa) {
              setForecast(forecastRes.data.forecasted_cgpa);
            }
          } catch {
            // No attendance data or forecast available yet
          }
        }
      }

      if (noticesRes.status === 'fulfilled') {
        setNotices((noticesRes.value.data.results || noticesRes.value.data || []).slice(0, 3));
      }
      if (timetableRes.status === 'fulfilled') {
        setTimetable((timetableRes.value.data.results || timetableRes.value.data || []).slice(0, 5));
      }
      if (enrollRes.status === 'fulfilled') {
        setElectives(enrollRes.value.data || []);
      }
      if (basketsRes.status === 'fulfilled') {
        setBaskets(basketsRes.value.data || []);
      }
    } catch (err) {
      console.error('Failed to load student data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchElective = async (groupName, subjectId, subjectName) => {
    setSavingElective(true);
    try {
      const res = await api.post('/api/scheduler/electives/enrollments/', {
        subject_id: subjectId,
        elective_group: groupName,
      });
      toast.success(`Enrolled in ${subjectName}!`);
      setElectives((prev) => {
        const filtered = prev.filter((e) => e.elective_group !== groupName);
        return [...filtered, res.data.enrollment];
      });
      setActiveSwitchGroup(null);
    } catch (err) {
      console.error('Failed to update elective:', err);
      toast.error('Failed to update elective choice.');
    } finally {
      setSavingElective(false);
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

  const handleDownloadPdf = async () => {
    if (!profile?.profile?.id) return;
    setDownloadingPdf(true);
    try {
      const response = await api.get(`/api/attendance/export/student/pdf/${profile.profile.id}/`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `attendance_${profile.profile.enrollment_number}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download PDF:', error);
      toast.error('Failed to download PDF report.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];
  const chartData = report.map((r, index) => ({
    name: r.subject_code,
    value: r.percentage,
    color: COLORS[index % COLORS.length]
  }));

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>Welcome, {user?.first_name}! 👋</h1>
          <p>
            {profile?.profile?.enrollment_number} · {profile?.profile?.department} · Semester {profile?.profile?.semester}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={handleDownloadPdf} disabled={downloadingPdf}>
            <HiOutlineDocumentDownload className="btn-icon" /> {downloadingPdf ? 'Exporting...' : 'Download PDF Report'}
          </button>
          <a href={`http://localhost:8000/api/scheduler/ical/${user?.id}/`} className="btn btn-secondary" style={{ textDecoration: 'none' }}>
            📅 Sync to Calendar (iCal)
          </a>
        </div>
      </div>

      {report.some(r => r.percentage < 75) && (
        <div className="alert alert-danger" style={{ marginBottom: '1.5rem', background: '#fee2e2', color: '#991b1b', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #ef4444', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <HiOutlineSpeakerphone size={24} />
          <div>
            <strong>Warning: Attendance Risk Detected!</strong>
            <p style={{ margin: 0 }}>Your attendance in one or more subjects is below the 75% required threshold. Please attend upcoming classes to avoid academic penalties.</p>
          </div>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid-5" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
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
          label="Predicted CGPA"
          value={forecast ? forecast.toFixed(2) : 'N/A'}
          change="AI Forecast"
          gradient="blue"
          delay={1.5}
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ height: '250px', width: '100%' }}>
                <LocalErrorBoundary>
                  <Suspense fallback={<div className="loading-spinner"><div className="spinner" /></div>}>
                    <StudentAttendanceChart data={chartData} />
                  </Suspense>
                </LocalErrorBoundary>
              </div>
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

      {/* Mandatory Elective Courses Section */}
      {baskets.length > 0 && (
        <div className="section" style={{ marginTop: '1.5rem' }}>
          <div
            className="glass-card animate-fade-in-up"
            style={{
              padding: '1.5rem',
              border: '1px solid rgba(139, 92, 246, 0.25)',
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(139, 92, 246, 0.08) 100%)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                  <span>⚡ Mandatory Elective Course Selection</span>
                  <span
                    className="badge"
                    style={{
                      fontSize: '0.75rem',
                      background: 'rgba(139, 92, 246, 0.2)',
                      color: '#c084fc',
                      border: '1px solid rgba(139, 92, 246, 0.4)',
                    }}
                  >
                    Semester {profile?.profile?.semester || 1}
                  </span>
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                  Academic regulations require you to study <strong>exactly one course</strong> per elective basket. You can switch your elective anytime.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.25rem' }}>
              {baskets.map((b) => {
                const currentEnrollment = electives.find((e) => e.elective_group === b.elective_group);
                const isExpanded = activeSwitchGroup === b.elective_group;

                return (
                  <div
                    key={b.elective_group}
                    style={{
                      background: 'var(--color-bg-glass)',
                      border: '1px solid var(--color-border)',
                      borderRadius: '12px',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                      <div>
                        <span style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                          Elective Basket
                        </span>
                        <h4 style={{ margin: '2px 0 0 0', fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>
                          {b.elective_group}
                        </h4>
                      </div>
                      <span className="badge badge-low" style={{ fontSize: '0.75rem' }}>
                        {b.choices_count} Available Options
                      </span>
                    </div>

                    {/* Current Selected Option */}
                    {currentEnrollment && (
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.75rem 1rem',
                          background: 'rgba(16, 185, 129, 0.08)',
                          border: '1px solid rgba(16, 185, 129, 0.25)',
                          borderRadius: '8px',
                          flexWrap: 'wrap',
                          gap: '8px',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ color: '#10b981', fontWeight: 700, fontSize: '0.9rem' }}>✓ Enrolled:</span>
                            <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                              {currentEnrollment.subject_code}
                            </span>
                            <strong style={{ color: 'var(--color-text-primary)' }}>
                              {currentEnrollment.subject_name}
                            </strong>
                          </div>
                          {currentEnrollment.faculty_name && (
                            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '2px', marginLeft: '1.8rem' }}>
                              👨‍🏫 Instructor: {currentEnrollment.faculty_name}
                            </div>
                          )}
                        </div>

                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => setActiveSwitchGroup(isExpanded ? null : b.elective_group)}
                          style={{ fontSize: '0.8rem', padding: '4px 10px' }}
                        >
                          {isExpanded ? 'Hide Options ▲' : 'Change Choice ▼'}
                        </button>
                      </div>
                    )}

                    {/* Expandable Options List */}
                    {(!currentEnrollment || isExpanded) && (
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                          gap: '0.75rem',
                          marginTop: '0.5rem',
                          paddingTop: '0.75rem',
                          borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                        }}
                      >
                        {b.choices.map((choice) => {
                          const isSelected = currentEnrollment?.subject === choice.id;

                          return (
                            <div
                              key={choice.id}
                              style={{
                                background: isSelected ? 'rgba(139, 92, 246, 0.12)' : 'var(--color-bg-input)',
                                border: isSelected ? '1px solid #8b5cf6' : '1px solid var(--color-border)',
                                borderRadius: '8px',
                                padding: '0.85rem',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'space-between',
                                gap: '0.5rem',
                              }}
                            >
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                  <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 700 }}>
                                    {choice.code}
                                  </span>
                                  <span className="badge badge-low" style={{ fontSize: '0.7rem' }}>
                                    {choice.credits} cr
                                  </span>
                                </div>
                                <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '0.92rem' }}>
                                  {choice.name}
                                </div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                                  👨‍🏫 {choice.faculty_name || 'TBD'}
                                </div>
                              </div>

                              <button
                                type="button"
                                className={`btn btn-sm ${isSelected ? 'btn-secondary' : 'btn-primary'}`}
                                style={{ width: '100%', marginTop: '4px', fontSize: '0.8rem' }}
                                disabled={isSelected || savingElective}
                                onClick={() => handleSwitchElective(b.elective_group, choice.id, choice.name)}
                              >
                                {isSelected ? '✓ Current Selection' : savingElective ? 'Switching...' : 'Select This Elective'}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {profile?.profile?.is_ta && (
        <div className="section" style={{ marginTop: '1.5rem' }}>
          <div className="glass-card animate-fade-in-up" style={{ opacity: 0, padding: '1.5rem' }}>
            <h3 className="section-title" style={{ marginBottom: '1rem' }}>
              👨‍🏫 Teaching Assistant Overview
            </h3>
            <div className="grid-2">
              <StatCard
                icon={<HiOutlineAcademicCap />}
                label="Max TA Hours / Week"
                value={profile.profile.ta_max_hours_per_week || 10}
                gradient="blue"
                delay={1}
              />
              <StatCard
                icon={<HiOutlineClipboardCheck />}
                label="Qualified Subjects"
                value={profile.profile.ta_qualified_subjects?.length || 0}
                gradient="purple"
                delay={2}
              />
            </div>
          </div>
        </div>
      )}

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
