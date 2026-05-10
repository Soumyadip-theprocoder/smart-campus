import { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import { HiOutlineChevronLeft, HiOutlineChevronRight } from 'react-icons/hi';
import '../scheduler/TimetablePage.css'; // Reuse timetable styles

export default function StudentClassAttendancePage() {
  const { user } = useAuth();
  const [timetable, setTimetable] = useState([]);
  const [timeSlots, setTimeSlots] = useState([]);
  const [attendanceLogs, setAttendanceLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Week navigation state
  const [currentWeekStart, setCurrentWeekStart] = useState(() => {
    const d = new Date();
    const day = d.getDay() || 7; // Get current day number, converting Sun(0) to 7
    if (day !== 1) {
      d.setHours(-24 * (day - 1)); // Set to Monday of this week
    }
    d.setHours(0, 0, 0, 0);
    return d;
  });

  const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

  useEffect(() => {
    loadData();
  }, [currentWeekStart]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ttRes, slotsRes, attendanceRes] = await Promise.all([
        api.get('/api/scheduler/timetable/').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/timeslots/').catch(() => ({ data: { results: [] } })),
        api.get('/api/attendance/') // Fetching all logs and filtering locally for simplicity
      ]);

      setTimetable(ttRes.data.results || ttRes.data || []);
      setTimeSlots(slotsRes.data.results || slotsRes.data || []);
      setAttendanceLogs(attendanceRes.data.results || attendanceRes.data || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const nextWeek = () => {
    const next = new Date(currentWeekStart);
    next.setDate(next.getDate() + 7);
    setCurrentWeekStart(next);
  };

  const prevWeek = () => {
    const prev = new Date(currentWeekStart);
    prev.setDate(prev.getDate() - 7);
    setCurrentWeekStart(prev);
  };

  // Helper to get actual date for a specific day in the selected week
  const getDateForDayIndex = (dayIndex) => {
    const d = new Date(currentWeekStart);
    d.setDate(d.getDate() + dayIndex);
    return d;
  };

  // Extract unique times for Y-axis
  const uniqueTimes = [...new Set(timeSlots.map(s => s.start_time))].sort();

  // Helper to find attendance status
  const getAttendanceStatus = (subjectCode, actualDate) => {
    // Format date to YYYY-MM-DD
    const dateStr = actualDate.toISOString().split('T')[0];
    const log = attendanceLogs.find(
      l => l.subject_code === subjectCode && l.date === dateStr
    );

    if (log) {
      return log.status; // 'present' or 'absent'
    }

    // Check if the date is in the future
    const today = new Date();
    today.setHours(0,0,0,0);
    if (actualDate > today) {
      return 'future';
    }

    return 'not_happened'; // Past but no record
  };

  if (loading && timeSlots.length === 0) {
    return <div className="page-container"><div className="loading-spinner"><div className="spinner" /></div></div>;
  }

  const weekEnd = new Date(currentWeekStart);
  weekEnd.setDate(weekEnd.getDate() + 5); // Saturday

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1>Class Attendance View</h1>
          <p>Track your actual class attendance on the timetable grid</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', background: 'var(--color-bg-input)', padding: '0.5rem', borderRadius: 'var(--radius-md)' }}>
          <button className="btn btn-sm btn-secondary" onClick={prevWeek} style={{ padding: '0.5rem' }}>
            <HiOutlineChevronLeft size={18} />
          </button>
          <span style={{ fontWeight: 500, fontSize: '0.9rem', minWidth: '180px', textAlign: 'center' }}>
            {currentWeekStart.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })} 
            {' - '}
            {weekEnd.toLocaleDateString('en-GB', { month: 'short', day: 'numeric', year: 'numeric' })}
          </span>
          <button className="btn btn-sm btn-secondary" onClick={nextWeek} style={{ padding: '0.5rem' }}>
            <HiOutlineChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="glass-card" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', display: 'flex', gap: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
          <div style={{ width: 16, height: 16, borderRadius: 4, background: 'rgba(16, 185, 129, 0.2)', border: '1px solid var(--color-accent-emerald)' }} />
          <span>Attended (Present)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
          <div style={{ width: 16, height: 16, borderRadius: 4, background: 'rgba(239, 68, 68, 0.2)', border: '1px solid var(--color-accent-red)' }} />
          <span>Missed (Absent)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
          <div style={{ width: 16, height: 16, borderRadius: 4, background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)' }} />
          <span>Did Not Happen / Future</span>
        </div>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem', overflowX: 'auto' }}>
        <div className="timetable-grid" style={{ minWidth: '800px' }}>
          {/* Header Row */}
          <div className="timetable-header-cell time-col">Time</div>
          {days.map((day, dayIndex) => {
            const actualDate = getDateForDayIndex(dayIndex);
            return (
              <div key={day} className="timetable-header-cell">
                <div style={{ fontWeight: 600 }}>{day}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 400 }}>
                  {actualDate.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                </div>
              </div>
            );
          })}

          {/* Time Rows */}
          {uniqueTimes.map(startTime => {
            const endTime = timeSlots.find(s => s.start_time === startTime)?.end_time;
            
            return (
              <div key={startTime} className="timetable-row" style={{ display: 'contents' }}>
                <div className="timetable-time-cell">
                  <div>{startTime.substring(0, 5)}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    to {endTime?.substring(0, 5)}
                  </div>
                </div>

                {days.map((day, dayIndex) => {
                  const actualDate = getDateForDayIndex(dayIndex);
                  
                  // Find if there's a scheduled class here
                  const entry = timetable.find(
                    t => t.day === day && t.start_time === startTime
                  );

                  if (!entry) {
                    return <div key={`${day}-${startTime}`} className="timetable-cell empty"></div>;
                  }

                  // Determine status for this class
                  const status = getAttendanceStatus(entry.subject_code || entry.subject_name.split(' ')[0], actualDate);

                  let bgStyle = {};
                  let textColor = 'var(--color-text-primary)';
                  let icon = '';

                  if (status === 'present') {
                    bgStyle = { background: 'rgba(16, 185, 129, 0.15)', borderLeft: '3px solid var(--color-accent-emerald)' };
                    textColor = 'var(--color-accent-emerald)';
                    icon = '✓';
                  } else if (status === 'absent') {
                    bgStyle = { background: 'rgba(239, 68, 68, 0.15)', borderLeft: '3px solid var(--color-accent-red)' };
                    textColor = 'var(--color-accent-red)';
                    icon = '✗';
                  } else {
                    bgStyle = { background: 'rgba(255, 255, 255, 0.05)', borderLeft: '3px solid rgba(255,255,255,0.2)', opacity: status === 'future' ? 0.7 : 1 };
                    textColor = 'var(--color-text-muted)';
                    icon = '-';
                  }

                  return (
                    <div key={`${day}-${startTime}`} className="timetable-cell filled" style={bgStyle}>
                      <div className="subject-code" style={{ color: textColor, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>{entry.subject_name.split(' ')[0] || 'CLASS'}</span>
                        <span style={{ fontSize: '0.85rem' }}>{icon}</span>
                      </div>
                      <div className="subject-name" style={{ fontSize: '0.75rem', opacity: 0.9 }}>
                        {entry.subject_name.substring(entry.subject_name.indexOf(' ') + 1)}
                      </div>
                      <div className="cell-footer">
                        <span className="room-badge">{entry.room_number}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
