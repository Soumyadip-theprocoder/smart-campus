import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import { HiOutlineArrowLeft } from 'react-icons/hi';
import './StudentDashboard.css';

export default function FacultySubjectsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [subjects, setSubjects] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  const [expandedSubject, setExpandedSubject] = useState(null);
  const [expandedStudent, setExpandedStudent] = useState(null);

  useEffect(() => {
    loadFacultyData();
  }, []);

  const loadFacultyData = async () => {
    setLoading(true);
    try {
      const [meRes, subjectsRes, attendanceRes] = await Promise.all([
        api.get('/api/auth/me/'),
        api.get('/api/scheduler/subjects/').catch(() => ({ data: { results: [] } })),
        api.get('/api/attendance/').catch(() => ({ data: { results: [] } }))
      ]);

      const facultyId = meRes.data.profile?.id;

      // Filter subjects taught by this faculty
      const mySubjects = (subjectsRes.data.results || subjectsRes.data || []).filter(
        s => s.faculty === facultyId
      );
      setSubjects(mySubjects);

      // Calculate attendance analytics for my subjects
      const allAttendance = attendanceRes.data.results || attendanceRes.data || [];
      const mySubjectCodes = mySubjects.map(s => s.code);
      const myAttendance = allAttendance.filter(a => mySubjectCodes.includes(a.subject_code));
      setAttendanceRecords(myAttendance);
      
    } catch (err) {
      console.error('Failed to load faculty subjects:', err);
    } finally {
      setLoading(false);
    }
  };

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

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button className="btn btn-secondary" onClick={() => navigate('/faculty')} style={{ padding: '0.5rem', borderRadius: '50%' }}>
          <HiOutlineArrowLeft size={20} />
        </button>
        <div>
          <h1>My Subjects & Analytics</h1>
          <p>Detailed attendance breakdown for the classes you teach.</p>
        </div>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ opacity: 0, padding: '1.5rem', marginTop: '1.5rem' }}>
        {subjectAnalytics.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📚</div>
            <h3>No subjects assigned</h3>
            <p>You currently do not have any subjects assigned to you.</p>
          </div>
        ) : (
          <div className="subject-attendance-list">
            {subjectAnalytics.map((subj, i) => {
              const isExpanded = expandedSubject === subj.code;
              return (
                <div className="subject-attendance-item" key={i} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                  <div 
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', width: '100%', padding: '0.5rem 0' }}
                    onClick={() => setExpandedSubject(isExpanded ? null : subj.code)}
                  >
                    <div className="subject-info" style={{ flex: 1 }}>
                      <span className="subject-code" style={{ fontSize: '1rem' }}>{subj.code}</span>
                      <span className="subject-name" style={{ fontSize: '1rem', fontWeight: 500 }}>{subj.name}</span>
                    </div>
                    
                    {!isExpanded && (
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginRight: '1rem' }}>
                        {subj.recordsCount} records
                      </div>
                    )}
                    
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      {isExpanded ? '▲' : '▼'}
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)', animation: 'fadeIn 0.3s ease' }}>
                      
                      <div style={{ marginBottom: '1.5rem', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px' }}>
                        <h4 style={{ fontSize: '0.85rem', marginBottom: '0.5rem', color: 'var(--color-text-secondary)' }}>Overall Subject Attendance</h4>
                        <div className="subject-progress" style={{ margin: '0.5rem 0' }}>
                          <div className="progress-bar">
                            <div
                              className="progress-fill"
                              style={{
                                width: `${subj.attendancePercentage}%`,
                                background: subj.attendancePercentage >= 75
                                  ? 'var(--gradient-emerald)'
                                  : 'var(--gradient-sunset)',
                              }}
                            />
                          </div>
                          <span className={`progress-text ${subj.attendancePercentage < 75 ? 'low' : ''}`} style={{ fontWeight: 'bold' }}>
                            {subj.attendancePercentage}%
                          </span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          {subj.recordsCount > 0 ? `Based on ${subj.recordsCount} total attendance records captured across all students.` : 'No attendance data yet'}
                        </div>
                      </div>

                      <h4 style={{ fontSize: '0.85rem', marginBottom: '0.75rem', color: 'var(--color-text-secondary)' }}>Student Attendance Breakdown</h4>
                      {getStudentAnalyticsForSubject(subj.code).length === 0 ? (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>No students found in this class.</div>
                      ) : (
                        <div style={{ overflowX: 'auto' }}>
                          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                            <thead>
                              <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                                <th style={{ padding: '0.5rem' }}>Student Name</th>
                                <th style={{ padding: '0.5rem', textAlign: 'center' }}>Present / Total</th>
                                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Percentage</th>
                              </tr>
                            </thead>
                            <tbody>
                              {getStudentAnalyticsForSubject(subj.code).map((student, idx) => {
                                const isStudentExpanded = expandedStudent === student.name;
                                return (
                                  <React.Fragment key={idx}>
                                    <tr 
                                      style={{ borderBottom: isStudentExpanded ? 'none' : '1px solid rgba(255,255,255,0.02)', cursor: 'pointer' }}
                                      onClick={() => setExpandedStudent(isStudentExpanded ? null : student.name)}
                                    >
                                      <td style={{ padding: '0.75rem 0.5rem', fontWeight: 500 }}>
                                        {isStudentExpanded ? '▼ ' : '▶ '}{student.name}
                                      </td>
                                      <td style={{ padding: '0.75rem 0.5rem', textAlign: 'center' }}>{student.present} / {student.total}</td>
                                      <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>
                                        <span className={`badge ${student.percentage >= 75 ? 'badge-low' : 'badge-urgent'}`}>
                                          {student.percentage}%
                                        </span>
                                      </td>
                                    </tr>
                                    {isStudentExpanded && (
                                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td colSpan={3} style={{ padding: '0 1rem 1rem 1.5rem' }}>
                                          <div style={{ background: 'var(--color-bg-input)', padding: '0.75rem', borderRadius: '4px', fontSize: '0.75rem' }}>
                                            <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--color-text-secondary)' }}>Daily Attendance Log</div>
                                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '0.5rem' }}>
                                              {attendanceRecords
                                                .filter(a => a.student_name === student.name && a.subject_code === subj.code)
                                                .sort((a, b) => new Date(b.date) - new Date(a.date)) // Latest first
                                                .map((record, rIdx) => (
                                                  <div key={rIdx} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                                                    <span style={{ 
                                                      width: 8, height: 8, borderRadius: '50%', 
                                                      background: record.status === 'present' ? 'var(--color-accent-emerald)' : 'var(--color-accent-red)' 
                                                    }} />
                                                    <span>{new Date(record.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</span>
                                                  </div>
                                                ))
                                              }
                                            </div>
                                          </div>
                                        </td>
                                      </tr>
                                    )}
                                  </React.Fragment>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
