import toast from 'react-hot-toast';
import React, { useState, useEffect, useRef } from 'react';
import { DndContext, useDraggable, useDroppable } from '@dnd-kit/core';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import LocalErrorBoundary from '../../components/LocalErrorBoundary';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import './TimetablePage.css';
import {
  normalizeBreaks, describeRow, slotOverlapsBreak, addBreak,
  removeHourFromBreaks, isTimeInBreak, toMinutes, fromMinutes, formatClock,
} from './breakUtils';

/* ── Drag & Drop Components ───────────────────────────────────── */
const DraggableClassCard = ({ cls, isLocked, color, isAdmin, isFaculty, isOwnClass, onLockToggle, showConfig, onReportAbsence, onFindSwap }) => {
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
        <div className="class-name" style={{ fontSize: cls.event_type === 'office_hours' ? '0.9rem' : undefined }}>{cls.subject_code || cls.event_title}</div>
        <div className="class-room">📍 {cls.room_number}</div>
        {cls.faculty_name && <div className="class-room">{cls.faculty_name}</div>}
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
      <button 
        className="wayfinding-btn"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          // Dispatch custom event to open wayfinding
          document.dispatchEvent(new CustomEvent('open-wayfinding', { detail: cls.room_number }));
        }}
        style={{ position: 'absolute', bottom: '4px', right: '4px', fontSize: '10px', background: 'var(--color-bg-glass)', border: 'none', borderRadius: '4px', padding: '2px 4px', cursor: 'pointer', color: 'inherit' }}
      >
        🗺️
      </button>

      {isFaculty && isOwnClass && (
        <button
          className="report-absence-btn"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onReportAbsence(cls);
          }}
          style={{ position: 'absolute', bottom: '4px', left: '4px', fontSize: '10px', background: 'var(--color-accent-red)', border: 'none', borderRadius: '4px', padding: '2px 4px', cursor: 'pointer', color: 'white' }}
          title="Report Absence for this class"
        >
          🚨
        </button>
      )}

      {(isAdmin || (isFaculty && isOwnClass)) && (
        <button
          className="find-swap-btn"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onFindSwap(cls);
          }}
          style={{ position: 'absolute', bottom: '4px', left: (isFaculty && isOwnClass) ? '28px' : '4px', fontSize: '10px', background: 'var(--color-accent-blue)', border: 'none', borderRadius: '4px', padding: '2px 4px', cursor: 'pointer', color: 'white' }}
          title={isAdmin ? "Find Smart Swap" : "Request Swap"}
        >
          🔄
        </button>
      )}
    </div>
  );
};

