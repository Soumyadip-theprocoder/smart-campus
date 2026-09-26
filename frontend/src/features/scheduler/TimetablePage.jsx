import toast from 'react-hot-toast';
import React, { useState, useEffect } from 'react';
import { DndContext, useDraggable, useDroppable } from '@dnd-kit/core';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import LocalErrorBoundary from '../../components/LocalErrorBoundary';
import './TimetablePage.css';

/* ── Drag & Drop Components ───────────────────────────────────── */
const DraggableClassCard = ({ cls, isLocked, color, isAdmin, onLockToggle, showConfig }) => {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: cls.id,
    disabled: isLocked || !isAdmin
  });

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    zIndex: 999,
    position: 'relative'
  } : { position: 'relative' };

  return (
    <div
      ref={setNodeRef}
      style={{ ...style, background: color }}
      className={`class-card ${isLocked ? 'class-card-locked' : ''}`}
    >
      <div 
        {...listeners} 
        {...attributes}
        style={{ flexGrow: 1, cursor: isLocked ? 'default' : 'grab', width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
      >
        <div className="class-name">{cls.subject_code}</div>
        <div className="class-room">📍 {cls.room_number}</div>
        <div className="class-room">{cls.faculty_name}</div>
      </div>
      
      {showConfig && isAdmin && (
        <button 
           style={{ position: 'absolute', top: '-8px', right: '-8px', padding: '2px 4px', fontSize: '12px', background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: '50%', cursor: 'pointer', zIndex: 10 }}
           onClick={(e) => { e.preventDefault(); e.stopPropagation(); onLockToggle(cls); }}
           title={isLocked ? "Unlock" : "Lock"}
        >
          {isLocked ? '🔒' : '🔓'}
        </button>
      )}
      {!showConfig && isLocked && <span className="lock-icon">🔒</span>}
    </div>
  );
};

const DroppableCell = ({ id, children }) => {
  const { isOver, setNodeRef } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={`timetable-cell ${isOver ? 'drop-target' : ''}`}
      style={isOver ? { backgroundColor: 'rgba(255, 255, 255, 0.1)' } : undefined}
    >
      {children}
    </div>
  );
};