const DroppableCell = ({ id, isValidDrop, children }) => {
  const { isOver, setNodeRef } = useDroppable({ id });

  let bg = undefined;
  let borderColor = undefined;
  if (isOver) {
    bg = isValidDrop === false ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)';
    borderColor = isValidDrop === false ? 'var(--color-accent-red)' : 'var(--color-accent-emerald)';
  } else if (isValidDrop === true) {
    bg = 'rgba(16, 185, 129, 0.05)';
    borderColor = 'rgba(16, 185, 129, 0.5)';
  } else if (isValidDrop === false) {
    bg = 'rgba(239, 68, 68, 0.02)';
    borderColor = 'rgba(239, 68, 68, 0.2)';
  }

  return (
    <div
      ref={setNodeRef}
      className={`timetable-cell ${isOver ? 'drop-target' : ''}`}
      style={{
        backgroundColor: bg || undefined,
        border: borderColor ? `1px dashed ${borderColor}` : undefined,
        transition: 'all 0.2s ease'
      }}
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
  const { user, isAdmin, isFaculty } = useAuth();
  const userFullName = user ? `${user.first_name} ${user.last_name}` : '';

  /* ── Reference data for configuration ───────────────────────────── */
  const [subjects, setSubjects] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [timeslots, setTimeslots] = useState([]);
  const [institutionSettings, setInstitutionSettings] = useState({ start_time: '08:00', end_time: '19:00', default_breaks: [] });

  /* ── Filter state ───────────────────────────────────────────────── */
  const [filterType, setFilterType] = useState('all'); // all, faculty, room
  const [filterValue, setFilterValue] = useState('');

  /* ── Department & Resource state ────────────────────────────────── */
  const [departments, setDepartments] = useState([]);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState('');
  const [resources, setResources] = useState([]);

  /* ── Mobile/Wayfinding state ────────────────────────────────────── */
  const [mobileDay, setMobileDay] = useState('MON');
  const [wayfindingRoom, setWayfindingRoom] = useState(null);

  /* ── Drag and Drop Active Item ──────────────────────────────────── */
  const [activeDragItem, setActiveDragItem] = useState(null);

  /* ── Smart Swaps state ──────────────────────────────────────────── */
  const [showSmartSwapModal, setShowSmartSwapModal] = useState(false);
  const [swapClass, setSwapClass] = useState(null);
  const [swapSuggestions, setSwapSuggestions] = useState([]);
  const [pendingSwaps, setPendingSwaps] = useState([]);
  const [swapReason, setSwapReason] = useState('');

  /* ── Add Event state ────────────────────────────────────────────── */
  const [showAddEventModal, setShowAddEventModal] = useState(false);
  const [addEventSlot, setAddEventSlot] = useState(null);
  const [newEvent, setNewEvent] = useState({ title: '', color: '#3b82f6', room: '' });

  /* ── Sandbox Version state ──────────────────────────────────────── */
  const [versions, setVersions] = useState([]);
  const [selectedVersionId, setSelectedVersionId] = useState('');
  const [draftName, setDraftName] = useState('New Draft');

  /* ── Report Absence state ───────────────────────────────────────── */
  const [showAbsenceModal, setShowAbsenceModal] = useState(false);
  const [absenceClass, setAbsenceClass] = useState(null);
  const [absenceReason, setAbsenceReason] = useState('');

  /* ── Substitute Requests state ──────────────────────────────────── */
  const [pendingSubstitutes, setPendingSubstitutes] = useState([]);


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
    balance_faculty_workload: false,
    auto_schedule_office_hours: false,
    exam_mode: false,
    breaks: normalizeBreaks(institutionSettings?.default_breaks),
  });

  const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const dayLabels = {
    MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday',
    THU: 'Thursday', FRI: 'Friday', SAT: 'Saturday',
  };

  /* ── Effective hours & breaks (department override -> global settings) ── */
  const activeDept = departments.find(d => String(d.id) === String(selectedDepartmentId));
  const effectiveStart = (activeDept?.start_time || institutionSettings?.start_time || '08:00').substring(0, 5);
  const effectiveEnd = (activeDept?.end_time || institutionSettings?.end_time || '19:00').substring(0, 5);

  /* Rows are derived from the effective hours plus the real time slots. Breaks never add rows
     and nothing is treated as a break unless it lies inside a configured break range. */
  const generateTimeRange = (start, end) => {
    const times = [];
    for (let m = toMinutes(start); m < toMinutes(end); m += 60) times.push(fromMinutes(m));
    return times;
  };

  const baseTimes = generateTimeRange(effectiveStart, effectiveEnd);

  const timeSlotTimes = [...new Set([
    ...baseTimes,
    ...timeslots.map(ts => ts.start_time?.substring(0, 5)),
  ])].filter(Boolean).sort();

  const formatTime = (timeStr) => formatClock(timeStr);

  const breaks = config.breaks || [];
  const isTimeSlotBreak = (time) => isTimeInBreak(time, breaks);

  /* Breaks as displayed in the grid: hours that already hold a scheduled class are never hidden
     behind a banner (e.g. a break added after the timetable was generated). */
  const displayBreaks = timeSlotTimes
    .filter(t => timetable.some(e => e.start_time?.substring(0, 5) === t))
    .reduce((acc, t) => removeHourFromBreaks(acc, t), breaks);

  /* Time slot ids that may be used for generation: the user's selection minus anything inside a break */
  const getEffectiveTimeslotIds = () => timeslots
    .filter(ts => config.timeslot_ids.includes(ts.id))
    .filter(ts => !slotOverlapsBreak(ts.start_time, ts.end_time, breaks))
    .map(ts => ts.id);

  /* Break editing (user edits make the config authoritative over fetched defaults) */
  const breaksDirtyRef = useRef(false);
  const updateBreaks = (updater) => {
    breaksDirtyRef.current = true;
    setConfig(prev => ({ ...prev, breaks: normalizeBreaks(typeof updater === 'function' ? updater(prev.breaks || []) : updater) }));
  };

  const saveBreaksAsDefault = async () => {
    try {
      const payload = { default_breaks: normalizeBreaks(config.breaks) };
      if (activeDept) {
        const res = await api.patch(`/api/scheduler/departments/${activeDept.id}/`, payload);
        setDepartments(prev => prev.map(d => d.id === activeDept.id ? { ...d, ...res.data } : d));
        toast.success(`Saved breaks as default for ${activeDept.name}`);
      } else {
        const res = await api.put('/api/scheduler/settings/', payload);
        setInstitutionSettings(prev => ({ ...prev, ...res.data }));
        toast.success('Saved breaks as institution default');
      }
    } catch (err) {
      toast.error(err.response?.data?.default_breaks?.[0] || 'Failed to save breaks');
    }
  };
  /* ── Load data ──────────────────────────────────────────────────── */
  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [ttRes, subRes, roomRes, tsRes, settingsRes, versionsRes, deptRes, resRes] = await Promise.all([
        api.get(`/api/scheduler/timetable/${selectedVersionId ? `?version=${selectedVersionId}` : ''}`),
        api.get('/api/scheduler/subjects/'),
        api.get('/api/scheduler/rooms/'),
        api.get('/api/scheduler/timeslots/'),
        api.get('/api/scheduler/settings/').catch(() => ({ data: { start_time: '08:00', end_time: '19:00', default_breaks: [] }})),
        api.get('/api/scheduler/versions/'),
        api.get('/api/scheduler/departments/').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/resources/').catch(() => ({ data: { results: [] } }))
      ]);
      const tt = ttRes.data.results || ttRes.data || [];
      const subs = subRes.data.results || subRes.data || [];
      const rms = roomRes.data.results || roomRes.data || [];
      const tss = tsRes.data.results || tsRes.data || [];
      const settings = settingsRes.data || { start_time: '08:00', end_time: '19:00', default_breaks: [] };
      const vers = versionsRes.data.results || versionsRes.data || [];
      const depts = deptRes.data.results || deptRes.data || [];
      const ress = resRes.data.results || resRes.data || [];

      setTimetable(tt);
      setSubjects(subs);
      setRooms(rms);
      setTimeslots(tss);
      setInstitutionSettings(settings);
      setVersions(vers);
      setDepartments(depts);
      setResources(ress);

      if (isFaculty || isAdmin) {
          api.get('/api/scheduler/absences/').then(res => {
              setPendingSubstitutes((res.data.results || res.data || []).filter(a => a.status === 'pending' && a.faculty_name !== userFullName));
          }).catch(console.error);
          api.get('/api/scheduler/swaps/').then(res => {
              setPendingSwaps((res.data.results || res.data || []).filter(s => s.status === 'pending'));
          }).catch(console.error);
      }

      if (!selectedVersionId && vers.length > 0) {
          const published = vers.find(v => v.is_published);
          if (published) setSelectedVersionId(published.id);
      }

      // Initialize config with all selected
      setConfig(prev => ({
        ...prev,
        subject_ids: subs.map(s => s.id),
        room_ids: rms.map(r => r.id),
        timeslot_ids: tss.map(ts => ts.id),
        breaks: breaksDirtyRef.current ? prev.breaks : normalizeBreaks(settings.default_breaks),
      }));
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  /* ── Generate with config ───────────────────────────────────────── */
  const handleGenerate = async () => {
    if (!draftName.trim()) return toast.error("Please provide a Draft Name");
    setGenerating(true);
    try {
      const payload = { ...config, draft_name: draftName };
      // Breaks are sent as ranges; time slots inside any break are never offered to the solver.
      payload.custom_breaks = normalizeBreaks(config.breaks);
      delete payload.breaks;
      payload.timeslot_ids = getEffectiveTimeslotIds();
      if (payload.timeslot_ids.length === 0) {
        setGenerating(false);
        return toast.error('No time slots left to schedule: every selected slot falls inside a break.');
      }
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
        if (response.data.version_id) setSelectedVersionId(response.data.version_id);
        toast(response.data.message);
        loadAll(); // Reload versions
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

  const handleDragStart = (event) => {
    setActiveDragItem(event.active.id);
  };

  const handleDragEnd = async (event) => {
    setActiveDragItem(null);
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

  const handleColorChange = async (subjectCode, color) => {
    const newColors = { ...customColors, [subjectCode]: color };
    setCustomColors(newColors);
    localStorage.setItem('timetableColors', JSON.stringify(newColors));
    
    const subject = subjects.find(s => s.code === subjectCode);
    if (subject) {
      try {
        await api.patch(`/api/scheduler/subjects/${subject.id}/`, { color_code: color });
      } catch (err) {
        console.error('Failed to update subject color', err);
      }
    }
  };

  const getClassForSlot = (day, time) => {
    return timetable.find(entry => {
      if (entry.day !== day || entry.start_time?.substring(0, 5) !== time) return false;
      if (filterType === 'faculty' && filterValue && entry.faculty_name !== filterValue) return false;
      if (filterType === 'room' && filterValue && entry.room_number !== filterValue) return false;
      if (filterType === 'resource' && filterValue) {
        // If the entry's subject or room requires this resource, show it
        const room = rooms.find(r => r.room_number === entry.room_number);
        const subject = subjects.find(s => s.code === entry.subject_code);
        const resId = parseInt(filterValue);
        const hasRes = (room?.amenities?.includes(resId)) || (subject?.amenities?.includes(resId));
        if (!hasRes) return false;
      }
      return true;
    });
  };

  const getTimeslotForDayTime = (day, time) => {
    return timeslots.find(ts => ts.day === day && ts.start_time?.substring(0, 5) === time);
  };

  const getSubjectColor = (cls) => {
    if (cls.event_color) return cls.event_color;
    if (cls.subject_code && customColors[cls.subject_code]) return customColors[cls.subject_code];
    const subject = subjects.find(s => s.code === cls.subject_code);
    if (subject?.color_code) return subject.color_code;
    switch (cls.subject_type?.toLowerCase()) {
      case "lecture":  return "var(--gradient-primary)";
      case "lab":      return "var(--gradient-emerald)";
      case "seminar":  return "var(--gradient-pink)";
      default:         return "var(--gradient-dark)";
    }
  };

  /**
   * Export the timetable to PDF. The capture always uses a fixed light "print" palette
   * (`.pdf-export-theme`), so the result is identical whether the app is in light or dark mode.
   */
  const exportToPDF = async () => {
    const element = document.getElementById('timetable-export-wrapper');
    if (!element) return;
    const toastId = toast.loading('Generating PDF...');
    try {
      const exportWidth = 1400; // fixed layout width: independent of screen size / media queries
      const canvas = await html2canvas(element, {
        scale: 2,
        backgroundColor: '#ffffff',
        useCORS: true,
        windowWidth: exportWidth,
        width: exportWidth,
        onclone: (clonedDoc, clonedEl) => {
          clonedDoc.body.classList.remove('light-theme');
          clonedEl.classList.add('pdf-export-theme');
          clonedEl.style.opacity = '1';
          clonedEl.style.animation = 'none';
          clonedEl.style.transform = 'none';
          clonedEl.style.width = `${exportWidth}px`;
          // Remove interactive controls so the printout is clean.
          clonedEl.querySelectorAll('.wayfinding-btn, .find-swap-btn, .report-absence-btn, .lock-icon, .class-card button')
            .forEach(n => n.remove());
          // Title block
          const versionName = versions.find(v => String(v.id) === String(selectedVersionId))?.name;
          const parts = ['Timetable'];
          if (activeDept) parts.push(activeDept.name);
          if (versionName) parts.push(versionName);
          const header = clonedDoc.createElement('div');
          header.className = 'pdf-export-title';
          header.textContent = `${parts.join(' - ')}  |  Exported ${new Date().toLocaleDateString()}`;
          clonedEl.insertBefore(header, clonedEl.firstChild);
        },
      });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('l', 'mm', 'a4');
      const margin = 8;
      const maxW = pdf.internal.pageSize.getWidth() - margin * 2;
      const maxH = pdf.internal.pageSize.getHeight() - margin * 2;
      // Fit to a single page, preserving aspect ratio.
      const ratio = Math.min(maxW / canvas.width, maxH / canvas.height);
      const w = canvas.width * ratio;
      const h = canvas.height * ratio;
      pdf.addImage(imgData, 'PNG', margin + (maxW - w) / 2, margin, w, h);
      pdf.save('Timetable.pdf');
      toast.success('PDF Exported!', { id: toastId });
    } catch (err) {
      console.error('PDF export failed:', err);
      toast.error('Failed to export PDF', { id: toastId });
    }
  };
  useEffect(() => {
    const handleWayfinding = (e) => {
      setWayfindingRoom(e.detail);
    };
    document.addEventListener('open-wayfinding', handleWayfinding);
    return () => document.removeEventListener('open-wayfinding', handleWayfinding);
  }, []);

  useEffect(() => {
      loadAll();
  }, [selectedVersionId]);

  const handlePublishVersion = async () => {
      if (!selectedVersionId) return;
      try {
          await api.patch(`/api/scheduler/versions/${selectedVersionId}/`, { is_published: true });
          toast.success("Timetable version published successfully!");
          loadAll();
      } catch (err) {
          toast.error("Failed to publish version");
      }
  };

  const handleReportAbsence = async () => {
    if (!absenceReason) return toast.error("Reason is required");
    try {
        // Find date for next occurrence of this day (simplified)
        const date = new Date().toISOString().split('T')[0]; // Current date as placeholder
        await api.post('/api/scheduler/absences/', {
            date: date,
            reason: `For class ${absenceClass.subject_code} at ${absenceClass.time_slot}: ${absenceReason}`,
            timetable_entry: absenceClass.id
        });
        toast.success("Absence reported & substitute request broadcasted!");
        setShowAbsenceModal(false);
        setAbsenceReason('');
        loadAll(); // Reload to show in substitute list if testing
    } catch (err) {
        toast.error("Failed to report absence");
    }
  };

  const handleAcceptSubstitute = async (absenceId) => {
    try {
        await api.patch(`/api/scheduler/absences/${absenceId}/`, {
            status: 'approved', // For testing, auto-approve
            substitute_id: user.id // Needs proper backend mapping but okay for mock
        });
        toast.success("You have accepted the substitute request!");
        loadAll();
    } catch (err) {
        toast.error("Failed to accept substitute request");
    }
  };

  const handleFindSwap = async (cls) => {
      setSwapClass(cls);
      setShowSmartSwapModal(true);
      if (isAdmin) {
          try {
              const res = await api.get(`/api/scheduler/timetable/${cls.id}/smart-swaps/`);
              setSwapSuggestions(res.data.suggestions || []);
          } catch (err) {
              toast.error("Failed to fetch smart swaps");
          }
      }
  };

  const executeSmartSwap = async (suggestion) => {
      try {
          await api.patch(`/api/scheduler/timetable/${swapClass.id}/`, {
              time_slot: suggestion.target_slot_id
          });
          toast.success("Smart swap executed!");
          setShowSmartSwapModal(false);
          loadAll();
      } catch (err) {
          toast.error("Failed to execute swap");
      }
  };

  const requestSmartSwap = async (targetSlotId) => {
      try {
          await api.post(`/api/scheduler/swaps/`, {
              target_entry: swapClass.id,
              requested_time_slot: targetSlotId,
              reason: swapReason
          });
          toast.success("Swap request sent to admin!");
          setShowSmartSwapModal(false);
          loadAll();
      } catch (err) {
          toast.error("Failed to request swap");
      }
  };

  const approveSwapRequest = async (swapId) => {
      try {
          await api.patch(`/api/scheduler/swaps/${swapId}/`, { status: 'approved' });
          toast.success("Swap request approved and applied!");
          loadAll();
      } catch (err) {
          toast.error("Failed to approve swap");
      }
  };

  /* ── Fairness Metric ────────────────────────────────────────────── */
  const getWorkloadMetric = () => {
     if (timetable.length === 0) return "N/A";
     const counts = {};
     timetable.forEach(t => {
         if (t.event_type === 'office_hours') return;
         if (!t.faculty_name) return;
         const key = `${t.faculty_name}-${t.day}`;
         counts[key] = (counts[key] || 0) + 1;
     });
     const values = Object.values(counts);
     if (values.length === 0) return "N/A";
     const max = Math.max(...values);
     const avg = (values.reduce((a,b)=>a+b,0)/values.length).toFixed(1);
     // Score from 0 to 100 based on standard deviation or max diff. 
     // Simple metric: if max > avg by a lot, score is lower.
     const diff = max - avg;
     const score = Math.max(0, 100 - (diff * 20)).toFixed(0);
     return `${score}/100 (Max ${max}/day)`;
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
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <select 
             className="form-select" 
             style={{ width: 'auto' }}
             value={filterType}
             onChange={(e) => {
               setFilterType(e.target.value);
               setFilterValue('');
             }}
          >
            <option value="all">All Classes</option>
            <option value="faculty">Filter by Faculty</option>
            <option value="room">Filter by Room</option>
            <option value="resource">Filter by Resource</option>
          </select>
          {filterType === 'faculty' && (
            <select className="form-select" style={{ width: 'auto' }} value={filterValue} onChange={(e) => setFilterValue(e.target.value)}>
              <option value="">Select Faculty...</option>
              {[...new Set(timetable.map(t => t.faculty_name).filter(Boolean))].map(f => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
          )}
          {filterType === 'room' && (
            <select className="form-select" style={{ width: 'auto' }} value={filterValue} onChange={(e) => setFilterValue(e.target.value)}>
              <option value="">Select Room...</option>
              {[...new Set(timetable.map(t => t.room_number).filter(Boolean))].map(r => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          )}
          {filterType === 'resource' && (
            <select className="form-select" style={{ width: 'auto' }} value={filterValue} onChange={(e) => setFilterValue(e.target.value)}>
              <option value="">Select Resource/Amenity...</option>
              {resources.map(r => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          )}

          <button className="btn btn-secondary" onClick={exportToPDF}>
            📥 Export PDF
          </button>
          
          {isAdmin && (
            <>
              {versions.length > 0 && (
                 <select 
                   className="form-select" 
                   style={{ width: 'auto', background: 'rgba(59, 130, 246, 0.1)', borderColor: 'var(--color-accent-blue)', color: 'var(--color-accent-blue-light)', fontWeight: 'bold' }}
                   value={selectedVersionId}
                   onChange={(e) => setSelectedVersionId(e.target.value)}
                 >
                   <option value="">-- Select Sandbox Version --</option>
                   {versions.map(v => (
                      <option key={v.id} value={v.id}>{v.name} {v.is_published ? '(Live)' : '(Draft)'}</option>
                   ))}
                 </select>
              )}
              
              {selectedVersionId && !versions.find(v => v.id == selectedVersionId)?.is_published && (
                  <button className="btn btn-primary" style={{ background: 'var(--color-accent-emerald)', borderColor: 'var(--color-accent-emerald)' }} onClick={handlePublishVersion}>
                      🚀 Publish Draft
                  </button>
              )}

              <button
                className="btn btn-secondary"
                onClick={() => setShowConfig(!showConfig)}
                id="btn-configure-generator"
              >
                ⚙️ {showConfig ? 'Hide Config' : 'New Sandbox Draft'}
              </button>
            <button
              className="btn btn-primary"
              onClick={() => showConfig ? handleGenerate() : setShowConfig(true)}
              disabled={generating}
              id="btn-generate-timetable"
            >
              {generating ? '⏳ Generating...' : '⚡ Generate'}
            </button>
            </>
          )}
        </div>
      </div>

      {/* ── Configuration Panel ─────────────────────────────────────── */}
      {isAdmin && showConfig && (
        <div className="config-panel glass-card animate-fade-in-up" style={{ opacity: 0 }}>
          <div className="config-header">
            <h2>🎛️ Generator Configuration</h2>
            <p>Fine-tune which resources to include and set scheduling constraints</p>
            <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <label style={{ fontWeight: 600 }}>Target Department:</label>
              <select 
                 className="form-select"
                 value={selectedDepartmentId}
                 onChange={(e) => {
                   const newDeptId = e.target.value;
                   setSelectedDepartmentId(newDeptId);
                    {
                      const dept = departments.find(d => String(d.id) === String(newDeptId));
                      const deptBreaks = normalizeBreaks(dept?.default_breaks);
                      breaksDirtyRef.current = true;
                      setConfig(prev => ({ ...prev, breaks: deptBreaks.length > 0 ? deptBreaks : normalizeBreaks(institutionSettings?.default_breaks) }));
                    }
                   if (newDeptId) {
                     const did = parseInt(newDeptId);
                     const filteredSubIds = subjects.filter(s => s.departments?.includes(did) || s.is_elective).map(s => s.id);
                     const filteredRoomIds = rooms.filter(r => r.departments?.includes(did) || !r.departments || r.departments.length === 0).map(r => r.id);
                     setConfig(prev => ({ ...prev, subject_ids: filteredSubIds, room_ids: filteredRoomIds }));
                   } else {
                     setConfig(prev => ({ ...prev, subject_ids: subjects.map(s => s.id), room_ids: rooms.map(r => r.id) }));
                   }
                 }}
              >
                 <option value="">All Departments (Global)</option>
                 {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                 ))}
              </select>
            </div>
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
                            {formatTime(ts.start_time)} – {formatTime(ts.end_time)}
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
                  <div className="advanced-option" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                    <div className="option-info" style={{ marginBottom: '1rem' }}>
                      <span className="option-label">☕ Global Break Times</span>
                      <span className="option-desc">Add as many breaks as you need. A break can be one slot (10 AM) or a continuous range (12 PM - 3 PM), and you can mix both (e.g. 10 AM, 12 PM-3 PM and 4 PM). Classes are never scheduled inside a break, and each break appears as a BREAK banner on the timetable.</span>
                    </div>
                    <div className="break-manager" id="break-manager">
                      <div className="break-quick-row">
                        <span className="break-quick-label">Quick toggle (1 hour):</span>
                        <div className="ts-slot-row" style={{ marginLeft: 0 }}>
                          {timeSlotTimes.map(time => {
                            const isBreak = isTimeSlotBreak(time);
                            return (
                              <label key={time} className={`ts-slot-chip ${isBreak ? 'selected' : ''}`} style={isBreak ? { borderColor: 'rgba(239, 68, 68, 0.5)', color: 'var(--color-accent-red)', background: 'rgba(239, 68, 68, 0.1)' } : {}}>
                                <input
                                  type="checkbox"
                                  checked={isBreak}
                                  onChange={(e) => {
                                    if (e.target.checked) updateBreaks(prev => addBreak(prev, time, fromMinutes(toMinutes(time) + 60)));
                                    else updateBreaks(prev => removeHourFromBreaks(prev, time));
                                  }}
                                />
                                {formatTime(time)} {isBreak ? '(Break)' : ''}
                              </label>
                            );
                          })}
                        </div>
                      </div>

                      <div className="break-list">
                        {breaks.length === 0 && <div className="break-empty">No breaks configured. Classes can be scheduled in every slot.</div>}
                        {breaks.map((b, idx) => {
                          const hourOptions = [...new Set([...generateTimeRange(effectiveStart, effectiveEnd), b.start, b.end, effectiveEnd])].sort();
                          const isRange = toMinutes(b.end) - toMinutes(b.start) > 60;
                          const patchBreak = (patch) => updateBreaks(prev => prev.map((x, i) => {
                            if (i !== idx) return x;
                            const next = { ...x, ...patch };
                            if (toMinutes(next.end) <= toMinutes(next.start)) next.end = fromMinutes(toMinutes(next.start) + 60);
                            return next;
                          }));
                          return (
                            <div className="break-row" key={`${b.start}-${idx}`}>
                              <span className="break-badge">{isRange ? 'Continuous' : 'Single'}</span>
                              <select className="form-select break-select" value={b.start} aria-label="Break start" onChange={(e) => patchBreak({ start: e.target.value })}>
                                {hourOptions.filter(t => t !== effectiveEnd || t === b.start).map(t => <option key={t} value={t}>{formatTime(t)}</option>)}
                              </select>
                              <span className="break-to">to</span>
                              <select className="form-select break-select" value={b.end} aria-label="Break end" onChange={(e) => patchBreak({ end: e.target.value })}>
                                {hourOptions.filter(t => toMinutes(t) > toMinutes(b.start)).map(t => <option key={t} value={t}>{formatTime(t)}</option>)}
                              </select>
                              <input
                                type="text"
                                className="form-input break-label-input"
                                placeholder="Label (e.g. Lunch)"
                                value={b.label || ''}
                                maxLength={30}
                                onChange={(e) => patchBreak({ label: e.target.value })}
                              />
                              <button type="button" className="btn btn-sm btn-secondary break-remove" title="Remove break" onClick={() => updateBreaks(prev => prev.filter((_, i) => i !== idx))}>✕</button>
                            </div>
                          );
                        })}
                      </div>

                      <div className="break-actions">
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => {
                            const free = timeSlotTimes.find(t => !isTimeSlotBreak(t));
                            if (!free) return toast.error('Every hour is already a break.');
                            updateBreaks(prev => addBreak(prev, free, fromMinutes(toMinutes(free) + 60)));
                          }}
                        >
                          ＋ Add Break
                        </button>
                        <button type="button" className="btn btn-sm btn-secondary" onClick={saveBreaksAsDefault}>
                          💾 Save as default{activeDept ? ` for ${activeDept.name}` : ''}
                        </button>
                        <button type="button" className="btn btn-sm btn-secondary" disabled={breaks.length === 0} onClick={() => updateBreaks([])}>
                          Clear all
                        </button>
                      </div>
                    </div>
                  </div>
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
                  
                  <label className="advanced-option">
                    <div className="option-toggle">
                      <input
                        type="checkbox"
                        checked={config.balance_faculty_workload}
                        onChange={(e) => setConfig(prev => ({ ...prev, balance_faculty_workload: e.target.checked }))}
                      />
                      <span className="toggle-slider" />
                    </div>
                    <div className="option-info">
                      <span className="option-label">Balance Faculty Workload</span>
                      <span className="option-desc">Avoid giving any single faculty member an extreme concentration of classes on a single day</span>
                    </div>
                  </label>

                  <label className="advanced-option">
                    <div className="option-toggle">
                      <input
                        type="checkbox"
                        checked={config.auto_schedule_office_hours}
                        onChange={(e) => setConfig(prev => ({ ...prev, auto_schedule_office_hours: e.target.checked }))}
                      />
                      <span className="toggle-slider" />
                    </div>
                    <div className="option-info">
                      <span className="option-label">Auto-Schedule Office Hours</span>
                      <span className="option-desc">Automatically create 1 Office Hour block per faculty in their free time slots</span>
                    </div>
                  </label>

                  <label className="advanced-option">
                    <div className="option-toggle">
                      <input
                        type="checkbox"
                        checked={config.exam_mode}
                        onChange={(e) => setConfig(prev => ({ ...prev, exam_mode: e.target.checked }))}
                      />
                      <span className="toggle-slider" />
                    </div>
                    <div className="option-info">
                      <span className="option-label">Exam Mode (Beta)</span>
                      <span className="option-desc">Generate an exam schedule (1 session per subject) instead of a weekly class schedule</span>
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
                    <div className="summary-item">
                      <span className="summary-label">Fairness Score</span>
                      <span className="summary-value" style={{ color: 'var(--color-accent-emerald)', fontWeight: 600 }}>{getWorkloadMetric()}</span>
                    </div>
                    {config.exam_mode && (
                      <div className="summary-item">
                        <span className="summary-label">Mode</span>
                        <span className="summary-value" style={{ color: 'var(--color-accent-red)', fontWeight: 600 }}>EXAM</span>
                      </div>
                    )}
                  </div>
                  
                  <div style={{ marginTop: '1rem' }}>
                    <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Draft Name</label>
                    <input type="text" className="form-input" style={{ width: '100%' }} value={draftName} onChange={e => setDraftName(e.target.value)} />
                  </div>

                  <button
                    className="btn btn-primary btn-lg"
                    onClick={handleGenerate}
                    disabled={generating || config.subject_ids.length === 0}
                    style={{ width: '100%', marginTop: '1.25rem' }}
                  >
                    {generating ? '⏳ Generating Draft...' : `⚡ Generate Draft (${config.subject_ids.length} subjects)`}
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
          {/* Mobile Day Selector */}
          <div className="mobile-day-selector">
            <button className="btn btn-sm btn-secondary" onClick={() => setMobileDay(days[Math.max(0, days.indexOf(mobileDay) - 1)])}>&lt; Prev</button>
            <span style={{ fontWeight: 'bold' }}>{dayLabels[mobileDay]}</span>
            <button className="btn btn-sm btn-secondary" onClick={() => setMobileDay(days[Math.min(days.length - 1, days.indexOf(mobileDay) + 1)])}>Next &gt;</button>
          </div>

          <div id="timetable-export-wrapper" className="glass-card timetable-wrapper animate-fade-in-up" style={{ opacity: 0 }}>
          <div className="timetable-grid">
            <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
              {/* Header row */}
              <div className="timetable-header">Time</div>
              {days.map(day => (
                <div className={`timetable-header ${day === mobileDay ? 'mobile-active' : 'mobile-hidden'}`} key={day}>
                  {dayLabels[day]}
                </div>
              ))}

              {/* Time slot rows */}
              {timeSlotTimes.map(time => {
                const row = describeRow(time, timeSlotTimes, displayBreaks);
                // Continuous breaks render once (first row) and span all covered rows.
                if (row.isBreak && !row.isFirstRow) return null;
                const isBreak = row.isBreak;
                return (
                <React.Fragment key={`row-${time}`}>
                  <div className="timetable-time" key={`time-${time}`} style={isBreak && row.span > 1 ? { gridRow: `span ${row.span}` } : undefined}>
                    {isBreak && row.span > 1 ? (
                      <span style={{ textAlign: 'center', lineHeight: 1.5 }}>{formatTime(row.range.start)}<br />to<br />{formatTime(row.range.end)}</span>
                    ) : formatTime(time)}
                  </div>
                  {isBreak ? (
                    <div className="timetable-break" style={{ gridRow: `span ${row.span}` }}>
                      <span className="break-title">Break</span>
                      {row.label && <span className="break-sub">{row.label}</span>}
                    </div>
                  ) : (
                    days.map(day => {
                      const cls = getClassForSlot(day, time);
                      const locked = cls && isEntryLocked(cls);
                      const ts = getTimeslotForDayTime(day, time);
                      const dropId = ts ? `${day}-${time}-${ts.id}` : `${day}-${time}-unknown`;
                      
                      let isValidDrop = null;
                      const activeEntry = activeDragItem ? timetable.find(t => t.id === activeDragItem) : null;
                      if (activeEntry && ts) {
                        const timeConflicts = timetable.filter(t => t.day === day && t.start_time?.substring(0, 5) === time && t.id !== activeEntry.id);
                        const facultyConflict = timeConflicts.some(t => t.faculty_name === activeEntry.faculty_name);
                        // If cell already has a class in this filtered view OR faculty conflict, it's invalid
                        if (cls || facultyConflict) {
                           isValidDrop = false;
                        } else {
                           isValidDrop = true;
                        }
                      }

                      return (
                        <div className={`${day === mobileDay ? 'mobile-active' : 'mobile-hidden'}`} key={`${day}-${time}`} onClick={() => {
                          if (!cls && isAdmin && ts) {
                            setAddEventSlot(ts);
                            setShowAddEventModal(true);
                          }
                        }}>
                          <DroppableCell id={dropId} isValidDrop={isValidDrop}>
                            {cls && (
                              <DraggableClassCard 
                                cls={cls} 
                                isLocked={locked} 
                                color={getSubjectColor(cls)} 
                                isAdmin={isAdmin} 
                                isFaculty={isFaculty}
                                isOwnClass={cls.faculty_name === userFullName}
                                showConfig={showConfig}
                                onLockToggle={toggleDBLockEntry}
                                onReportAbsence={(c) => {
                                  setAbsenceClass(c);
                                  setShowAbsenceModal(true);
                                }}
                                onFindSwap={handleFindSwap}
                              />
                            )}
                          </DroppableCell>
                        </div>
                      );
                    })
                  )}
                </React.Fragment>
              )})}
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
            {[...new Set(timetable.filter(t => t.subject_code).map(t => t.subject_code))].map(code => {
              const entry = timetable.find(t => t.subject_code === code);
              return (
                <div className="legend-item" key={code}>
                  <div style={{ position: 'relative', width: '1rem', height: '1rem', borderRadius: '4px', overflow: 'hidden', border: '1px solid var(--color-border)', cursor: 'pointer' }}>
                    <input
                      type="color"
                      value={customColors[code] || '#5b6cf9'}
                      onChange={(e) => handleColorChange(code, e.target.value)}
                      style={{ position: 'absolute', top: '-10px', left: '-10px', width: '40px', height: '40px', cursor: 'pointer', border: 'none', padding: 0 }}
                      title="Change color"
                    />
                    <div
                      style={{ position: 'absolute', inset: 0, background: getSubjectColor(entry), pointerEvents: 'none' }}
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

      {/* Substitute Requests Panel */}
      {(isFaculty || isAdmin) && pendingSubstitutes.length > 0 && (
        <div className="glass-card animate-fade-in-up stagger-4" style={{ opacity: 0, marginTop: '1.5rem', padding: '1.5rem', borderLeft: '4px solid var(--color-accent-emerald)' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>🙋 Substitute Requests</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>The following classes need coverage. Click 'Accept' to substitute.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
             {pendingSubstitutes.map(sub => (
                 <div key={sub.id} style={{ padding: '1rem', background: 'var(--color-bg-glass)', border: '1px solid var(--color-border)', borderRadius: '8px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{sub.faculty_name}'s Class</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem' }}>📅 {sub.date}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '0.5rem', fontStyle: 'italic' }}>"{sub.reason}"</div>
                    <button className="btn btn-sm btn-primary" style={{ marginTop: '1rem', width: '100%', background: 'var(--color-accent-emerald)', borderColor: 'var(--color-accent-emerald)' }} onClick={() => handleAcceptSubstitute(sub.id)}>Accept Request</button>
                 </div>
             ))}
          </div>
        </div>
      )}

      {/* Pending Swaps Panel */}
      {isAdmin && pendingSwaps.length > 0 && (
        <div className="glass-card animate-fade-in-up stagger-4" style={{ opacity: 0, marginTop: '1.5rem', padding: '1.5rem', borderLeft: '4px solid var(--color-accent-blue)' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>🔄 Pending Swap Requests</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>Faculty have requested to move these classes.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
             {pendingSwaps.map(swap => (
                 <div key={swap.id} style={{ padding: '1rem', background: 'var(--color-bg-glass)', border: '1px solid var(--color-border)', borderRadius: '8px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{swap.requester_name}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem' }}>
                       Wants to move {swap.target_entry_details?.subject?.code} to {swap.requested_time_slot_details?.day} {swap.requested_time_slot_details?.start_time}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '0.5rem', fontStyle: 'italic' }}>"{swap.reason}"</div>
                    <button className="btn btn-sm btn-primary" style={{ marginTop: '1rem', width: '100%', background: 'var(--color-accent-blue)', borderColor: 'var(--color-accent-blue)' }} onClick={() => approveSwapRequest(swap.id)}>Approve Swap</button>
                 </div>
             ))}
          </div>
        </div>
      )}

      {/* Wayfinding Modal */}
      {wayfindingRoom && (
        <div className="modal-overlay" onClick={() => setWayfindingRoom(null)}>
          <div className="modal-content glass-card" onClick={e => e.stopPropagation()}>
            <h3>🗺️ Wayfinding: {wayfindingRoom}</h3>
            <p>Campus map locating room {wayfindingRoom} would appear here.</p>
            <div style={{ width: '100%', height: '200px', background: 'var(--color-bg-glass)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '1rem' }}>
              📍 [Map Placeholder]
            </div>
            <button className="btn btn-primary" style={{ marginTop: '1rem', width: '100%' }} onClick={() => setWayfindingRoom(null)}>Close</button>
          </div>
        </div>
      )}

      {/* Add Event Modal */}
      {showAddEventModal && addEventSlot && (
        <div className="modal-overlay" onClick={() => setShowAddEventModal(false)}>
          <div className="modal-content glass-card" onClick={e => e.stopPropagation()} style={{ width: '400px' }}>
            <h3>➕ Add Custom Event</h3>
            <p>Time: {addEventSlot.day} {formatTime(addEventSlot.start_time)}</p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              <input 
                type="text" 
                className="form-input" 
                placeholder="Event Title" 
                value={newEvent.title}
                onChange={e => setNewEvent({...newEvent, title: e.target.value})}
              />
              <input 
                type="text" 
                className="form-input" 
                placeholder="Room / Location" 
                value={newEvent.room}
                onChange={e => setNewEvent({...newEvent, room: e.target.value})}
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <label>Color:</label>
                <input 
                  type="color" 
                  value={newEvent.color}
                  onChange={e => setNewEvent({...newEvent, color: e.target.value})}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowAddEventModal(false)}>Cancel</button>
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={async () => {
                if (!newEvent.title) return toast.error('Title is required');
                try {
                  const res = await api.post('/api/scheduler/timetable/', {
                    day: addEventSlot.day,
                    start_time: addEventSlot.start_time,
                    end_time: addEventSlot.end_time,
                    time_slot: addEventSlot.id,
                    event_title: newEvent.title,
                    event_color: newEvent.color,
                    event_type: 'custom',
                    room_number: newEvent.room,
                    is_locked: true // Custom events are locked by default
                  });
                  setTimetable([...timetable, res.data]);
                  setShowAddEventModal(false);
                  setNewEvent({ title: '', color: '#3b82f6', room: '' });
                  toast.success('Event added!');
                } catch (err) {
                  toast.error('Failed to add event');
                }
              }}>Save Event</button>
            </div>
          </div>
        </div>
      )}

      {/* Report Absence Modal */}
      {showAbsenceModal && absenceClass && (
        <div className="modal-overlay" onClick={() => setShowAbsenceModal(false)}>
          <div className="modal-content glass-card" onClick={e => e.stopPropagation()}>
            <h3>🚨 Report Absence</h3>
            <p>You are reporting an absence for: <strong>{absenceClass.subject_code}</strong> ({absenceClass.room_number})</p>
            <p>Time: {absenceClass.day} {formatTime(absenceClass.start_time)}</p>
            
            <div style={{ marginTop: '1rem' }}>
              <label>Reason for absence:</label>
              <textarea 
                className="form-input" 
                style={{ width: '100%', height: '80px', marginTop: '0.5rem' }} 
                placeholder="e.g. Unwell, attending conference..."
                value={absenceReason}
                onChange={(e) => setAbsenceReason(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowAbsenceModal(false)}>Cancel</button>
              <button className="btn btn-primary" style={{ flex: 1, background: 'var(--color-accent-red)', borderColor: 'var(--color-accent-red)' }} onClick={handleReportAbsence}>Broadcast Request</button>
            </div>
          </div>
        </div>
      )}

      {/* Smart Swap Modal */}
      {showSmartSwapModal && swapClass && (
        <div className="modal-overlay" onClick={() => setShowSmartSwapModal(false)}>
          <div className="modal-content glass-card" onClick={e => e.stopPropagation()} style={{ width: '450px' }}>
            <h3>🔄 {isAdmin ? 'Smart Swaps' : 'Request Swap'}</h3>
            <p>Moving: <strong>{swapClass.subject_code}</strong> ({swapClass.room_number})</p>
            <p>Current: {swapClass.day} {formatTime(swapClass.start_time)}</p>
            
            {isAdmin ? (
               <div style={{ marginTop: '1rem' }}>
                 <h4>Suggested Moves:</h4>
                 {swapSuggestions.length === 0 ? (
                    <p style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>Loading or no swaps found...</p>
                 ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                       {swapSuggestions.map((s, idx) => (
                           <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-bg-glass)', padding: '0.75rem', borderRadius: '4px' }}>
                               <span>{s.description}</span>
                               <button className="btn btn-sm btn-primary" onClick={() => executeSmartSwap(s)}>Move Here</button>
                           </div>
                       ))}
                    </div>
                 )}
               </div>
            ) : (
               <div style={{ marginTop: '1rem' }}>
                 <label>Request new timeslot:</label>
                 <select className="form-select" style={{ width: '100%', marginBottom: '1rem' }} onChange={(e) => setSwapClass({...swapClass, targetSlotId: e.target.value})}>
                    <option value="">-- Select Target Timeslot --</option>
                    {timeslots.map(ts => (
                       <option key={ts.id} value={ts.id}>{ts.day} {ts.start_time}</option>
                    ))}
                 </select>
                 
                 <label>Reason:</label>
                 <input type="text" className="form-input" style={{ width: '100%', marginBottom: '1rem' }} placeholder="e.g. Need a larger block" value={swapReason} onChange={e => setSwapReason(e.target.value)} />
                 
                 <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => requestSmartSwap(swapClass.targetSlotId)}>Submit Swap Request</button>
               </div>
            )}

            <button className="btn btn-secondary" style={{ marginTop: '1rem', width: '100%' }} onClick={() => setShowSmartSwapModal(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}