export default function TimetablePage() {
  const [timetable, setTimetable] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const { isAdmin } = useAuth();

  /* ── Reference data for configuration ───────────────────────────── */
  const [subjects, setSubjects] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [timeslots, setTimeslots] = useState([]);

  /* ── Generator config state ─────────────────────────────────────── */
  const [config, setConfig] = useState({
    subject_ids: [],
    room_ids: [],
    timeslot_ids: [],
    locked_entries: [],
    excluded_slots: {},
    preferred_room_types: {},
    avoid_back_to_back: false,
    max_classes_per_day: 1,
  });

  const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const dayLabels = {
    MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday',
    THU: 'Thursday', FRI: 'Friday', SAT: 'Saturday',
  };

  /* Derive unique start times dynamically from fetched time slots */
  const timeSlotTimes = [...new Set(
    timeslots.map(ts => ts.start_time?.substring(0, 5))
  )].filter(Boolean).sort();

  /* ── Load data ──────────────────────────────────────────────────── */
  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [ttRes, subRes, roomRes, tsRes] = await Promise.all([
        api.get('/api/scheduler/timetable/'),
        api.get('/api/scheduler/subjects/'),
        api.get('/api/scheduler/rooms/'),
        api.get('/api/scheduler/timeslots/'),
      ]);
      const tt = ttRes.data.results || ttRes.data || [];
      const subs = subRes.data.results || subRes.data || [];
      const rms = roomRes.data.results || roomRes.data || [];
      const tss = tsRes.data.results || tsRes.data || [];

      setTimetable(tt);
      setSubjects(subs);
      setRooms(rms);
      setTimeslots(tss);

      // Initialize config with all selected
      setConfig(prev => ({
        ...prev,
        subject_ids: subs.map(s => s.id),
        room_ids: rms.map(r => r.id),
        timeslot_ids: tss.map(ts => ts.id),
      }));
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  /* ── Generate with config ───────────────────────────────────────── */
  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const payload = { ...config };
      if (Object.keys(payload.excluded_slots).length === 0) delete payload.excluded_slots;
      if (Object.keys(payload.preferred_room_types).length === 0) delete payload.preferred_room_types;
      if (payload.locked_entries.length === 0) delete payload.locked_entries;

      const response = await api.post('/api/scheduler/generate/', payload);
      
      if (response.data.task_id) {
        // Poll for task completion
        const taskId = response.data.task_id;
        let isComplete = false;
        
        while (!isComplete) {
          await new Promise(resolve => setTimeout(resolve, 2000));
          const statusRes = await api.get(`/api/scheduler/task-status/${taskId}/`);
          
          if (statusRes.data.status === 'completed') {
            isComplete = true;
            if (statusRes.data.result?.success === false) {
                toast.error('Generation failed: ' + statusRes.data.result.error);
            } else {
                toast.success('Timetable generated successfully!');
                window.location.reload();
            }
          } else if (statusRes.data.status === 'failed') {
            isComplete = true;
            toast.error('Failed to generate timetable: ' + statusRes.data.error);
          }
        }
      } else {
        setTimetable(response.data.timetable || []);
        setShowConfig(false);
        toast(response.data.message);
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to generate timetable.');
    } finally {
      setGenerating(false);
    }
  };

  /* ── Config toggles ─────────────────────────────────────────────── */
  const toggleId = (key, id) => {
    setConfig(prev => ({
      ...prev,
      [key]: prev[key].includes(id)
        ? prev[key].filter(x => x !== id)
        : [...prev[key], id],
    }));
  };

  const toggleAll = (key, allIds) => {
    setConfig(prev => ({
      ...prev,
      [key]: prev[key].length === allIds.length ? [] : [...allIds],
    }));
  };

  const toggleExcludedSlot = (subjectId, tsId) => {
    setConfig(prev => {
      const current = prev.excluded_slots[subjectId] || [];
      const updated = current.includes(tsId)
        ? current.filter(x => x !== tsId)
        : [...current, tsId];
      return {
        ...prev,
        excluded_slots: {
          ...prev.excluded_slots,
          [subjectId]: updated.length > 0 ? updated : undefined,
        },
      };
    });
  };

  const setPreferredRoomType = (subjectId, roomType) => {
    setConfig(prev => ({
      ...prev,
      preferred_room_types: {
        ...prev.preferred_room_types,
        [subjectId]: roomType || undefined,
      },
    }));
  };

  const toggleDBLockEntry = async (entry) => {
    try {
      const newLockedStatus = !entry.is_locked;
      const response = await api.patch(`/api/scheduler/timetable/${entry.id}/`, {
        is_locked: newLockedStatus
      });
      setTimetable(prev => prev.map(item => item.id === entry.id ? { ...item, is_locked: newLockedStatus } : item));
      toast.success(newLockedStatus ? 'Class locked' : 'Class unlocked');
    } catch (err) {
      toast.error('Failed to toggle lock');
    }
  };

  const isEntryLocked = (entry) => {
    return entry.is_locked;
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    
    const entryId = active.id;
    const parts = over.id.split('-');
    const timeslotId = parts[parts.length - 1];
    
    try {
      const response = await api.patch(`/api/scheduler/timetable/${entryId}/`, {
        time_slot: parseInt(timeslotId)
      });
      setTimetable(prev => prev.map(item => 
        item.id === entryId ? { 
          ...item, 
          time_slot: response.data.time_slot,
          day: response.data.day,
          start_time: response.data.start_time,
          end_time: response.data.end_time
        } : item
      ));
      toast.success('Class moved successfully');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to move class');
    }
  };

  /* ── Timetable helpers ──────────────────────────────────────────── */
  const [customColors, setCustomColors] = useState(() => {
    const saved = localStorage.getItem('timetableColors');
    return saved ? JSON.parse(saved) : {};
  });

  const handleColorChange = (subjectCode, color) => {
    const newColors = { ...customColors, [subjectCode]: color };
    setCustomColors(newColors);
    localStorage.setItem('timetableColors', JSON.stringify(newColors));
  };

  const getClassForSlot = (day, time) => {
    return timetable.find(
      entry => entry.day === day && entry.start_time?.substring(0, 5) === time
    );
  };

  const getTimeslotForDayTime = (day, time) => {
    return timeslots.find(ts => ts.day === day && ts.start_time?.substring(0, 5) === time);
  };

  const getSubjectColor = (subjectCode, subjectType) => {
    if (customColors[subjectCode]) return customColors[subjectCode];
    switch (subjectType?.toLowerCase()) {
      case "lecture":  return "var(--gradient-primary)";
      case "lab":      return "var(--gradient-emerald)";
      case "seminar":  return "var(--gradient-pink)";
      default:         return "var(--gradient-dark)";
    }
  };

  /* ── Group time slots by day ────────────────────────────────────── */
  const tsByDay = {};
  timeslots.forEach(ts => {
    if (!tsByDay[ts.day]) tsByDay[ts.day] = [];
    tsByDay[ts.day].push(ts);
  });

  /* ── Active config tab ──────────────────────────────────────────── */
  const [configTab, setConfigTab] = useState('subjects');

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Class Timetable</h1>
          <p>Weekly schedule generated by the constraint satisfaction algorithm</p>
        </div>
        {isAdmin && (
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              className="btn btn-secondary"
              onClick={() => setShowConfig(!showConfig)}
              id="btn-configure-generator"
            >
              ⚙️ {showConfig ? 'Hide Config' : 'Configure'}
            </button>
            <button
              className="btn btn-primary"
              onClick={() => showConfig ? handleGenerate() : setShowConfig(true)}
              disabled={generating}
              id="btn-generate-timetable"
            >
              {generating ? '⏳ Generating...' : '⚡ Generate'}
            </button>
          </div>
        )}
      </div>

      {/* ── Configuration Panel ─────────────────────────────────────── */}
      {isAdmin && showConfig && (
        <div className="config-panel glass-card animate-fade-in-up" style={{ opacity: 0 }}>
          <div className="config-header">
            <h2>🎛️ Generator Configuration</h2>
            <p>Fine-tune which resources to include and set scheduling constraints</p>
          </div>

          {/* Config tabs */}
          <div className="config-tabs">
            {[
              { key: 'subjects', label: '📚 Subjects', count: `${config.subject_ids.length}/${subjects.length}` },
              { key: 'rooms', label: '🏛️ Rooms', count: `${config.room_ids.length}/${rooms.length}` },
              { key: 'timeslots', label: '🕒 Time Slots', count: `${config.timeslot_ids.length}/${timeslots.length}` },
              { key: 'constraints', label: '🔒 Constraints' },
              { key: 'advanced', label: '⚙️ Advanced' },
            ].map(tab => (
              <button
                key={tab.key}
                className={`config-tab ${configTab === tab.key ? 'active' : ''}`}
                onClick={() => setConfigTab(tab.key)}
              >
                {tab.label}
                {tab.count && <span className="config-tab-count">{tab.count}</span>}
              </button>
            ))}
          </div>

          <div className="config-body">
            {/* ── Subjects tab ──────────────────────────────────────────── */}
            {configTab === 'subjects' && (
              <div className="config-section">
                <div className="config-section-header">
                  <h3>Select Subjects to Schedule</h3>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => toggleAll('subject_ids', subjects.map(s => s.id))}
                  >
                    {config.subject_ids.length === subjects.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                <div className="checkbox-grid">
                  {subjects.map(s => (
                    <label key={s.id} className={`checkbox-card ${config.subject_ids.includes(s.id) ? 'selected' : ''}`}>
                      <input
                        type="checkbox"
                        checked={config.subject_ids.includes(s.id)}
                        onChange={() => toggleId('subject_ids', s.id)}
                      />
                      <div className="checkbox-card-content">
                        <span className="checkbox-code">{s.code}</span>
                        <span className="checkbox-name">{s.name}</span>
                        <span className="checkbox-meta">{s.faculty_name} · {s.sessions_per_week} sessions/wk</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* ── Rooms tab ─────────────────────────────────────────────── */}
            {configTab === 'rooms' && (
              <div className="config-section">
                <div className="config-section-header">
                  <h3>Select Rooms to Use</h3>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => toggleAll('room_ids', rooms.map(r => r.id))}
                  >
                    {config.room_ids.length === rooms.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                <div className="checkbox-grid">
                  {rooms.map(r => (
                    <label key={r.id} className={`checkbox-card ${config.room_ids.includes(r.id) ? 'selected' : ''}`}>
                      <input
                        type="checkbox"
                        checked={config.room_ids.includes(r.id)}
                        onChange={() => toggleId('room_ids', r.id)}
                      />
                      <div className="checkbox-card-content">
                        <span className="checkbox-code">{r.room_number}</span>
                        <span className="checkbox-name">📍 {r.building}</span>
                        <span className="checkbox-meta">{r.room_type} · {r.capacity} seats</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* ── Time Slots tab ────────────────────────────────────────── */}
            {configTab === 'timeslots' && (
              <div className="config-section">
                <div className="config-section-header">
                  <h3>Select Allowed Time Slots</h3>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => toggleAll('timeslot_ids', timeslots.map(ts => ts.id))}
                  >
                    {config.timeslot_ids.length === timeslots.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                {Object.entries(tsByDay).map(([day, slots]) => {
                  const allDayIds = slots.map(s => s.id);
                  const allDaySelected = allDayIds.every(id => config.timeslot_ids.includes(id));
                  return (
                    <div className="ts-day-group" key={day}>
                      <div className="ts-day-header">
                        <label className="ts-day-toggle">
                          <input
                            type="checkbox"
                            checked={allDaySelected}
                            onChange={() => {
                              setConfig(prev => {
                                const newIds = allDaySelected
                                  ? prev.timeslot_ids.filter(id => !allDayIds.includes(id))
                                  : [...new Set([...prev.timeslot_ids, ...allDayIds])];
                                return { ...prev, timeslot_ids: newIds };
                              });
                            }}
                          />
                          <span className="ts-day-name">{dayLabels[day]}</span>
                        </label>
                        <span className="ts-day-count">
                          {slots.filter(s => config.timeslot_ids.includes(s.id)).length}/{slots.length}
                        </span>
                      </div>
                      <div className="ts-slot-row">
                        {slots.map(ts => (
                          <label
                            key={ts.id}
                            className={`ts-slot-chip ${config.timeslot_ids.includes(ts.id) ? 'selected' : ''}`}
                          >
                            <input
                              type="checkbox"
                              checked={config.timeslot_ids.includes(ts.id)}
                              onChange={() => toggleId('timeslot_ids', ts.id)}
                            />
                            {ts.start_time?.substring(0, 5)} – {ts.end_time?.substring(0, 5)}
                          </label>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── Constraints tab ───────────────────────────────────────── */}
            {configTab === 'constraints' && (
              <div className="config-section">
                <h3 style={{ marginBottom: '1rem' }}>Per-Subject Constraints</h3>

                {/* Excluded slots per subject */}
                <div className="constraint-group">
                  <h4 className="constraint-title">🚫 Excluded Time Slots</h4>
                  <p className="constraint-desc">Block specific time slots for each subject</p>
                  <div className="constraint-subjects">
                    {subjects.filter(s => config.subject_ids.includes(s.id)).map(s => (
                      <details key={s.id} className="constraint-detail">
                        <summary className="constraint-summary">
                          <span className="checkbox-code">{s.code}</span>
                          <span>{s.name}</span>
                          {(config.excluded_slots[s.id] || []).length > 0 && (
                            <span className="constraint-count">
                              {(config.excluded_slots[s.id] || []).length} blocked
                            </span>
                          )}
                        </summary>
                        <div className="constraint-slots">
                          {Object.entries(tsByDay).map(([day, slots]) => (
                            <div className="constraint-day" key={day}>
                              <span className="constraint-day-label">{dayLabels[day]}</span>
                              <div className="constraint-chips">
                                {slots
                                  .filter(ts => config.timeslot_ids.includes(ts.id))
                                  .map(ts => {
                                    const isExcluded = (config.excluded_slots[s.id] || []).includes(ts.id);
                                    return (
                                      <button
                                        key={ts.id}
                                        className={`constraint-chip ${isExcluded ? 'excluded' : ''}`}
                                        onClick={() => toggleExcludedSlot(s.id, ts.id)}
                                      >
                                        {ts.start_time?.substring(0, 5)}
                                        {isExcluded && ' ✕'}
                                      </button>
                                    );
                                  })}
                              </div>
                            </div>
                          ))}
                        </div>
                      </details>
                    ))}
                  </div>
                </div>

                {/* Preferred room type per subject */}
                <div className="constraint-group" style={{ marginTop: '1.5rem' }}>
                  <h4 className="constraint-title">🏠 Preferred Room Type</h4>
                  <p className="constraint-desc">Set room type preference per subject (solver tries preferred type first)</p>
                  <div className="pref-grid">
                    {subjects.filter(s => config.subject_ids.includes(s.id)).map(s => (
                      <div key={s.id} className="pref-row">
                        <span className="pref-label">
                          <span className="checkbox-code">{s.code}</span>
                          {s.name}
                        </span>
                        <select
                          className="form-select pref-select"
                          value={config.preferred_room_types[s.id] || ''}
                          onChange={(e) => setPreferredRoomType(s.id, e.target.value)}
                        >
                          <option value="">Any</option>
                          <option value="lecture">Lecture Hall</option>
                          <option value="lab">Laboratory</option>
                          <option value="seminar">Seminar Room</option>
                        </select>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── Advanced tab ──────────────────────────────────────────── */}
            {configTab === 'advanced' && (
              <div className="config-section">
                <h3 style={{ marginBottom: '1rem' }}>Advanced Settings</h3>

                <div className="advanced-options">
                  <label className="advanced-option">
                    <div className="option-toggle">
                      <input
                        type="checkbox"
                        checked={config.avoid_back_to_back}
                        onChange={(e) => setConfig(prev => ({ ...prev, avoid_back_to_back: e.target.checked }))}
                      />
                      <span className="toggle-slider" />
                    </div>
                    <div className="option-info">
                      <span className="option-label">Avoid Back-to-Back Classes</span>
                      <span className="option-desc">Prevent scheduling consecutive sessions for the same faculty member</span>
                    </div>
                  </label>

                  <div className="advanced-option">
                    <div className="option-info">
                      <span className="option-label">Max Classes Per Subject Per Day</span>
                      <span className="option-desc">Maximum number of sessions for the same subject on a single day</span>
                    </div>
                    <div className="option-control">
                      <button
                        className="stepper-btn"
                        onClick={() => setConfig(prev => ({ ...prev, max_classes_per_day: Math.max(1, prev.max_classes_per_day - 1) }))}
                      >−</button>
                      <span className="stepper-value">{config.max_classes_per_day}</span>
                      <button
                        className="stepper-btn"
                        onClick={() => setConfig(prev => ({ ...prev, max_classes_per_day: Math.min(5, prev.max_classes_per_day + 1) }))}
                      >+</button>
                    </div>
                  </div>

                  {/* Lock existing entries */}
                  {timetable.length > 0 && (
                    <div className="lock-section">
                      <h4 className="constraint-title">🔒 Lock Existing Entries</h4>
                      <p className="constraint-desc" style={{ marginBottom: '1rem' }}>
                        Lock entries in place — the generator will schedule around them.
                        Click entries in the timetable below to lock/unlock.
                        You can also drag and drop unlocked entries directly on the grid!
                      </p>
                    </div>
                  )}
                </div>

                {/* Summary */}
                <div className="config-summary">
                  <h4>Generation Summary</h4>
                  <div className="summary-items">
                    <div className="summary-item">
                      <span className="summary-label">Subjects</span>
                      <span className="summary-value">{config.subject_ids.length} of {subjects.length}</span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">Rooms</span>
                      <span className="summary-value">{config.room_ids.length} of {rooms.length}</span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">Time Slots</span>
                      <span className="summary-value">{config.timeslot_ids.length} of {timeslots.length}</span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">Locked</span>
                      <span className="summary-value">{config.locked_entries.length} entries</span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">Excluded Slots</span>
                      <span className="summary-value">
                        {Object.values(config.excluded_slots).reduce((a, b) => a + (b?.length || 0), 0)} blocked
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">Back-to-back</span>
                      <span className="summary-value">{config.avoid_back_to_back ? 'Avoided' : 'Allowed'}</span>
                    </div>
                  </div>
                  <button
                    className="btn btn-primary btn-lg"
                    onClick={handleGenerate}
                    disabled={generating || config.subject_ids.length === 0}
                    style={{ width: '100%', marginTop: '1.25rem' }}
                  >
                    {generating ? '⏳ Generating...' : `⚡ Generate Timetable (${config.subject_ids.length} subjects)`}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Timetable Grid ──────────────────────────────────────────── */}
      {timetable.length === 0 ? (
        <div className="glass-card" style={{ padding: '3rem' }}>
          <div className="empty-state">
            <div className="empty-icon">📅</div>
            <h3>No Timetable Generated</h3>
            <p>
              {isAdmin
                ? 'Click "Configure" to set constraints, then "Generate" to create a conflict-free timetable.'
                : 'The admin has not generated a timetable yet.'}
            </p>
          </div>
        </div>
      ) : (
        <LocalErrorBoundary>
          <div className="glass-card timetable-wrapper animate-fade-in-up" style={{ opacity: 0 }}>
          <div className="timetable-grid">
            <DndContext onDragEnd={handleDragEnd}>
              {/* Header row */}
              <div className="timetable-header">Time</div>
              {days.map(day => (
                <div className="timetable-header" key={day}>
                  {dayLabels[day]}
                </div>
              ))}

              {/* Time slot rows */}
              {timeSlotTimes.map(time => (
                <React.Fragment key={`row-${time}`}>
                  <div className="timetable-time" key={`time-${time}`}>
                    {time}
                  </div>
                  {days.map(day => {
                    const cls = getClassForSlot(day, time);
                    const locked = cls && isEntryLocked(cls);
                    const ts = getTimeslotForDayTime(day, time);
                    const dropId = ts ? `${day}-${time}-${ts.id}` : `${day}-${time}-unknown`;
                    
                    return (
                      <DroppableCell 
                        key={`${day}-${time}`} 
                        id={dropId} 
                      >
                        {cls && (
                          <DraggableClassCard 
                            cls={cls} 
                            isLocked={locked} 
                            color={getSubjectColor(cls.subject_code, cls.subject_type)} 
                            isAdmin={isAdmin} 
                            showConfig={showConfig}
                            onLockToggle={toggleDBLockEntry}
                          />
                        )}
                      </DroppableCell>
                    );
                  })}
                </React.Fragment>
              ))}
            </DndContext>
          </div>
        </div>
      </LocalErrorBoundary>
      )}

      {/* Legend */}
      {timetable.length > 0 && (
        <div className="glass-card timetable-legend animate-fade-in-up stagger-3" style={{ opacity: 0, marginTop: '1.5rem', padding: '1.5rem' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>Subjects</h3>
          <div className="legend-items">
            {[...new Set(timetable.map(t => t.subject_code))].map(code => {
              const entry = timetable.find(t => t.subject_code === code);
              return (
                <div className="legend-item" key={code}>
                  <div style={{ position: 'relative', width: '1rem', height: '1rem', borderRadius: '4px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer' }}>
                    <input
                      type="color"
                      value={customColors[code] || '#5b6cf9'}
                      onChange={(e) => handleColorChange(code, e.target.value)}
                      style={{ position: 'absolute', top: '-10px', left: '-10px', width: '40px', height: '40px', cursor: 'pointer', border: 'none', padding: 0 }}
                      title="Change color"
                    />
                    <div
                      style={{ position: 'absolute', inset: 0, background: getSubjectColor(code, entry?.subject_type), pointerEvents: 'none' }}
                    />
                  </div>
                  <span className="legend-code">{code}</span>
                  <span className="legend-name">{entry?.subject_name}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
