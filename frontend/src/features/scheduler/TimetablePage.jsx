import toast from 'react-hot-toast';
import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { DndContext, useDraggable, useDroppable } from '@dnd-kit/core';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import { useTaskProgress } from '../../context/TaskProgressContext';
import LocalErrorBoundary from '../../components/LocalErrorBoundary';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import './TimetablePage.css';
import {
  normalizeBreaks, describeRow, slotOverlapsBreak, addBreak,
  removeHourFromBreaks, isTimeInBreak, toMinutes, fromMinutes, formatClock,
} from './breakUtils';

export const ACADEMIC_BLOCKS = {
  "Block A": "Computing & AI",
  "Block B": "Engineering",
  "Block C": "Basic & Applied Sciences",
  "Block D": "Health Sciences",
  "Block E": "Management & Commerce",
  "Block F": "Law & Social Sciences",
  "Block G": "Arts & Humanities",
  "Block H": "Agriculture & Environmental Sciences",
  "Block I": "Interdisciplinary Studies",
};

export const DAY_CODE_MAP = {
  MON: 1,
  TUE: 2,
  WED: 3,
  THU: 4,
  FRI: 5,
  SAT: 6,
  SUN: 0,
};

export const getNextDateForDay = (dayStr) => {
  if (!dayStr) return new Date().toISOString().split('T')[0];
  const targetDay = DAY_CODE_MAP[dayStr.toUpperCase()] ?? 1;
  const now = new Date();
  const currentDay = now.getDay();
  const diff = (targetDay - currentDay + 7) % 7;
  const targetDate = new Date(now);
  targetDate.setDate(now.getDate() + diff);
  return targetDate.toISOString().split('T')[0];
};

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
        <div className="class-room">📍 {cls.room_number} {cls.block_name ? `(${cls.block_name.split(' - ')[0]})` : ''}</div>
        {cls.faculty_name && <div className="class-room">{cls.faculty_name}</div>}
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '3px', justifyContent: 'center' }}>
          {cls.subject_type === 'lab' && (
            <span style={{ fontSize: '9px', fontWeight: 700, padding: '1px 5px', borderRadius: '4px', background: 'rgba(245, 158, 11, 0.25)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.4)' }}>
              🧪 2h Lab
            </span>
          )}
          {cls.department_names && cls.department_names.length > 1 && (
            <span style={{ fontSize: '9px', fontWeight: 700, padding: '1px 5px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.25)', color: '#93c5fd', border: '1px solid rgba(59, 130, 246, 0.4)' }} title={cls.department_names.join(', ')}>
              ⚡ Merged ({cls.department_names.length})
            </span>
          )}
        </div>
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
  const [searchParams] = useSearchParams();
  const [timetable, setTimetable] = useState([]);
  const [loading, setLoading] = useState(true);
  const taskProgress = useTaskProgress();
  const generating = taskProgress.isGenerating;
  const generationProgress = taskProgress.activeTask;
  const formatSeconds = taskProgress.formatSeconds;
  const formatDurationDisplay = taskProgress.formatDurationDisplay;
  const [isProgressMinimized, setIsProgressMinimized] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const { user, isAdmin, isFaculty, isStudent } = useAuth();
  const userFullName = user ? `${user.first_name} ${user.last_name}` : '';
  const initialLoadedRef = useRef(false);
  const loadAllRef = useRef(null);

  useEffect(() => {
    const handleReload = (e) => {
      const newVersionId = e?.detail?.version_id;
      setShowConfig(false);
      if (loadAllRef.current) {
        if (newVersionId) {
          loadAllRef.current(newVersionId);
        } else {
          loadAllRef.current();
        }
      }
      setTimeout(() => {
        const el = document.getElementById('timetable-grid-section');
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 150);
    };

    const handleSwitchView = (e) => {
      const { versionId, scopeType, blockName, deptId } = e?.detail || {};
      if (scopeType === 'block' && blockName) {
        setViewMode('block');
        setViewBlock(blockName);
      } else if (scopeType === 'department' && deptId) {
        setViewMode('department');
        setViewDeptId(String(deptId));
      } else if (scopeType === 'all') {
        setViewMode('all');
      }

      setShowConfig(false);

      if (versionId && loadAllRef.current) {
        loadAllRef.current(versionId);
      }

      setTimeout(() => {
        const el = document.getElementById('timetable-grid-section');
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 150);
    };

    window.addEventListener('smartcampus:timetable-generated', handleReload);
    window.addEventListener('smartcampus:switch-timetable-view', handleSwitchView);
    return () => {
      window.removeEventListener('smartcampus:timetable-generated', handleReload);
      window.removeEventListener('smartcampus:switch-timetable-view', handleSwitchView);
    };
  }, []);

  /* ── Reference data for configuration ───────────────────────────── */
  const [subjects, setSubjects] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [timeslots, setTimeslots] = useState([]);
  const [institutionSettings, setInstitutionSettings] = useState({ start_time: '09:00', end_time: '18:00', default_breaks: [] });

  /* ── Filter state ───────────────────────────────────────────────── */
  const [filterType, setFilterType] = useState('all'); // legacy fallback
  const [filterValue, setFilterValue] = useState('');

  /* ── Multi-Timetable View Switcher state ────────────────────────── */
  const [viewMode, setViewMode] = useState('department'); // 'department', 'block', 'room', 'faculty', 'all'
  const [viewDeptId, setViewDeptId] = useState('');
  const [viewSemester, setViewSemester] = useState('');
  const [viewBlock, setViewBlock] = useState('Block A');
  const [viewRoomNumber, setViewRoomNumber] = useState('');
  const [viewFacultyName, setViewFacultyName] = useState('');
  const [viewSearchTerm, setViewSearchTerm] = useState('');

  /* ── Generator subjects & rooms dynamic state ───────────────────── */
  const [genCourses, setGenCourses] = useState([]);
  const [genCourseSearch, setGenCourseSearch] = useState('');
  const [genCoursePage, setGenCoursePage] = useState(1);
  const [genCourseTotal, setGenCourseTotal] = useState(0);
  const [genCourseLoading, setGenCourseLoading] = useState(false);
  const [genCourseLoadingMore, setGenCourseLoadingMore] = useState(false);
  const [genRoomSearch, setGenRoomSearch] = useState('');
  const [genRoomBlock, setGenRoomBlock] = useState('all');

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
  const [newEvent, setNewEvent] = useState({ title: '', color: '#3b82f6', roomId: '' });

  /* ── Sandbox Version state ──────────────────────────────────────── */
  const [versions, setVersions] = useState([]);
  const [selectedVersionId, setSelectedVersionId] = useState('');
  const [draftName, setDraftName] = useState('New Draft');
  const [confirmDeleteVersion, setConfirmDeleteVersion] = useState(null);
  const [deletingVersion, setDeletingVersion] = useState(false);
  const [showManageVersionsModal, setShowManageVersionsModal] = useState(false);
  const [selectedDraftIds, setSelectedDraftIds] = useState([]);
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(null);
  const [renamingVersion, setRenamingVersion] = useState(null);
  const [newVersionName, setNewVersionName] = useState('');
  const [savingRename, setSavingRename] = useState(false);

  /* ── Report Absence state ───────────────────────────────────────── */
  const [showAbsenceModal, setShowAbsenceModal] = useState(false);
  const [absenceClass, setAbsenceClass] = useState(null);
  const [absenceDate, setAbsenceDate] = useState('');
  const [absenceCategory, setAbsenceCategory] = useState('Sick Leave');
  const [absenceCustomNotes, setAbsenceCustomNotes] = useState('');
  const [absenceTargetSubstituteId, setAbsenceTargetSubstituteId] = useState('');
  const [submittingAbsence, setSubmittingAbsence] = useState(false);

  /* ── Substitute Requests state ──────────────────────────────────── */
  const [pendingSubstitutes, setPendingSubstitutes] = useState([]);
  const [myReportedAbsences, setMyReportedAbsences] = useState([]);
  const [facultyList, setFacultyList] = useState([]);
  const [acceptingSubstituteId, setAcceptingSubstituteId] = useState(null);
  const [cancellingAbsenceId, setCancellingAbsenceId] = useState(null);


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
    scope_type: 'department', // 'all', 'block', 'department'
    block_name: 'Block A',
    semester: '',
    term: 'odd', // 'odd' (Autumn), 'even' (Spring), '' (All)
    merge_common_courses: true,
    consecutive_labs: true,
    allow_spillover: true,
    breaks: normalizeBreaks(institutionSettings?.default_breaks),
  });

  const getUpfrontEtaEstimate = () => {
    let scopeType = config.scope_type || 'department';
    const deptId = selectedDepartmentId;
    const semester = config.semester;

    if (scopeType === 'department' && !deptId) {
      scopeType = 'all';
    }

    let baseSeconds = 3.0;
    let label = 'Low Load';
    let color = '#10b981';
    let desc = 'Fast single-department solve. Ideal for targeted schedules and rapid sandboxing.';

    if (scopeType === 'department') {
      if (semester) {
        baseSeconds = 2.5;
        label = 'Low Load (Single Cohort)';
        color = '#10b981';
        desc = 'Single semester cohort. Solves conflict-free in ~2–4 seconds.';
      } else {
        baseSeconds = 6.0;
        label = 'Moderate Load (Department)';
        color = '#3b82f6';
        desc = 'All semesters for department. Finishes in ~4–8 seconds.';
      }
    } else if (scopeType === 'block') {
      const bDepts = departments.filter(d => (d.building || '').toLowerCase().includes((config.block_name || '').toLowerCase()));
      const dCount = Math.max(5, bDepts.length || 25);
      baseSeconds = Math.round(dCount * 1.5);
      label = `High Load (${dCount} Block Waves)`;
      color = '#f59e0b';
      desc = `Sequentially co-schedules all ${dCount} departments in ${config.block_name} with localized room affinity (~${Math.max(1, Math.round(baseSeconds / 60))} min).`;
    } else {
      const termFactor = (config.term === 'odd' || config.term === 'even') ? 0.55 : 1.0;
      const totalDepts = departments.length || 178;
      const estWaves = Math.round(totalDepts * 0.92 * termFactor);
      baseSeconds = Math.round(estWaves * 1.4);
      label = `Enterprise Campus Master (~${estWaves} Waves)`;
      color = '#8b5cf6';
      desc = `Fast campus wave solver sequentially scheduling 178 departments (${estWaves} waves) across all campus rooms (~${Math.max(1, Math.round(baseSeconds / 60))} min).`;
    }

    let multiplier = 1.0;
    if (config.balance_faculty_workload) multiplier += 0.10;
    if (config.consecutive_labs) multiplier += 0.05;
    if (config.avoid_back_to_back) multiplier += 0.05;

    const totalSeconds = Math.round(baseSeconds * multiplier);
    let formatted = '';
    if (totalSeconds < 60) {
      formatted = `~${totalSeconds}s`;
    } else if (totalSeconds < 3600) {
      const m = Math.floor(totalSeconds / 60);
      const s = totalSeconds % 60;
      formatted = s > 0 ? `~${m}m ${s}s` : `~${m}m`;
    } else {
      const h = Math.floor(totalSeconds / 3600);
      const m = Math.floor((totalSeconds % 3600) / 60);
      formatted = `~${h}h ${m}m`;
    }

    return { totalSeconds, formatted, label, color, desc, isUpgradedToAll: config.scope_type === 'department' && !deptId };
  };

  const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const dayLabels = {
    MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday',
    THU: 'Thursday', FRI: 'Friday', SAT: 'Saturday',
  };

  /* ── Effective hours & breaks (department override -> global settings) ── */
  const activeDept = viewMode === 'department' && viewDeptId
    ? departments.find(d => String(d.id) === String(viewDeptId))
    : departments.find(d => String(d.id) === String(selectedDepartmentId));
  const effectiveStart = (activeDept?.start_time || institutionSettings?.start_time || '09:00').substring(0, 5);
  const effectiveEnd = (activeDept?.end_time || institutionSettings?.end_time || '18:00').substring(0, 5);

  const selectedVersion = versions.find(v => String(v.id) === String(selectedVersionId));
  const versionBuildings = [...new Set(timetable.map(e => e.building).filter(Boolean))];
  const versionBlocks = [...new Set(
    versionBuildings
      .map(b => {
        for (const bKey of Object.keys(ACADEMIC_BLOCKS)) {
          if (b.toLowerCase().includes(bKey.toLowerCase())) return bKey;
        }
        return null;
      })
      .filter(Boolean)
  )];
  const detectedScope = versionBlocks.length >= 3
    ? 'Whole Campus (All Blocks)'
    : versionBlocks.length === 1
      ? versionBlocks[0]
      : selectedVersion?.name?.toLowerCase().includes('campus')
        ? 'Whole Campus'
        : (activeDept?.name || '');

  const blockClassCount = viewMode === 'block' && viewBlock
    ? timetable.filter(e =>
        (e.building && e.building.toLowerCase().includes(viewBlock.toLowerCase())) ||
        (e.block_name && e.block_name.toLowerCase().includes(viewBlock.toLowerCase()))
      ).length
    : 0;

  /* Rows are derived strictly from the real, schedulable time slots (09:00 - 18:00).
     Breaks never add rows and nothing is treated as a break unless it lies inside a configured break range. */
  const generateTimeRange = (start, end) => {
    const times = [];
    for (let m = toMinutes(start); m < toMinutes(end); m += 60) times.push(fromMinutes(m));
    return times;
  };

  const timeSlotTimes = timeslots.length > 0
    ? [...new Set(timeslots.map(ts => ts.start_time?.substring(0, 5)))].filter(Boolean).sort()
    : generateTimeRange(effectiveStart, effectiveEnd);

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

  const saveBreaksAsDepartmentDefault = async () => {
    if (!activeDept) return toast.error('No active department selected.');
    try {
      const payload = { default_breaks: normalizeBreaks(config.breaks) };
      const res = await api.patch(`/api/scheduler/departments/${activeDept.id}/`, payload);
      setDepartments(prev => prev.map(d => d.id === activeDept.id ? { ...d, ...res.data } : d));
      toast.success(`Saved breaks as default for ${activeDept.name}`);
    } catch (err) {
      toast.error(err.response?.data?.default_breaks?.[0] || 'Failed to save department breaks');
    }
  };

  const saveBreaksAsInstitutionDefault = async () => {
    try {
      const payload = { default_breaks: normalizeBreaks(config.breaks) };
      const res = await api.put('/api/scheduler/settings/', payload);
      setInstitutionSettings(prev => ({ ...prev, ...res.data }));
      toast.success('Saved breaks as global institution default');
    } catch (err) {
      toast.error(err.response?.data?.default_breaks?.[0] || 'Failed to save institution breaks');
    }
  };
  /* ── Load data ──────────────────────────────────────────────────── */
  useEffect(() => {
    const urlVersion = searchParams.get('version');
    const urlScope = searchParams.get('scope');
    const urlBlock = searchParams.get('block');
    const urlDept = searchParams.get('dept');

    if (urlScope === 'block' && urlBlock) {
      setViewMode('block');
      setViewBlock(urlBlock);
    } else if (urlScope === 'department' && urlDept) {
      setViewMode('department');
      setViewDeptId(String(urlDept));
    } else if (urlScope === 'all') {
      setViewMode('all');
    }

    loadAll(urlVersion || null);
  }, []);

  useEffect(() => {
    if (!initialLoadedRef.current) return;
    if (!selectedVersionId) return;
    api.get(`/api/scheduler/timetable/?version=${selectedVersionId}&all=true`)
      .then(res => setTimetable(res.data.results || res.data || []))
      .catch(err => console.error('Failed to load version timetable:', err));
  }, [selectedVersionId]);

  const loadAll = async (overrideVersionId = null) => {
    setLoading(true);
    try {
      const [deptRes, subRes, roomRes, tsRes, settingsRes, versionsRes, resRes] = await Promise.all([
        api.get('/api/scheduler/departments/?all=true').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/subjects/?all=true').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/rooms/?all=true').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/timeslots/?all=true').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/settings/').catch(() => ({ data: { start_time: '09:00', end_time: '18:00', default_breaks: [] }})),
        api.get('/api/scheduler/versions/?all=true').catch(() => ({ data: { results: [] } })),
        api.get('/api/scheduler/resources/').catch(() => ({ data: { results: [] } }))
      ]);
      const depts = deptRes.data.results || deptRes.data || [];
      const subs = subRes.data.results || subRes.data || [];
      const rms = roomRes.data.results || roomRes.data || [];
      const tss = tsRes.data.results || tsRes.data || [];
      const settings = settingsRes.data || { start_time: '09:00', end_time: '18:00', default_breaks: [] };
      const vers = versionsRes.data.results || versionsRes.data || [];
      const ress = resRes.data.results || resRes.data || [];

      setDepartments(depts);
      setSubjects(subs);
      setRooms(rms);
      setTimeslots(tss);
      setInstitutionSettings(settings);
      setVersions(vers);
      setResources(ress);

      if (depts.length > 0 && !viewDeptId) {
        setViewDeptId(String(depts[0].id));
      }
      if (rms.length > 0 && !viewRoomNumber) {
        setViewRoomNumber(rms[0].room_number);
      }

      let targetVersionId = overrideVersionId ? String(overrideVersionId) : (selectedVersionId ? String(selectedVersionId) : '');
      if (!targetVersionId && vers.length > 0) {
        const published = vers.find(v => v.is_published);
        targetVersionId = String(published ? published.id : vers[0].id);
      }
      if (targetVersionId) {
        setSelectedVersionId(targetVersionId);
      }

      const ttUrl = targetVersionId ? `/api/scheduler/timetable/?version=${targetVersionId}&all=true` : '/api/scheduler/timetable/?all=true';
      const ttRes = await api.get(ttUrl);
      setTimetable(ttRes.data.results || ttRes.data || []);

      if (isFaculty || isAdmin) {
        api.get('/api/scheduler/absences/').then(res => {
          const allAbs = res.data.results || res.data || [];
          const myFid = user?.faculty_profile?.id;

          if (isAdmin) {
            setPendingSubstitutes(allAbs.filter(a => a.status === 'pending'));
            setMyReportedAbsences(allAbs);
          } else {
            // My reported absences
            const myAbs = allAbs.filter(a =>
              (myFid && a.faculty === myFid) ||
              (a.faculty_name && userFullName && a.faculty_name.trim().toLowerCase() === userFullName.trim().toLowerCase())
            );
            setMyReportedAbsences(myAbs);

            // Open substitute requests needing coverage from other colleagues
            const openSubs = allAbs.filter(a => {
              const isMine = (myFid && a.faculty === myFid) ||
                (a.faculty_name && userFullName && a.faculty_name.trim().toLowerCase() === userFullName.trim().toLowerCase());
              if (isMine) return false;
              if (a.status !== 'pending') return false;
              // If directed to a specific substitute, only show to target
              if (a.substitute && myFid && a.substitute !== myFid) return false;
              return true;
            });
            setPendingSubstitutes(openSubs);
          }
        }).catch(console.error);

        api.get('/api/auth/faculty/?page_size=200').then(res => {
          setFacultyList(res.data.results || res.data || []);
        }).catch(console.error);

        api.get('/api/scheduler/swaps/').then(res => {
          setPendingSwaps((res.data.results || res.data || []).filter(s => s.status === 'pending'));
        }).catch(console.error);
      }

      // Initialize config with all selected
      setConfig(prev => ({
        ...prev,
        subject_ids: subs.map(s => s.id),
        room_ids: rms.map(r => r.id),
        timeslot_ids: tss.map(ts => ts.id),
        breaks: breaksDirtyRef.current ? prev.breaks : normalizeBreaks(settings.default_breaks),
      }));

      initialLoadedRef.current = true;
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };
  loadAllRef.current = loadAll;

  /* ── Generator Dynamic Courses & Rooms Fetching ─────────────────── */
  const fetchGenCourses = async ({
    pageNum = 1,
    searchQuery = genCourseSearch,
    deptId = selectedDepartmentId,
    blockName = config.block_name,
    term = config.term,
    append = false,
  } = {}) => {
    if (pageNum === 1) setGenCourseLoading(true);
    else setGenCourseLoadingMore(true);

    try {
      let url = `/api/scheduler/subjects/?page=${pageNum}&page_size=100`;
      if (searchQuery && searchQuery.trim()) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }
      if (config.scope_type === 'department' && deptId) {
        url += `&department=${deptId}`;
      } else if (config.scope_type === 'block' && blockName) {
        url += `&block=${encodeURIComponent(blockName)}`;
      }
      if (config.semester) {
        url += `&semester=${config.semester}`;
      }
      if (term) {
        url += `&term=${term}`;
      }

      const res = await api.get(url);
      const data = res.data;
      const results = data.results || (Array.isArray(data) ? data : []);
      const count = data.count !== undefined ? data.count : (Array.isArray(data) ? data.length : results.length);

      setGenCourseTotal(count);
      setGenCoursePage(pageNum);

      if (append) {
        setGenCourses(prev => {
          const existingIds = new Set(prev.map(c => c.id));
          const newUnique = results.filter(c => !existingIds.has(c.id));
          return [...prev, ...newUnique];
        });
      } else {
        setGenCourses(results);
      }
    } catch (err) {
      console.error('Failed to fetch generator courses:', err);
    } finally {
      setGenCourseLoading(false);
      setGenCourseLoadingMore(false);
    }
  };

  const handleSelectDepartmentForScope = async (deptId) => {
    setSelectedDepartmentId(deptId);
    const dept = departments.find(d => String(d.id) === String(deptId));
    const deptBreaks = normalizeBreaks(dept?.default_breaks);
    breaksDirtyRef.current = true;
    setConfig(prev => ({
      ...prev,
      breaks: deptBreaks.length > 0 ? deptBreaks : normalizeBreaks(institutionSettings?.default_breaks),
    }));

    if (deptId) {
      const did = parseInt(deptId, 10);
      try {
        setGenCourseLoading(true);
        const termParam = config.term ? `&term=${config.term}` : '';
        const res = await api.get(`/api/scheduler/subjects/?department=${did}&all=true${termParam}`);
        const deptSubjects = res.data.results || res.data || [];
        const deptSubIds = deptSubjects.map(s => s.id);
        const filteredRoomIds = rooms
          .filter(r => r.departments?.includes(did) || !r.departments || r.departments.length === 0)
          .map(r => r.id);
        setConfig(prev => ({
          ...prev,
          subject_ids: deptSubIds,
          room_ids: filteredRoomIds.length > 0 ? filteredRoomIds : rooms.map(r => r.id),
        }));
        setGenCourses(deptSubjects);
        setGenCourseTotal(deptSubjects.length);
        setGenCoursePage(1);
      } catch (err) {
        console.error('Failed to fetch department subjects:', err);
      } finally {
        setGenCourseLoading(false);
      }
    } else {
      setConfig(prev => ({ ...prev, subject_ids: subjects.map(s => s.id), room_ids: rooms.map(r => r.id) }));
      fetchGenCourses({ pageNum: 1, deptId: '', searchQuery: '' });
    }
  };

  const handleSelectAllLoadedCourses = () => {
    const loadedIds = genCourses.map(c => c.id);
    const allSelected = loadedIds.length > 0 && loadedIds.every(id => config.subject_ids.includes(id));
    if (allSelected) {
      const loadedSet = new Set(loadedIds);
      setConfig(prev => ({
        ...prev,
        subject_ids: prev.subject_ids.filter(id => !loadedSet.has(id)),
      }));
    } else {
      setConfig(prev => ({
        ...prev,
        subject_ids: [...new Set([...prev.subject_ids, ...loadedIds])],
      }));
    }
  };

  const handleSelectAllMatchingCatalog = async () => {
    const toastId = toast.loading('Selecting all matching courses across campus...');
    try {
      let url = `/api/scheduler/subjects/?all=true`;
      if (genCourseSearch && genCourseSearch.trim()) url += `&search=${encodeURIComponent(genCourseSearch.trim())}`;
      if (config.scope_type === 'department' && selectedDepartmentId) url += `&department=${selectedDepartmentId}`;
      else if (config.scope_type === 'block' && config.block_name) url += `&block=${encodeURIComponent(config.block_name)}`;
      if (config.semester) url += `&semester=${config.semester}`;
      if (config.term) url += `&term=${config.term}`;

      const res = await api.get(url);
      const allMatching = res.data.results || res.data || [];
      const allIds = allMatching.map(c => c.id);
      setConfig(prev => ({
        ...prev,
        subject_ids: [...new Set([...prev.subject_ids, ...allIds])],
      }));
      toast.success(`Selected all ${allIds.length} matching courses!`, { id: toastId });
    } catch (err) {
      toast.error('Failed to select all courses', { id: toastId });
    }
  };

  const filteredGenRooms = (rooms || []).filter(r => {
    if (genRoomBlock !== 'all') {
      if (!r.building || !r.building.toLowerCase().includes(genRoomBlock.toLowerCase())) {
        return false;
      }
    }
    if (genRoomSearch && genRoomSearch.trim()) {
      const q = genRoomSearch.toLowerCase().trim();
      const matchNum = r.room_number?.toLowerCase().includes(q);
      const matchBuild = r.building?.toLowerCase().includes(q);
      const matchType = r.room_type?.toLowerCase().includes(q);
      if (!matchNum && !matchBuild && !matchType) return false;
    }
    return true;
  });

  const toggleAllFilteredRooms = () => {
    const fIds = filteredGenRooms.map(r => r.id);
    const allSelected = fIds.length > 0 && fIds.every(id => config.room_ids.includes(id));
    if (allSelected) {
      const fSet = new Set(fIds);
      setConfig(prev => ({ ...prev, room_ids: prev.room_ids.filter(id => !fSet.has(id)) }));
    } else {
      setConfig(prev => ({ ...prev, room_ids: [...new Set([...prev.room_ids, ...fIds])] }));
    }
  };

  useEffect(() => {
    if (showConfig) {
      if (config.scope_type === 'department' && selectedDepartmentId) {
        handleSelectDepartmentForScope(selectedDepartmentId);
      } else if (config.scope_type === 'block' && config.block_name) {
        fetchGenCourses({ pageNum: 1, blockName: config.block_name });
      } else {
        fetchGenCourses({ pageNum: 1 });
      }
    }
  }, [showConfig]);

  /* ── Generate with config ───────────────────────────────────────── */
  const handleGenerate = async () => {
    if (!draftName.trim()) return toast.error("Please provide a Draft Name");
    setIsProgressMinimized(false);
    const upfrontEta = getUpfrontEtaEstimate();

    try {
      const payload = {
        ...config,
        draft_name: draftName,
        scope_type: config.scope_type || 'department',
        block_name: config.scope_type === 'block' ? config.block_name : undefined,
        department_id: config.scope_type === 'department' && selectedDepartmentId ? parseInt(selectedDepartmentId, 10) : undefined,
        semester: config.semester ? parseInt(config.semester, 10) : undefined,
        term: config.term || undefined,
        merge_common_courses: !!config.merge_common_courses,
        consecutive_labs: !!config.consecutive_labs,
        allow_spillover: !!config.allow_spillover,
      };

      // Auto-upgrade if 'department' is selected without a specific department ID
      if (payload.scope_type === 'department' && !payload.department_id) {
        payload.scope_type = 'all';
      }

      // For 'all' or 'block' scopes, do not constrain to a paginated subset of subject_ids or room_ids.
      // This ensures the solver schedules ALL departments across the campus or block.
      if (payload.scope_type === 'all' || payload.scope_type === 'block') {
        delete payload.subject_ids;
        delete payload.room_ids;
      }
      // Breaks are sent as ranges; time slots inside any break are never offered to the solver.
      payload.custom_breaks = normalizeBreaks(config.breaks);
      delete payload.breaks;
      payload.timeslot_ids = getEffectiveTimeslotIds();
      if (payload.timeslot_ids.length === 0) {
        return toast.error('No time slots left to schedule: every selected slot falls inside a break.');
      }
      if (Object.keys(payload.excluded_slots).length === 0) delete payload.excluded_slots;
      if (Object.keys(payload.preferred_room_types).length === 0) delete payload.preferred_room_types;
      if (payload.locked_entries.length === 0) delete payload.locked_entries;

      const response = await api.post('/api/scheduler/generate/', payload);
      
      if (response.data.task_id) {
        const scopeLabel = payload.scope_type === 'all'
          ? 'Whole Campus Master'
          : payload.scope_type === 'block'
            ? `Block ${payload.block_name}`
            : 'Department Schedule';

        taskProgress.startTracking(response.data.task_id, {
          initialEta: upfrontEta.totalSeconds,
          scopeLabel,
          scopeType: payload.scope_type,
          blockName: payload.block_name,
          departmentId: payload.department_id,
        });
        toast.success('Timetable generation queued in background');
      } else {
        setTimetable(response.data.timetable || []);
        setShowConfig(false);
        if (response.data.version_id) setSelectedVersionId(response.data.version_id);
        toast(response.data.message);
        loadAll(); // Reload versions
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to generate timetable.');
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
    const timeslotId = parseInt(parts[parts.length - 1], 10);
    if (isNaN(timeslotId)) return toast.error("Cannot move to an invalid slot");
    
    try {
      const response = await api.patch(`/api/scheduler/timetable/${entryId}/`, {
        time_slot: timeslotId
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

  const getClassesForSlot = (day, time) => {
    return timetable.filter(entry => {
      if (entry.day !== day || entry.start_time?.substring(0, 5) !== time) return false;

      // Live search filter across any view
      if (viewSearchTerm && viewSearchTerm.trim()) {
        const q = viewSearchTerm.toLowerCase().trim();
        const matchSub = entry.subject_code?.toLowerCase().includes(q) || entry.subject_name?.toLowerCase().includes(q);
        const matchFac = entry.faculty_name?.toLowerCase().includes(q);
        const matchRoom = entry.room_number?.toLowerCase().includes(q);
        const matchDept = entry.department_names?.some(d => d.toLowerCase().includes(q));
        if (!matchSub && !matchFac && !matchRoom && !matchDept) return false;
      }

      // For students and faculty, backend has already scoped the timetable to their enrolled or teaching classes
      if (!isAdmin) {
        return true;
      }

      // Multi-View Switcher Filter Modes
      if (viewMode === 'department') {
        if (viewDeptId) {
          const did = parseInt(viewDeptId, 10);
          if (entry.department_ids && entry.department_ids.length > 0) {
            if (!entry.department_ids.includes(did)) return false;
          } else {
            const targetDept = departments.find(d => d.id === did);
            if (targetDept && !entry.department_names?.includes(targetDept.name)) return false;
          }
        }
        if (viewSemester) {
          if (String(entry.semester) !== String(viewSemester)) return false;
        }
        return true;
      }

      if (viewMode === 'block') {
        if (viewBlock) {
          const inBuilding = entry.building && entry.building.toLowerCase().includes(viewBlock.toLowerCase());
          const inBlock = entry.block_name && entry.block_name.toLowerCase().includes(viewBlock.toLowerCase());
          if (!inBuilding && !inBlock) return false;
        }
        return true;
      }

      if (viewMode === 'room') {
        if (viewRoomNumber) {
          if (entry.room_number !== viewRoomNumber) return false;
        }
        return true;
      }

      if (viewMode === 'faculty') {
        if (viewFacultyName) {
          if (entry.faculty_name !== viewFacultyName) return false;
        }
        return true;
      }

      if (viewMode === 'all') {
        return true;
      }

      // Legacy fallback
      if (filterType === 'my_classes' && userFullName && entry.faculty_name !== userFullName) return false;
      if (filterType === 'faculty' && filterValue && entry.faculty_name !== filterValue) return false;
      if (filterType === 'room' && filterValue && entry.room_number !== filterValue) return false;
      if (filterType === 'department' && filterValue) {
        const depId = parseInt(filterValue, 10);
        if (entry.department_ids && entry.department_ids.length > 0) {
          if (!entry.department_ids.includes(depId)) return false;
        } else {
          const targetDept = departments.find(d => d.id === depId);
          if (targetDept && !entry.department_names?.includes(targetDept.name)) return false;
        }
      }
      if (filterType === 'block' && filterValue) {
        const inBuilding = entry.building && entry.building.toLowerCase().includes(filterValue.toLowerCase());
        const inBlock = entry.block_name && entry.block_name.toLowerCase().includes(filterValue.toLowerCase());
        if (!inBuilding && !inBlock) return false;
      }
      if (filterType === 'resource' && filterValue) {
        const room = rooms.find(r => r.room_number === entry.room_number);
        const subject = subjects.find(s => s.code === entry.subject_code);
        const resId = parseInt(filterValue, 10);
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

  const handleDeleteVersion = async () => {
    if (!confirmDeleteVersion) return;
    setDeletingVersion(true);
    try {
      await api.delete(`/api/scheduler/versions/${confirmDeleteVersion.id}/`);
      toast.success(`Draft timetable "${confirmDeleteVersion.name}" deleted successfully!`);
      const deletedId = confirmDeleteVersion.id;
      setConfirmDeleteVersion(null);

      // Re-fetch versions
      const versionsRes = await api.get('/api/scheduler/versions/?all=true');
      const updatedVersions = versionsRes.data.results || versionsRes.data || [];
      setVersions(updatedVersions);

      // If the currently selected version was the one deleted, switch to published or fallback
      if (String(selectedVersionId) === String(deletedId)) {
        const published = updatedVersions.find(v => v.is_published);
        setSelectedVersionId(published ? published.id : (updatedVersions[0]?.id || ''));
      } else {
        loadAll();
      }
    } catch (err) {
      console.error('Failed to delete timetable version:', err);
      toast.error(err.response?.data?.detail || err.response?.data?.[0] || 'Failed to delete draft timetable');
    } finally {
      setDeletingVersion(false);
    }
  };

  const openRenameModal = (version) => {
    if (!version) return;
    setRenamingVersion(version);
    setNewVersionName(version.name || '');
  };

  const handleRenameVersion = async (e) => {
    if (e) e.preventDefault();
    if (!renamingVersion || !newVersionName.trim()) return;
    setSavingRename(true);
    try {
      const res = await api.patch(`/api/scheduler/versions/${renamingVersion.id}/`, {
        name: newVersionName.trim(),
      });
      const updated = res.data;
      toast.success(`Timetable renamed to "${updated.name}"`);
      setVersions(prev => prev.map(v => (v.id === updated.id ? { ...v, name: updated.name } : v)));
      setRenamingVersion(null);
      setNewVersionName('');
    } catch (err) {
      console.error('Failed to rename timetable version:', err);
      toast.error(err.response?.data?.name?.[0] || err.response?.data?.detail || 'Failed to rename timetable');
    } finally {
      setSavingRename(false);
    }
  };

  const toggleDraftSelect = (id) => {
    setSelectedDraftIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const toggleSelectAllDrafts = () => {
    const draftIds = versions.filter(v => !v.is_published).map(v => v.id);
    if (selectedDraftIds.length === draftIds.length) {
      setSelectedDraftIds([]);
    } else {
      setSelectedDraftIds(draftIds);
    }
  };

  const handleBulkDelete = async () => {
    if (!confirmBulkDelete) return;
    setDeletingVersion(true);
    try {
      const payload = confirmBulkDelete.allDrafts
        ? { delete_all_drafts: true }
        : { ids: confirmBulkDelete.ids };
      const res = await api.post('/api/scheduler/versions/bulk-delete/', payload);
      toast.success(res.data.message || 'Draft timetables deleted successfully!');

      const deletedIds = new Set(confirmBulkDelete.allDrafts ? versions.filter(v => !v.is_published).map(v => v.id) : confirmBulkDelete.ids);
      setSelectedDraftIds([]);
      setConfirmBulkDelete(null);

      // Re-fetch versions
      const versionsRes = await api.get('/api/scheduler/versions/?all=true');
      const updatedVersions = versionsRes.data.results || versionsRes.data || [];
      setVersions(updatedVersions);

      // If active version was deleted, fallback to published
      if (confirmBulkDelete.allDrafts || deletedIds.has(Number(selectedVersionId))) {
        const published = updatedVersions.find(v => v.is_published);
        setSelectedVersionId(published ? published.id : (updatedVersions[0]?.id || ''));
      } else {
        loadAll();
      }
    } catch (err) {
      console.error('Failed to bulk delete drafts:', err);
      toast.error(err.response?.data?.error || 'Failed to bulk delete draft timetables');
    } finally {
      setDeletingVersion(false);
    }
  };

  const handleReportAbsence = async () => {
    if (!absenceClass) return;
    if (!absenceDate) {
      toast.error("Please select an absence date");
      return;
    }
    setSubmittingAbsence(true);
    try {
      const fullReason = absenceCustomNotes.trim()
        ? `[${absenceCategory}] ${absenceCustomNotes.trim()}`
        : `[${absenceCategory}] Requesting substitute coverage`;

      const payload = {
        date: absenceDate,
        reason: fullReason,
        timetable_entry: absenceClass.id,
      };

      if (absenceTargetSubstituteId) {
        payload.substitute = Number(absenceTargetSubstituteId);
      }

      await api.post('/api/scheduler/absences/', payload);
      toast.success("Absence reported & substitute request broadcasted!");
      setShowAbsenceModal(false);
      setAbsenceClass(null);
      setAbsenceCustomNotes('');
      setAbsenceTargetSubstituteId('');
      loadAll();
    } catch (err) {
      console.error('Failed to report absence:', err);
      const msg = err.response?.data?.error || err.response?.data?.detail || "Failed to report absence";
      toast.error(msg);
    } finally {
      setSubmittingAbsence(false);
    }
  };

  const handleAcceptSubstitute = async (absenceId) => {
    setAcceptingSubstituteId(absenceId);
    try {
      const payload = {
        status: 'approved',
      };
      if (user?.faculty_profile?.id) {
        payload.substitute = user.faculty_profile.id;
      }
      await api.patch(`/api/scheduler/absences/${absenceId}/`, payload);
      toast.success("Substitute request accepted! The class is now on your teaching schedule.");
      loadAll();
    } catch (err) {
      console.error('Failed to accept substitute request:', err);
      const msg = err.response?.data?.error || err.response?.data?.detail || "Failed to accept substitute request";
      toast.error(msg);
    } finally {
      setAcceptingSubstituteId(null);
    }
  };

  const handleCancelAbsence = async (absenceId) => {
    if (!window.confirm("Are you sure you want to cancel this absence request?")) return;
    setCancellingAbsenceId(absenceId);
    try {
      await api.delete(`/api/scheduler/absences/${absenceId}/`);
      toast.success("Absence request cancelled.");
      loadAll();
    } catch (err) {
      console.error('Failed to cancel absence:', err);
      const msg = err.response?.data?.error || err.response?.data?.detail || "Failed to cancel absence request";
      toast.error(msg);
    } finally {
      setCancellingAbsenceId(null);
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

  const activeVersion = versions.find(v => String(v.id) === String(selectedVersionId)) || versions.find(v => v.is_published);

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <h1 style={{ margin: 0 }}>
              {isStudent ? 'My Class Timetable' : isFaculty ? 'My Teaching Schedule' : 'Class Timetable'}
            </h1>
            {activeVersion && (
              <span className={`badge ${activeVersion.is_published ? 'badge-present' : 'badge-low'}`} style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                {activeVersion.is_published ? '🟢 Live' : '🟡 Draft'}: {activeVersion.name}
              </span>
            )}
            {isAdmin && detectedScope && (
              <span className="badge" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem', background: 'rgba(59, 130, 246, 0.15)', border: '1px solid rgba(59, 130, 246, 0.35)', color: 'var(--color-accent-blue-light)' }} title="Timetable generation scope">
                📍 Scope: {detectedScope}
              </span>
            )}
          </div>
          <p style={{ marginTop: '0.25rem', marginBottom: 0 }}>
            {isStudent
              ? 'Personalized weekly schedule of your enrolled department courses and electives'
              : isFaculty
                ? 'Your assigned lectures, laboratories, and approved substitute teaching duties'
                : 'Weekly academic schedule generated by the constraint satisfaction algorithm'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={exportToPDF}>
            📥 Export PDF
          </button>
          
          {isAdmin && (
            <>
              {versions.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <select 
                    className="form-select" 
                    style={{ width: 'auto', background: 'rgba(59, 130, 246, 0.1)', borderColor: 'var(--color-accent-blue)', color: 'var(--color-accent-blue-light)', fontWeight: 'bold' }}
                    value={selectedVersionId}
                    onChange={(e) => setSelectedVersionId(e.target.value)}
                  >
                    <option value="">-- Timetable Versions --</option>
                    {versions.map(v => (
                       <option key={v.id} value={v.id}>{v.name} {v.is_published ? '(Live)' : '(Draft)'}</option>
                    ))}
                  </select>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setShowManageVersionsModal(true)}
                    title="Manage and view all sandbox draft timetables"
                    style={{ padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                  >
                    📋 Drafts ({versions.filter(v => !v.is_published).length})
                  </button>
                  {selectedVersionId && (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => openRenameModal(versions.find(v => String(v.id) === String(selectedVersionId)))}
                      title="Rename currently selected timetable"
                      id="btn-rename-selected-version"
                      style={{ padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                    >
                      ✏️ Rename
                    </button>
                  )}
                </div>
              )}
              
              {selectedVersionId && !versions.find(v => v.id == selectedVersionId)?.is_published && (
                <>
                  <button className="btn btn-primary" style={{ background: 'var(--color-accent-emerald)', borderColor: 'var(--color-accent-emerald)' }} onClick={handlePublishVersion}>
                      🚀 Publish Draft
                  </button>
                  <button
                    className="btn btn-danger"
                    style={{ background: 'var(--color-accent-rose, #ef4444)', borderColor: 'var(--color-accent-rose, #ef4444)' }}
                    onClick={() => setConfirmDeleteVersion(versions.find(v => String(v.id) === String(selectedVersionId)))}
                    title="Delete this draft timetable"
                    id="btn-delete-selected-draft"
                  >
                      🗑️ Delete Draft
                  </button>
                </>
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
            <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <label style={{ fontWeight: 600 }}>Draft Name:</label>
                  <input
                    type="text"
                    className="form-input"
                    style={{ width: '220px' }}
                    placeholder="e.g. Fall 2026 Sandbox"
                    value={draftName}
                    onChange={(e) => setDraftName(e.target.value)}
                  />
                </div>
                
                {/* Multi-Department Scope Selector */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <label style={{ fontWeight: 600 }}>Scheduling Scope:</label>
                  <select
                    className="form-select"
                    style={{ width: 'auto', fontWeight: 600, borderColor: 'var(--color-accent-blue)' }}
                    value={config.scope_type}
                    onChange={(e) => {
                      const scope = e.target.value;
                      setConfig(prev => {
                        let newBreaks = prev.breaks;
                        if (scope === 'all' || scope === 'block') {
                          newBreaks = normalizeBreaks(institutionSettings?.default_breaks);
                        } else if (scope === 'department') {
                          const dept = departments.find(d => String(d.id) === String(selectedDepartmentId));
                          const deptBreaks = normalizeBreaks(dept?.default_breaks);
                          newBreaks = deptBreaks.length > 0 ? deptBreaks : normalizeBreaks(institutionSettings?.default_breaks);
                        }
                        return { ...prev, scope_type: scope, breaks: newBreaks };
                      });
                    }}
                  >
                    <option value="department">🏛️ Single Department</option>
                    <option value="block">🏢 Academic School Block (Wave)</option>
                    <option value="all">🌐 Whole Campus (All 9 Blocks & 178 Depts)</option>
                  </select>
                </div>

                {/* Instant Upfront ETA Badge */}
                {(() => {
                  const eta = getUpfrontEtaEstimate();
                  return (
                    <div style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      padding: '0.35rem 0.8rem',
                      borderRadius: '20px',
                      background: `${eta.color}15`,
                      border: `1px solid ${eta.color}50`,
                      color: eta.color,
                      fontSize: '0.82rem',
                      fontWeight: 700,
                    }}>
                      <span>⏱️ Est. Duration: {eta.formatted}</span>
                      <span style={{ fontSize: '0.75rem', opacity: 0.9 }}>• {eta.label}</span>
                    </div>
                  );
                })()}
              </div>

              {/* Conditional scope targets */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
                {config.scope_type === 'department' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <label style={{ fontWeight: 600, fontSize: '0.9rem' }}>Target Department:</label>
                    <select 
                      className="form-select"
                      style={{ maxWidth: '300px' }}
                      value={selectedDepartmentId}
                      onChange={(e) => handleSelectDepartmentForScope(e.target.value)}
                    >
                      <option value="">All Departments (Global)</option>
                      {departments.map(d => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                {config.scope_type === 'block' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <label style={{ fontWeight: 600, fontSize: '0.9rem' }}>Target School Block:</label>
                    <select
                      className="form-select"
                      style={{ maxWidth: '340px' }}
                      value={config.block_name}
                      onChange={(e) => {
                        const bName = e.target.value;
                        setConfig(prev => ({ ...prev, block_name: bName }));
                        fetchGenCourses({ pageNum: 1, blockName: bName });
                      }}
                    >
                      {Object.entries(ACADEMIC_BLOCKS).map(([bKey, bName]) => (
                        <option key={bKey} value={bKey}>{bKey} - {bName}</option>
                      ))}
                    </select>
                  </div>
                )}

                {config.scope_type === 'all' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-accent-blue-light)' }}>
                    <span>🚀 <strong>Enterprise Wave Engine:</strong> Sequentially schedules 9 Academic Blocks with locked cross-block faculty & room reservations.</span>
                  </div>
                )}

                {/* Academic Term Selector (Odd vs Even) */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <label style={{ fontWeight: 600, fontSize: '0.9rem' }}>Academic Term:</label>
                  <select
                    className="form-select"
                    style={{ width: 'auto', fontWeight: 600, borderColor: 'var(--color-accent-blue)' }}
                    value={config.term}
                    onChange={(e) => {
                      const t = e.target.value;
                      setConfig(prev => ({ ...prev, term: t }));
                      fetchGenCourses({ pageNum: 1, term: t });
                    }}
                  >
                    <option value="odd">🍂 Autumn Term (Odd Semesters: 1, 3, 5, 7)</option>
                    <option value="even">🌸 Spring Term (Even Semesters: 2, 4, 6, 8)</option>
                    <option value="">🌐 Full Year (All Semesters)</option>
                  </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <label style={{ fontWeight: 600, fontSize: '0.9rem' }}>Semester:</label>
                  <select
                    className="form-select"
                    style={{ width: '130px' }}
                    value={config.semester}
                    onChange={(e) => {
                      const sem = e.target.value;
                      setConfig(prev => ({ ...prev, semester: sem }));
                      fetchGenCourses({ pageNum: 1 });
                    }}
                  >
                    <option value="">All Semesters</option>
                    {[1, 2, 3, 4, 5, 6, 7, 8].map(s => (
                      <option key={s} value={s}>Semester {s}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Config tabs */}
          <div className="config-tabs">
            {[
              {
                key: 'subjects',
                label: '📚 Subjects',
                count: config.scope_type === 'all'
                  ? 'All 178 Depts'
                  : config.scope_type === 'block'
                    ? config.block_name
                    : `${config.subject_ids.length}/${genCourseTotal || genCourses.length || subjects.length}`
              },
              {
                key: 'rooms',
                label: '🏛️ Rooms',
                count: config.scope_type === 'all'
                  ? `All (${rooms.length})`
                  : config.scope_type === 'block'
                    ? `Block (${rooms.filter(r => r.building?.toLowerCase().includes((config.block_name || '').toLowerCase()) || r.building?.toLowerCase().includes('central')).length})`
                    : `${config.room_ids.length}/${rooms.length}`
              },
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
                {config.scope_type === 'all' && (
                  <div style={{ padding: '0.85rem 1.15rem', background: 'rgba(59, 130, 246, 0.12)', border: '1px solid rgba(59, 130, 246, 0.35)', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.88rem', color: 'var(--color-accent-blue-light)' }}>
                    🌐 <strong>Whole Campus Scope Active:</strong> All courses across all 178 academic departments will be scheduled automatically into their designated blocks using the enterprise wave solver. Manual course checkboxes are optional overrides.
                  </div>
                )}
                {config.scope_type === 'block' && (
                  <div style={{ padding: '0.85rem 1.15rem', background: 'rgba(59, 130, 246, 0.12)', border: '1px solid rgba(59, 130, 246, 0.35)', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.88rem', color: 'var(--color-accent-blue-light)' }}>
                    🏢 <strong>Academic Block Scope Active:</strong> All courses belonging to <strong>{config.block_name}</strong> will be scheduled automatically into {config.block_name} facilities and central lecture halls.
                  </div>
                )}
                <div className="config-section-header" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div>
                    <h3 style={{ margin: 0 }}>Select Subjects to Schedule</h3>
                    <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                      {config.scope_type === 'all'
                        ? `Whole Campus Scope · Showing ${(genCourses.length > 0 ? genCourses : subjects).length} of ${genCourseTotal || (genCourses.length > 0 ? genCourses : subjects).length} in catalog`
                        : `${config.subject_ids.length} selected · Showing ${(genCourses.length > 0 ? genCourses : subjects).length} of ${genCourseTotal || (genCourses.length > 0 ? genCourses : subjects).length} in catalog`}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn btn-sm btn-secondary"
                      onClick={handleSelectAllLoadedCourses}
                    >
                      {(genCourses.length > 0 ? genCourses : subjects).length > 0 &&
                       (genCourses.length > 0 ? genCourses : subjects).every(c => config.subject_ids.includes(c.id))
                        ? 'Deselect Loaded'
                        : `Select All Loaded (${(genCourses.length > 0 ? genCourses : subjects).length})`}
                    </button>
                    {genCourseTotal > (genCourses.length > 0 ? genCourses : subjects).length && (
                      <button
                        type="button"
                        className="btn btn-sm btn-primary"
                        onClick={handleSelectAllMatchingCatalog}
                        title="Select all matching courses across the database"
                      >
                        ⚡ Select All in Catalog ({genCourseTotal})
                      </button>
                    )}
                  </div>
                </div>

                {/* Course Search & Filter Bar */}
                <div className="generator-search-bar">
                  <div style={{ position: 'relative', flex: '1 1 240px', maxWidth: '400px' }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Search courses by code or title (e.g. CS101, Data Structures)..."
                      value={genCourseSearch}
                      onChange={(e) => setGenCourseSearch(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          fetchGenCourses({ pageNum: 1, searchQuery: genCourseSearch });
                        }
                      }}
                      style={{ paddingRight: '2rem' }}
                    />
                    <button
                      type="button"
                      onClick={() => fetchGenCourses({ pageNum: 1, searchQuery: genCourseSearch })}
                      style={{ position: 'absolute', right: '0.5rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--color-accent-blue)', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                      🔍
                    </button>
                  </div>
                  {genCourseLoading && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span className="spinner" style={{ width: '14px', height: '14px' }} /> Loading courses...
                    </span>
                  )}
                </div>

                <div className="checkbox-grid">
                  {(genCourses.length > 0 ? genCourses : subjects).map(s => (
                    <label key={s.id} className={`checkbox-card ${config.subject_ids.includes(s.id) ? 'selected' : ''}`}>
                      <input
                        type="checkbox"
                        checked={config.subject_ids.includes(s.id)}
                        onChange={() => toggleId('subject_ids', s.id)}
                      />
                      <div className="checkbox-card-content">
                        <span className="checkbox-code">{s.code}</span>
                        <span className="checkbox-name">{s.name}</span>
                        <span className="checkbox-meta">
                          {s.faculty_name || 'No faculty'} · Sem {s.semester || 'N/A'} · {s.sessions_per_week} sess/wk
                        </span>
                      </div>
                    </label>
                  ))}
                </div>

                {/* Load More Button */}
                {genCourseTotal > (genCourses.length > 0 ? genCourses : subjects).length && (
                  <button
                    type="button"
                    className="generator-load-more"
                    onClick={() => fetchGenCourses({ pageNum: genCoursePage + 1, append: true })}
                    disabled={genCourseLoadingMore}
                  >
                    {genCourseLoadingMore ? (
                      <>
                        <span className="spinner" style={{ width: '16px', height: '16px' }} />
                        Loading next 100 courses...
                      </>
                    ) : (
                      <>
                        📥 Load More Courses (+100) — {genCourseTotal - (genCourses.length > 0 ? genCourses : subjects).length} remaining
                      </>
                    )}
                  </button>
                )}
              </div>
            )}

            {/* ── Rooms tab ─────────────────────────────────────────────── */}
            {configTab === 'rooms' && (
              <div className="config-section">
                <div className="config-section-header" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div>
                    <h3 style={{ margin: 0 }}>Select Rooms to Use</h3>
                    <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                      {config.room_ids.length} of {rooms.length} campus rooms selected
                    </span>
                  </div>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={toggleAllFilteredRooms}
                  >
                    {filteredGenRooms.length > 0 && filteredGenRooms.every(r => config.room_ids.includes(r.id))
                      ? 'Deselect Filtered'
                      : `Select All Filtered (${filteredGenRooms.length})`}
                  </button>
                </div>

                {/* Block Filter Pills & Search */}
                <div style={{ marginBottom: '0.75rem' }}>
                  <div className="block-filter-pills">
                    <button
                      type="button"
                      className={`block-filter-pill ${genRoomBlock === 'all' ? 'active' : ''}`}
                      onClick={() => setGenRoomBlock('all')}
                    >
                      All Blocks ({rooms.length})
                    </button>
                    {Object.keys(ACADEMIC_BLOCKS).map(bKey => (
                      <button
                        key={bKey}
                        type="button"
                        className={`block-filter-pill ${genRoomBlock === bKey ? 'active' : ''}`}
                        onClick={() => setGenRoomBlock(bKey)}
                      >
                        {bKey}
                      </button>
                    ))}
                    <button
                      type="button"
                      className={`block-filter-pill ${genRoomBlock === 'Central' ? 'active' : ''}`}
                      onClick={() => setGenRoomBlock('Central')}
                    >
                      Central Complex
                    </button>
                  </div>

                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search rooms by number, building, or type..."
                    value={genRoomSearch}
                    onChange={(e) => setGenRoomSearch(e.target.value)}
                    style={{ maxWidth: '350px' }}
                  />
                </div>

                <div className="checkbox-grid">
                  {filteredGenRooms.map(r => (
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
                        {activeDept && (
                          <button type="button" className="btn btn-sm btn-secondary" onClick={saveBreaksAsDepartmentDefault}>
                            💾 Save as Default for {activeDept.name}
                          </button>
                        )}
                        <button type="button" className="btn btn-sm btn-secondary" onClick={saveBreaksAsInstitutionDefault}>
                          🌐 Save as Institution Default
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
                        checked={config.merge_common_courses}
                        onChange={(e) => setConfig(prev => ({ ...prev, merge_common_courses: e.target.checked }))}
                      />
                      <span className="toggle-slider" />
                    </div>
                    <div className="option-info">
                      <span className="option-label">⚡ Merge Common University Courses</span>
                      <span className="option-desc">Automatically co-schedule shared multi-department courses in Seminar & Central Halls with 1 instructor</span>
                    </div>
                  </label>

                  <label className="advanced-option">
                    <div className="option-toggle">
                      <input
                        type="checkbox"
                        checked={config.consecutive_labs}
                        onChange={(e) => setConfig(prev => ({ ...prev, consecutive_labs: e.target.checked }))}
                      />
                      <span className="toggle-slider" />
                    </div>
                    <div className="option-info">
                      <span className="option-label">🧪 Enforce 2-Hour Consecutive Lab Blocks</span>
                      <span className="option-desc">Schedule practical lab classes as atomic 2-hour back-to-back blocks in dedicated laboratory rooms</span>
                    </div>
                  </label>

                  <label className="advanced-option">
                    <div className="option-toggle">
                      <input
                        type="checkbox"
                        checked={config.allow_spillover}
                        onChange={(e) => setConfig(prev => ({ ...prev, allow_spillover: e.target.checked }))}
                      />
                      <span className="toggle-slider" />
                    </div>
                    <div className="option-info">
                      <span className="option-label">🏢 Dynamic Academic Block Spillover</span>
                      <span className="option-desc">Allow soft spillover to adjacent school blocks when departmental home block rooms are at peak capacity</span>
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
              </div>
            )}

            {/* Summary & Generator Action Bar (Persistent across all tabs) */}
            <div className="config-summary" style={{ marginTop: '1.5rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '1.25rem' }}>
                  <h4>Generation Summary</h4>
                  <div className="summary-items">
                    <div className="summary-item">
                      <span className="summary-label">Scope</span>
                      <span className="summary-value" style={{ color: 'var(--color-accent-blue-light)', fontWeight: 600 }}>
                        {config.scope_type === 'all'
                          ? '🌐 Whole Campus (All 178 Depts)'
                          : config.scope_type === 'block'
                            ? `🏢 Block (${config.block_name})`
                            : '🏛️ Single Department'}
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">Subjects</span>
                      <span className="summary-value">
                        {config.scope_type === 'all'
                          ? `All Campus (~${genCourseTotal || 2886})`
                          : config.scope_type === 'block'
                            ? `All in ${config.block_name} (~${genCourseTotal || 'All'})`
                            : `${config.subject_ids.length} of ${subjects.length}`}
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">Rooms</span>
                      <span className="summary-value">
                        {config.scope_type === 'all'
                          ? `All Campus (${rooms.length})`
                          : config.scope_type === 'block'
                            ? `Block & Central (${rooms.filter(r => r.building?.toLowerCase().includes((config.block_name || '').toLowerCase()) || r.building?.toLowerCase().includes('central')).length})`
                            : `${config.room_ids.length} of ${rooms.length}`}
                      </span>
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

                  {/* Pre-generation Load & ETA Estimate */}
                  {!generating && (() => {
                    const eta = getUpfrontEtaEstimate();
                    return (
                      <div style={{
                        marginTop: '1.25rem',
                        padding: '0.85rem 1.1rem',
                        background: 'rgba(255, 255, 255, 0.03)',
                        border: `1px solid ${eta.color}40`,
                        borderRadius: '10px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.45rem',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            ⏱️ Estimated Solver Duration:
                          </span>
                          <span style={{
                            fontSize: '0.82rem',
                            fontWeight: 700,
                            padding: '0.25rem 0.65rem',
                            borderRadius: '12px',
                            background: `${eta.color}20`,
                            color: eta.color,
                            border: `1px solid ${eta.color}50`
                          }}>
                            {eta.formatted} • {eta.label}
                          </span>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                          {eta.desc}
                        </p>
                        {eta.isUpgradedToAll && (
                          <div style={{ fontSize: '0.76rem', color: '#f59e0b', marginTop: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <span>🌐</span>
                            <span><strong>Campus-Wide Scope Active:</strong> 'All Departments (Global)' will execute the multi-block wave engine.</span>
                          </div>
                        )}
                      </div>
                    );
                  })()}

                  {/* Real-Time Live Progress Card during Generation */}
                  {generating && (
                    <div style={{
                      marginTop: '1.25rem',
                      padding: '1.25rem',
                      background: 'linear-gradient(145deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95))',
                      border: '1px solid rgba(59, 130, 246, 0.4)',
                      borderRadius: '12px',
                      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
                          <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#fff' }}>
                            Generating Timetable ({Math.round(generationProgress?.percent || 5)}%)
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                          <button
                            type="button"
                            className="btn btn-danger btn-sm"
                            id="btn-cancel-generation-inline"
                            disabled={taskProgress.isCancelling}
                            onClick={() => taskProgress.cancelTask()}
                            style={{
                              fontSize: '0.75rem',
                              padding: '0.25rem 0.65rem',
                              background: taskProgress.confirmingCancel ? 'rgba(239, 68, 68, 0.4)' : 'rgba(239, 68, 68, 0.2)',
                              color: taskProgress.confirmingCancel ? '#fff' : '#f87171',
                              border: taskProgress.confirmingCancel ? '1px solid #ef4444' : '1px solid rgba(239, 68, 68, 0.45)',
                              fontWeight: taskProgress.confirmingCancel ? 700 : 500,
                              transition: 'all 0.2s ease',
                            }}
                          >
                            {taskProgress.isCancelling
                              ? 'Cancelling...'
                              : taskProgress.confirmingCancel
                                ? '⚠️ Confirm?'
                                : '🛑 Cancel'}
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => {
                              setIsProgressMinimized(true);
                              setShowConfig(false);
                            }}
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                          >
                            Minimize ↘
                          </button>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div style={{
                        width: '100%',
                        height: '10px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        borderRadius: '5px',
                        overflow: 'hidden',
                        marginBottom: '0.85rem',
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${Math.max(5, Math.min(100, generationProgress?.percent || 5))}%`,
                          background: 'linear-gradient(90deg, #3b82f6, #8b5cf6, #10b981)',
                          borderRadius: '5px',
                          transition: 'width 0.4s ease-in-out',
                        }} />
                      </div>

                      {/* Current Wave details */}
                      <div style={{
                        fontSize: '0.82rem',
                        fontWeight: 600,
                        color: 'var(--color-accent-blue-light, #93c5fd)',
                        marginBottom: '0.75rem',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}>
                        {generationProgress?.totalWaves > 1
                          ? `🌊 Wave ${generationProgress?.currentWave || 0} of ${generationProgress?.totalWaves}: ${generationProgress?.currentWaveName || 'Initializing...'}`
                          : `⚙️ ${generationProgress?.currentWaveName || 'Solving constraints...'}`}
                      </div>

                      {/* Telemetry Stats Ticker */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '0.5rem',
                        padding: '0.6rem',
                        background: 'rgba(0, 0, 0, 0.25)',
                        borderRadius: '8px',
                        textAlign: 'center',
                      }}>
                        <div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Elapsed</div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>
                            {formatSeconds(generationProgress?.elapsedSeconds)}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>ETA Remaining</div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-accent-emerald, #10b981)' }}>
                            ~{formatSeconds(generationProgress?.etaRemainingSeconds)}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Scheduled</div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-accent-blue-light, #93c5fd)' }}>
                            {generationProgress?.sessionsScheduled || 0}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div style={{ marginTop: '1rem' }}>
                    <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Draft Name</label>
                    <input type="text" className="form-input" style={{ width: '100%' }} value={draftName} onChange={e => setDraftName(e.target.value)} disabled={generating} />
                  </div>

                  <button
                    className="btn btn-primary btn-lg"
                    onClick={handleGenerate}
                    disabled={generating || (config.scope_type === 'department' && selectedDepartmentId && config.subject_ids.length === 0)}
                    style={{ width: '100%', marginTop: '1.25rem' }}
                  >
                    {generating
                      ? `⏳ Generating... (~${formatDurationDisplay(generationProgress?.etaRemainingSeconds)} left)`
                      : config.scope_type === 'all' || (!selectedDepartmentId && config.scope_type === 'department')
                        ? '⚡ Generate Whole Campus Timetable (All 178 Departments)'
                        : config.scope_type === 'block'
                          ? `⚡ Generate Block Timetable (${config.block_name})`
                          : `⚡ Generate Department Draft (${config.subject_ids.length} subjects)`}
                  </button>
                </div>
          </div>
        </div>
      )}

      {/* ── Multi-Timetable View Switcher Hub or Personal Schedule Banner ── */}
      {!isAdmin ? (
        <div id="timetable-grid-section" className="personal-schedule-banner glass-card" style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          padding: '1.1rem 1.6rem',
          marginBottom: '1.25rem',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85))',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: isStudent ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              border: isStudent ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem'
            }}>
              {isStudent ? '🎓' : '👨‍🏫'}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: '#fff' }}>
                  {isStudent
                    ? (user?.student_profile?.department_name
                        ? `${user.student_profile.department_name} · Semester ${user.student_profile.semester}`
                        : 'Enrolled Classes & Electives')
                    : (user?.faculty_profile?.department_name
                        ? `${user.faculty_profile.department_name} · ${userFullName || 'Faculty'}`
                        : (userFullName ? `Prof. ${userFullName}` : 'Teaching Routine'))}
                </span>
                <span className="badge" style={{
                  fontSize: '0.78rem',
                  padding: '0.2rem 0.55rem',
                  background: isStudent ? 'rgba(59, 130, 246, 0.25)' : 'rgba(16, 185, 129, 0.25)',
                  color: isStudent ? '#93c5fd' : '#a7f3d0',
                  border: isStudent ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)'
                }}>
                  {isStudent ? 'Enrolled Schedule' : 'Assigned Teaching'}
                </span>
                {isStudent && user?.student_profile?.is_ta && (
                  <span className="badge" style={{
                    fontSize: '0.78rem',
                    padding: '0.2rem 0.55rem',
                    background: 'rgba(245, 158, 11, 0.25)',
                    color: '#fde68a',
                    border: '1px solid rgba(245, 158, 11, 0.4)'
                  }}>
                    ⭐ TA Assignments Included
                  </span>
                )}
              </div>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                {isStudent
                  ? `Displaying core department courses, enrolled electives, and assigned TA lab sessions (${timetable.length} classes scheduled)`
                  : `Displaying assigned lectures, laboratories, and approved substitute teaching duties (${timetable.length} classes scheduled)`}
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="text"
              className="form-input"
              placeholder="🔍 Filter my classes..."
              value={viewSearchTerm}
              onChange={(e) => setViewSearchTerm(e.target.value)}
              style={{ width: '210px', padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
            />
            {viewSearchTerm && (
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={() => setViewSearchTerm('')}
                style={{ padding: '0.35rem 0.6rem', fontSize: '0.8rem' }}
              >
                Clear
              </button>
            )}
          </div>
        </div>
      ) : (
        <>
          {/* ── Multi-Timetable View Switcher Hub ── */}
          <div id="timetable-grid-section" className="timetable-view-switcher">
            <button
              type="button"
              className={`view-switch-btn ${viewMode === 'department' ? 'active' : ''}`}
              onClick={() => setViewMode('department')}
            >
              🏛️ By Department & Semester
            </button>
            <button
              type="button"
              className={`view-switch-btn ${viewMode === 'block' ? 'active' : ''}`}
              onClick={() => setViewMode('block')}
            >
              🏢 By Academic Block
            </button>
            <button
              type="button"
              className={`view-switch-btn ${viewMode === 'room' ? 'active' : ''}`}
              onClick={() => setViewMode('room')}
            >
              📍 By Room Schedule ({rooms.length})
            </button>
            <button
              type="button"
              className={`view-switch-btn ${viewMode === 'faculty' && viewFacultyName !== userFullName ? 'active' : ''}`}
              onClick={() => setViewMode('faculty')}
            >
              👨‍🏫 By Faculty Schedule
            </button>
            <button
              type="button"
              className={`view-switch-btn ${viewMode === 'all' ? 'active' : ''}`}
              onClick={() => setViewMode('all')}
            >
              🌐 All Campus Master
            </button>
          </div>

          {/* ── View Context Controls Bar ── */}
          <div className="view-context-bar">
            <div className="view-context-filters">
              {viewMode === 'department' && (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Department:</span>
                    <select
                      className="form-select"
                      style={{ minWidth: '260px', maxWidth: '380px' }}
                      value={viewDeptId}
                      onChange={(e) => setViewDeptId(e.target.value)}
                    >
                      <option value="">-- All Departments --</option>
                      {departments.map(d => (
                        <option key={d.id} value={d.id}>{d.name} ({d.dept_id || `DEP-${d.id}`})</option>
                      ))}
                    </select>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Semester:</span>
                    <div className="semester-pill-group">
                      <button
                        type="button"
                        className={`semester-pill ${viewSemester === '' ? 'active' : ''}`}
                        onClick={() => setViewSemester('')}
                      >
                        All
                      </button>
                      {[1, 2, 3, 4, 5, 6, 7, 8].map(s => (
                        <button
                          key={s}
                          type="button"
                          className={`semester-pill ${String(viewSemester) === String(s) ? 'active' : ''}`}
                          onClick={() => setViewSemester(String(s))}
                        >
                          S{s}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {viewMode === 'block' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Academic Block:</span>
                  <div className="block-filter-pills" style={{ margin: 0 }}>
                    {Object.entries(ACADEMIC_BLOCKS).map(([bKey, bName]) => (
                      <button
                        key={bKey}
                        type="button"
                        className={`block-filter-pill ${viewBlock === bKey ? 'active' : ''}`}
                        onClick={() => setViewBlock(bKey)}
                      >
                        {bKey}
                      </button>
                    ))}
                    <button
                      type="button"
                      className={`block-filter-pill ${viewBlock === 'Central' ? 'active' : ''}`}
                      onClick={() => setViewBlock('Central')}
                    >
                      Central Complex
                    </button>
                  </div>
                </div>
              )}

              {viewMode === 'room' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Classroom / Facility:</span>
                  <select
                    className="form-select"
                    style={{ minWidth: '280px', maxWidth: '400px' }}
                    value={viewRoomNumber}
                    onChange={(e) => setViewRoomNumber(e.target.value)}
                  >
                    <option value="">-- All {rooms.length} Campus Rooms --</option>
                    {rooms.map(r => (
                      <option key={r.id} value={r.room_number}>
                        {r.room_number} ({r.building}) — {r.room_type} · {r.capacity} seats
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {viewMode === 'faculty' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Faculty Instructor:</span>
                  <select
                    className="form-select"
                    style={{ minWidth: '240px', maxWidth: '340px' }}
                    value={viewFacultyName}
                    onChange={(e) => setViewFacultyName(e.target.value)}
                  >
                    <option value="">-- All Faculty Members --</option>
                    {[...new Set(timetable.map(t => t.faculty_name).filter(Boolean))].sort().map(f => (
                      <option key={f} value={f}>{f}</option>
                    ))}
                  </select>
                </div>
              )}

              {viewMode === 'all' && (
                <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                  🌐 Displaying master campus-wide routine across all 9 blocks and departments
                </span>
              )}
            </div>

            {/* Live quick search across class cards in any active view */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="text"
                className="form-input"
                placeholder="🔍 Quick filter classes..."
                value={viewSearchTerm}
                onChange={(e) => setViewSearchTerm(e.target.value)}
                style={{ width: '180px', padding: '0.35rem 0.65rem', fontSize: '0.82rem' }}
              />
              {viewSearchTerm && (
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => setViewSearchTerm('')}
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </>
      )}

      {/* ── Timetable Grid ──────────────────────────────────────────── */}
      {timetable.length === 0 ? (
        <div className="glass-card" style={{ padding: '3rem' }}>
          <div className="empty-state">
            <div className="empty-icon">📅</div>
            <h3>No Classes Scheduled</h3>
            <p>
              {isAdmin
                ? 'Click "Configure" to set constraints, then "Generate" to create a conflict-free timetable.'
                : isStudent
                  ? 'No classes found for your current enrollment and semester. Contact your academic advisor or administrator.'
                  : isFaculty
                    ? 'No teaching sessions currently assigned to you for this published timetable.'
                    : 'The administrator has not published a timetable yet.'}
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

          {/* Notice when current block view has 0 classes in this version */}
          {viewMode === 'block' && blockClassCount === 0 && timetable.length > 0 && (
            <div style={{ padding: '0.85rem 1.15rem', marginBottom: '1rem', background: 'rgba(234, 179, 8, 0.12)', border: '1px solid rgba(234, 179, 8, 0.35)', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#fef08a', fontSize: '0.88rem' }}>
              <span style={{ fontSize: '1.25rem' }}>💡</span>
              <div>
                <strong>No classes scheduled in {viewBlock} for "{selectedVersion?.name || 'this draft'}".</strong>
                <div style={{ fontSize: '0.82rem', color: 'rgba(255, 255, 255, 0.75)', marginTop: '0.15rem' }}>
                  This draft version was generated for <strong>{detectedScope || 'another specific block or department'}</strong>.
                  To see all 9 blocks populated with classes, select a <em>Whole Campus</em> version from the dropdown above or click <strong>New Sandbox Draft → Scope: Whole Campus</strong> to generate.
                </div>
              </div>
            </div>
          )}

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
                      const slotClasses = getClassesForSlot(day, time);
                      const ts = getTimeslotForDayTime(day, time);
                      const dropId = ts ? `${day}-${time}-${ts.id}` : `${day}-${time}-unknown`;
                      
                      let isValidDrop = null;
                      const activeEntry = activeDragItem ? timetable.find(t => t.id === activeDragItem) : null;
                      if (activeEntry && ts) {
                        const timeConflicts = timetable.filter(t => t.day === day && t.start_time?.substring(0, 5) === time && t.id !== activeEntry.id);
                        const facultyConflict = activeEntry.faculty_name && timeConflicts.some(t => t.faculty_name === activeEntry.faculty_name);
                        const roomConflict = activeEntry.room_number && timeConflicts.some(t => t.room_number === activeEntry.room_number);
                        if (facultyConflict || roomConflict) {
                           isValidDrop = false;
                        } else {
                           isValidDrop = true;
                        }
                      }

                      return (
                        <div 
                          className={`${day === mobileDay ? 'mobile-active' : 'mobile-hidden'}`} 
                          key={`${day}-${time}`} 
                          onClick={(e) => {
                            if (slotClasses.length === 0 && isAdmin && ts && (e.target.classList.contains('timetable-cell') || e.target.closest('.timetable-cell') === e.target)) {
                              setAddEventSlot(ts);
                              setShowAddEventModal(true);
                            }
                          }}
                        >
                          <DroppableCell id={dropId} isValidDrop={isValidDrop}>
                            {slotClasses.map(cls => (
                              <DraggableClassCard 
                                key={cls.id}
                                cls={cls} 
                                isLocked={isEntryLocked(cls)} 
                                color={getSubjectColor(cls)} 
                                isAdmin={isAdmin} 
                                isFaculty={isFaculty}
                                isOwnClass={cls.faculty_name === userFullName}
                                showConfig={showConfig}
                                onLockToggle={toggleDBLockEntry}
                                onReportAbsence={(c) => {
                                  setAbsenceClass(c);
                                  setAbsenceDate(getNextDateForDay(c.day));
                                  setAbsenceCategory('Sick Leave');
                                  setAbsenceCustomNotes('');
                                  setAbsenceTargetSubstituteId('');
                                  setShowAbsenceModal(true);
                                }}
                                onFindSwap={handleFindSwap}
                              />
                            ))}
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

      {/* Substitute & Absence Coverage Management */}
      {(isFaculty || isAdmin) && (pendingSubstitutes.length > 0 || myReportedAbsences.length > 0) && (
        <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Available Substitute Requests */}
          {pendingSubstitutes.length > 0 && (
            <div
              className="glass-card animate-fade-in-up stagger-4"
              style={{
                opacity: 0,
                padding: '1.5rem',
                borderLeft: '4px solid var(--color-accent-emerald)',
                background: 'var(--color-bg-surface, rgba(17, 24, 39, 0.7))',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h3 className="section-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>🙋</span> Available Substitute Requests
                  <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.55rem', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', fontWeight: 600 }}>
                    {pendingSubstitutes.length} pending
                  </span>
                </h3>
                <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                  Classes needing coverage. Click 'Accept' to cover the lecture.
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                {pendingSubstitutes.map(sub => (
                  <div
                    key={sub.id}
                    style={{
                      padding: '1.15rem',
                      background: 'var(--color-bg-glass, rgba(255, 255, 255, 0.03))',
                      border: '1px solid var(--color-border)',
                      borderRadius: '10px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-primary)' }}>
                            {sub.subject_code ? `${sub.subject_code}` : 'Class Session'}
                            {sub.subject_name && (
                              <span style={{ fontWeight: 400, fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginLeft: '0.35rem' }}>
                                · {sub.subject_name}
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '0.2rem' }}>
                            👨‍🏫 Prof. <strong>{sub.faculty_name}</strong> {sub.faculty_department ? `(${sub.faculty_department})` : ''}
                          </div>
                        </div>
                        <span style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(234, 179, 8, 0.18)', color: '#facc15', fontWeight: 600, whiteSpace: 'nowrap' }}>
                          Needs Coverage
                        </span>
                      </div>

                      <div style={{ background: 'rgba(0, 0, 0, 0.15)', padding: '0.65rem', borderRadius: '6px', fontSize: '0.83rem', display: 'flex', flexDirection: 'column', gap: '0.3rem', margin: '0.6rem 0' }}>
                        <div>
                          <strong>📅 Date:</strong> {sub.date} {sub.day ? `(${dayLabels[sub.day] || sub.day})` : ''}
                        </div>
                        {(sub.start_time || sub.end_time) && (
                          <div>
                            <strong>⏰ Time:</strong> {formatTime(sub.start_time || '')} {sub.end_time ? `- ${formatTime(sub.end_time)}` : ''}
                          </div>
                        )}
                        {(sub.room_number || sub.building) && (
                          <div>
                            <strong>📍 Room:</strong> {sub.room_number || 'TBD'} {sub.building ? `(${sub.building})` : ''}
                          </div>
                        )}
                      </div>

                      <div style={{ fontSize: '0.83rem', color: 'var(--color-text-secondary)', fontStyle: 'italic', background: 'rgba(255, 255, 255, 0.02)', padding: '0.5rem', borderRadius: '4px', borderLeft: '3px solid var(--color-border)' }}>
                        "{sub.reason}"
                      </div>
                    </div>

                    <button
                      className="btn btn-sm btn-primary"
                      style={{
                        marginTop: '1rem',
                        width: '100%',
                        background: 'var(--color-accent-emerald)',
                        borderColor: 'var(--color-accent-emerald)',
                        fontWeight: 600,
                      }}
                      onClick={() => handleAcceptSubstitute(sub.id)}
                      disabled={acceptingSubstituteId === sub.id}
                    >
                      {acceptingSubstituteId === sub.id ? 'Accepting...' : '✅ Accept Class Coverage'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* My Reported Absences & Coverage Status */}
          {myReportedAbsences.length > 0 && (
            <div
              className="glass-card animate-fade-in-up stagger-4"
              style={{
                opacity: 0,
                padding: '1.5rem',
                borderLeft: '4px solid var(--color-accent-blue)',
                background: 'var(--color-bg-surface, rgba(17, 24, 39, 0.7))',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h3 className="section-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>📋</span> {isAdmin ? 'Campus Absence Tracking' : 'My Reported Absences'}
                  <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.55rem', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', fontWeight: 600 }}>
                    {myReportedAbsences.length} total
                  </span>
                </h3>
                <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                  Track coverage status and substitute assignments for reported class absences.
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                {myReportedAbsences.map(sub => {
                  const isApproved = sub.status === 'approved';
                  return (
                    <div
                      key={sub.id}
                      style={{
                        padding: '1.15rem',
                        background: 'var(--color-bg-glass, rgba(255, 255, 255, 0.03))',
                        border: '1px solid var(--color-border)',
                        borderRadius: '10px',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.5rem' }}>
                          <div>
                            <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-primary)' }}>
                              {sub.subject_code ? `${sub.subject_code}` : 'Class Session'}
                              {sub.subject_name && (
                                <span style={{ fontWeight: 400, fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginLeft: '0.35rem' }}>
                                  · {sub.subject_name}
                                </span>
                              )}
                            </div>
                            {isAdmin && (
                              <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: '0.2rem' }}>
                                Instructor: <strong>{sub.faculty_name}</strong>
                              </div>
                            )}
                          </div>
                          {isApproved ? (
                            <span style={{ fontSize: '0.72rem', padding: '0.2rem 0.55rem', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', fontWeight: 600, whiteSpace: 'nowrap' }}>
                              🟢 Covered
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.72rem', padding: '0.2rem 0.55rem', borderRadius: '4px', background: 'rgba(234, 179, 8, 0.2)', color: '#fbbf24', fontWeight: 600, whiteSpace: 'nowrap' }}>
                              🟡 Pending
                            </span>
                          )}
                        </div>

                        <div style={{ background: 'rgba(0, 0, 0, 0.15)', padding: '0.65rem', borderRadius: '6px', fontSize: '0.83rem', display: 'flex', flexDirection: 'column', gap: '0.3rem', margin: '0.6rem 0' }}>
                          <div>
                            <strong>📅 Date:</strong> {sub.date} {sub.day ? `(${dayLabels[sub.day] || sub.day})` : ''}
                          </div>
                          {(sub.start_time || sub.end_time) && (
                            <div>
                              <strong>⏰ Time:</strong> {formatTime(sub.start_time || '')} {sub.end_time ? `- ${formatTime(sub.end_time)}` : ''}
                            </div>
                          )}
                          {(sub.room_number || sub.building) && (
                            <div>
                              <strong>📍 Room:</strong> {sub.room_number || 'TBD'} {sub.building ? `(${sub.building})` : ''}
                            </div>
                          )}
                        </div>

                        <div style={{ fontSize: '0.83rem', color: 'var(--color-text-secondary)', fontStyle: 'italic', background: 'rgba(255, 255, 255, 0.02)', padding: '0.5rem', borderRadius: '4px', borderLeft: '3px solid var(--color-border)', marginBottom: '0.75rem' }}>
                          "{sub.reason}"
                        </div>

                        <div style={{ fontSize: '0.84rem', padding: '0.5rem 0.75rem', borderRadius: '6px', background: isApproved ? 'rgba(16, 185, 129, 0.1)' : 'rgba(234, 179, 8, 0.08)', border: `1px solid ${isApproved ? 'rgba(16, 185, 129, 0.25)' : 'rgba(234, 179, 8, 0.2)'}` }}>
                          {isApproved ? (
                            <span style={{ color: '#34d399', fontWeight: 600 }}>
                              Covered by Prof. {sub.substitute_name || 'Assigned Substitute'} {sub.substitute_department ? `(${sub.substitute_department})` : ''}
                            </span>
                          ) : (
                            <span style={{ color: '#fbbf24' }}>
                              {sub.substitute_name
                                ? `Directed Request to: Prof. ${sub.substitute_name}`
                                : 'Broadcast to all available faculty'}
                            </span>
                          )}
                        </div>
                      </div>

                      {!isApproved && (
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          style={{
                            marginTop: '1rem',
                            width: '100%',
                            color: 'var(--color-accent-red)',
                            borderColor: 'rgba(239, 68, 68, 0.3)',
                          }}
                          onClick={() => handleCancelAbsence(sub.id)}
                          disabled={cancellingAbsenceId === sub.id}
                        >
                          {cancellingAbsenceId === sub.id ? 'Cancelling...' : '✖ Cancel Absence Request'}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
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
          <div className="modal-content glass-card" onClick={e => e.stopPropagation()} style={{ width: '420px' }}>
            <h3>➕ Add Custom Event</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
              Scheduled for: <strong>{dayLabels[addEventSlot.day] || addEventSlot.day}</strong> at <strong>{formatTime(addEventSlot.start_time)}</strong>
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '0.25rem' }}>Event Title</label>
                <input 
                  type="text" 
                  className="form-input" 
                  style={{ width: '100%' }}
                  placeholder="e.g. Guest Lecture, Department Meeting" 
                  value={newEvent.title}
                  onChange={e => setNewEvent({...newEvent, title: e.target.value})}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '0.25rem' }}>Room / Venue</label>
                <select
                  className="form-select"
                  style={{ width: '100%' }}
                  value={newEvent.roomId || ''}
                  onChange={e => setNewEvent({...newEvent, roomId: e.target.value})}
                >
                  <option value="">Select Room...</option>
                  {rooms.map(r => (
                    <option key={r.id} value={r.id}>
                      {r.room_number} ({r.building || 'Campus'}) - Cap: {r.capacity}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Badge Color:</label>
                <input 
                  type="color" 
                  value={newEvent.color}
                  onChange={e => setNewEvent({...newEvent, color: e.target.value})}
                  style={{ cursor: 'pointer', borderRadius: '4px', border: '1px solid var(--color-border)', width: '38px', height: '36px', padding: 0 }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowAddEventModal(false)}>Cancel</button>
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={async () => {
                if (!newEvent.title.trim()) return toast.error('Event title is required');
                if (!newEvent.roomId) return toast.error('Please select a room');
                try {
                  const res = await api.post('/api/scheduler/timetable/', {
                    time_slot: addEventSlot.id,
                    room: parseInt(newEvent.roomId, 10),
                    event_title: newEvent.title.trim(),
                    event_color: newEvent.color,
                    event_type: 'custom',
                    version: selectedVersionId || undefined,
                    is_locked: true
                  });
                  setTimetable(prev => [...prev, res.data]);
                  setShowAddEventModal(false);
                  setNewEvent({ title: '', color: '#3b82f6', roomId: '' });
                  toast.success('Event added successfully!');
                } catch (err) {
                  toast.error(err.response?.data?.error || err.response?.data?.detail || 'Failed to add event');
                }
              }}>Save Event</button>
            </div>
          </div>
        </div>
      )}

      {/* Report Absence Modal */}
      {showAbsenceModal && absenceClass && (
        <div className="modal-overlay" onClick={() => !submittingAbsence && setShowAbsenceModal(false)}>
          <div
            className="modal-content glass-card"
            onClick={e => e.stopPropagation()}
            style={{ maxWidth: '520px', width: '92%', maxHeight: '90vh', overflowY: 'auto' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>🚨</span> Report Class Absence
              </h3>
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                style={{ padding: '0.2rem 0.5rem', borderRadius: '50%' }}
                onClick={() => setShowAbsenceModal(false)}
                disabled={submittingAbsence}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: 0, marginBottom: '1.25rem' }}>
              Submit an absence notice for this class. You can request a specific colleague or broadcast to all department faculty.
            </p>

            {/* Class Details Card */}
            <div
              style={{
                padding: '0.9rem',
                borderRadius: '8px',
                background: 'rgba(0, 0, 0, 0.25)',
                border: '1px solid var(--color-border)',
                marginBottom: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.45rem',
                fontSize: '0.88rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.98rem', color: 'var(--color-text-primary)' }}>
                  📘 {absenceClass.subject_code} {absenceClass.subject_name ? `· ${absenceClass.subject_name}` : ''}
                </span>
                <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', fontWeight: 600 }}>
                  {absenceClass.subject_type === 'lab' ? '🧪 2h Lab' : '📖 Lecture'}
                </span>
              </div>
              <div style={{ color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', fontSize: '0.84rem' }}>
                <span>📅 {dayLabels[absenceClass.day] || absenceClass.day}</span>
                <span>⏰ {formatTime(absenceClass.start_time)} {absenceClass.end_time ? `- ${formatTime(absenceClass.end_time)}` : ''}</span>
                <span>📍 Room {absenceClass.room_number || 'TBD'} {absenceClass.building ? `(${absenceClass.building})` : ''}</span>
              </div>
            </div>

            {/* Form Inputs */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Absence Date: <span style={{ color: 'var(--color-accent-red)' }}>*</span>
                </label>
                <input
                  type="date"
                  className="form-input"
                  style={{ width: '100%' }}
                  min={new Date().toISOString().split('T')[0]}
                  value={absenceDate}
                  onChange={(e) => setAbsenceDate(e.target.value)}
                  required
                />
                <span style={{ fontSize: '0.76rem', color: 'var(--color-text-muted)', marginTop: '0.25rem', display: 'block' }}>
                  Default set to next upcoming {dayLabels[absenceClass.day] || absenceClass.day}. Change if reporting for another date.
                </span>
              </div>

              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Reason Category: <span style={{ color: 'var(--color-accent-red)' }}>*</span>
                </label>
                <select
                  className="form-select"
                  style={{ width: '100%' }}
                  value={absenceCategory}
                  onChange={(e) => setAbsenceCategory(e.target.value)}
                >
                  <option value="Sick Leave">🤒 Sick Leave / Medical</option>
                  <option value="Emergency">🚨 Personal Emergency</option>
                  <option value="Academic Conference">🎓 Academic Conference / Symposium</option>
                  <option value="Official University Duty">🏛️ Official University Duty / Admin Task</option>
                  <option value="Personal Leave">🏖️ Personal Leave</option>
                  <option value="Other">📝 Other</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Handover Notes & Syllabus Topic (Optional):
                </label>
                <textarea
                  className="form-input"
                  style={{ width: '100%', height: '75px', resize: 'vertical' }}
                  placeholder="e.g. Please cover Chapter 4 (Binary Search Trees). Presentation slides are available on LMS."
                  value={absenceCustomNotes}
                  onChange={(e) => setAbsenceCustomNotes(e.target.value)}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Substitute Colleague (Optional):
                </label>
                <select
                  className="form-select"
                  style={{ width: '100%' }}
                  value={absenceTargetSubstituteId}
                  onChange={(e) => setAbsenceTargetSubstituteId(e.target.value)}
                >
                  <option value="">📢 Open Request (Broadcast to all eligible faculty)</option>
                  {facultyList
                    .filter(f => f.id !== user?.faculty_profile?.id && f.user?.id !== user?.id)
                    .map(f => (
                      <option key={f.id} value={f.id}>
                        Prof. {f.user?.first_name} {f.user?.last_name} ({f.department_name || f.department || 'Faculty'}{f.employee_id ? ` · ${f.employee_id}` : ''})
                      </option>
                    ))}
                </select>
                <span style={{ fontSize: '0.76rem', color: 'var(--color-text-muted)', marginTop: '0.25rem', display: 'block' }}>
                  Selecting a colleague sends a direct substitution request to them first.
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.75rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ flex: 1 }}
                onClick={() => setShowAbsenceModal(false)}
                disabled={submittingAbsence}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                style={{
                  flex: 1.5,
                  background: 'var(--color-accent-red)',
                  borderColor: 'var(--color-accent-red)',
                  fontWeight: 600,
                }}
                onClick={handleReportAbsence}
                disabled={submittingAbsence}
              >
                {submittingAbsence ? 'Submitting Request...' : '🚨 Broadcast Request'}
              </button>
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

      {/* Confirm Delete Draft Timetable Modal */}
      {confirmDeleteVersion && (
        <div className="modal-overlay" onClick={() => !deletingVersion && setConfirmDeleteVersion(null)}>
          <div className="modal-content glass-card confirm-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: '440px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ 
                width: '38px', 
                height: '38px', 
                borderRadius: '8px', 
                background: 'rgba(239, 68, 68, 0.15)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                fontSize: '1.2rem',
                color: '#ef4444' 
              }}>
                🗑️
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Delete Draft Timetable</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Sandbox Version Removal</span>
              </div>
            </div>

            <p style={{ marginBottom: '1rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
              Are you sure you want to delete the draft timetable <strong>"{confirmDeleteVersion.name}"</strong>?
            </p>
            <p style={{ marginBottom: '1.5rem', fontSize: '0.85rem', color: 'var(--color-text-muted)', background: 'rgba(239, 68, 68, 0.08)', padding: '0.75rem', borderRadius: '6px', borderLeft: '3px solid #ef4444' }}>
              ⚠️ This will remove all scheduled sessions generated for this sandbox. This action cannot be undone.
            </p>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => setConfirmDeleteVersion(null)} 
                disabled={deletingVersion}
              >
                Cancel
              </button>
              <button 
                className="btn btn-danger" 
                style={{ background: '#ef4444', borderColor: '#ef4444' }} 
                onClick={handleDeleteVersion}
                disabled={deletingVersion}
              >
                {deletingVersion ? 'Deleting...' : 'Delete Draft'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manage Drafts Modal */}
      {showManageVersionsModal && (
        <div className="modal-overlay" onClick={() => setShowManageVersionsModal(false)}>
          <div className="modal-content glass-card" onClick={e => e.stopPropagation()} style={{ maxWidth: '650px', width: '90%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>📋</span>
                <div>
                  <h3 style={{ margin: 0 }}>Timetable Versions & Drafts</h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                    {versions.length} total versions ({versions.filter(v => !v.is_published).length} drafts)
                  </span>
                </div>
              </div>
              <button className="modal-close" onClick={() => setShowManageVersionsModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--color-text-muted)' }}>✕</button>
            </div>

            {/* Bulk Action Controls */}
            {versions.filter(v => !v.is_published).length > 0 && (
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                padding: '0.6rem 0.8rem', 
                background: 'rgba(255, 255, 255, 0.04)', 
                borderRadius: '8px', 
                marginBottom: '1rem',
                border: '1px solid rgba(255, 255, 255, 0.08)'
              }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600 }}>
                  <input
                    type="checkbox"
                    checked={
                      versions.filter(v => !v.is_published).length > 0 &&
                      selectedDraftIds.length === versions.filter(v => !v.is_published).length
                    }
                    onChange={toggleSelectAllDrafts}
                  />
                  Select All Drafts ({selectedDraftIds.length}/{versions.filter(v => !v.is_published).length})
                </label>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {selectedDraftIds.length > 0 && (
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => setConfirmBulkDelete({ ids: selectedDraftIds, count: selectedDraftIds.length, allDrafts: false })}
                      disabled={deletingVersion}
                      style={{ background: '#ef4444', borderColor: '#ef4444' }}
                    >
                      🗑️ Delete Selected ({selectedDraftIds.length})
                    </button>
                  )}
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setConfirmBulkDelete({ count: versions.filter(v => !v.is_published).length, allDrafts: true })}
                    disabled={deletingVersion}
                    style={{ color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                    title="Delete all draft sandboxes at once"
                  >
                    Delete All Drafts
                  </button>
                </div>
              </div>
            )}

            <div style={{ maxHeight: '360px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {versions.length === 0 ? (
                <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '2rem 0' }}>No timetable versions available.</p>
              ) : (
                versions.map(v => (
                  <div 
                    key={v.id} 
                    style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center', 
                      padding: '0.75rem 1rem', 
                      borderRadius: '8px',
                      background: String(selectedVersionId) === String(v.id) ? 'rgba(59, 130, 246, 0.12)' : 'var(--color-bg-glass)',
                      border: String(selectedVersionId) === String(v.id) ? '1px solid var(--color-accent-blue)' : '1px solid rgba(255, 255, 255, 0.05)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {!v.is_published ? (
                        <input
                          type="checkbox"
                          checked={selectedDraftIds.includes(v.id)}
                          onChange={() => toggleDraftSelect(v.id)}
                          style={{ cursor: 'pointer', transform: 'scale(1.1)' }}
                        />
                      ) : (
                        <span title="Active published timetable is protected" style={{ fontSize: '0.9rem', opacity: 0.6 }}>🔒</span>
                      )}
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 600 }}>{v.name}</span>
                          {v.is_published ? (
                            <span className="badge badge-present" style={{ fontSize: '0.75rem' }}>🟢 Live Published</span>
                          ) : (
                            <span className="badge badge-low" style={{ fontSize: '0.75rem' }}>🟡 Sandbox Draft</span>
                          )}
                          {String(selectedVersionId) === String(v.id) && (
                            <span className="badge badge-medium" style={{ fontSize: '0.7rem' }}>Active View</span>
                          )}
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          Created: {v.created_at ? new Date(v.created_at).toLocaleString() : 'N/A'}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <button 
                        className="btn btn-sm btn-secondary"
                        onClick={() => openRenameModal(v)}
                        title="Rename this timetable"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                      >
                        ✏️ Rename
                      </button>
                      {String(selectedVersionId) !== String(v.id) && (
                        <button 
                          className="btn btn-sm btn-secondary"
                          onClick={() => {
                            setSelectedVersionId(v.id);
                            setShowManageVersionsModal(false);
                          }}
                        >
                          View
                        </button>
                      )}
                      {!v.is_published && (
                        <button 
                          className="btn btn-sm btn-danger"
                          style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', borderColor: '#ef4444' }}
                          onClick={() => {
                            setConfirmDeleteVersion(v);
                          }}
                          title="Delete this draft"
                        >
                          🗑️ Delete
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowManageVersionsModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Bulk Delete Modal */}
      {confirmBulkDelete && (
        <div className="modal-overlay" onClick={() => !deletingVersion && setConfirmBulkDelete(null)}>
          <div className="modal-content glass-card confirm-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: '440px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ 
                width: '38px', 
                height: '38px', 
                borderRadius: '8px', 
                background: 'rgba(239, 68, 68, 0.15)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                fontSize: '1.2rem',
                color: '#ef4444' 
              }}>
                🗑️
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>
                  {confirmBulkDelete.allDrafts ? 'Delete All Draft Timetables' : 'Delete Selected Drafts'}
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  Batch Sandbox Removal
                </span>
              </div>
            </div>

            <p style={{ marginBottom: '1rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
              Are you sure you want to permanently delete <strong>{confirmBulkDelete.count} draft timetable(s)</strong>?
            </p>
            <p style={{ marginBottom: '1.5rem', fontSize: '0.85rem', color: 'var(--color-text-muted)', background: 'rgba(239, 68, 68, 0.08)', padding: '0.75rem', borderRadius: '6px', borderLeft: '3px solid #ef4444' }}>
              ⚠️ This will remove all scheduled sessions across these sandboxes. The active published timetable will NOT be affected. This action cannot be undone.
            </p>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => setConfirmBulkDelete(null)} 
                disabled={deletingVersion}
              >
                Cancel
              </button>
              <button 
                className="btn btn-danger" 
                style={{ background: '#ef4444', borderColor: '#ef4444' }} 
                onClick={handleBulkDelete}
                disabled={deletingVersion}
              >
                {deletingVersion ? 'Deleting...' : `Delete ${confirmBulkDelete.count} Drafts`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Timetable Modal */}
      {renamingVersion && (
        <div className="modal-overlay" onClick={() => !savingRename && setRenamingVersion(null)}>
          <div 
            className="modal-content glass-card" 
            onClick={e => e.stopPropagation()} 
            style={{ maxWidth: '440px', width: '92%', padding: '1.75rem' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.3rem' }}>✏️</span>
                <h3 style={{ margin: 0, fontSize: '1.2rem' }}>Rename Timetable</h3>
              </div>
              <button 
                onClick={() => !savingRename && setRenamingVersion(null)}
                style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--color-text-muted)' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleRenameVersion}>
              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Timetable Name
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={newVersionName}
                  onChange={e => setNewVersionName(e.target.value)}
                  placeholder="e.g. Fall 2026 Official Campus Schedule"
                  autoFocus
                  required
                  maxLength={120}
                  style={{ width: '100%', padding: '0.65rem 0.85rem', fontSize: '0.95rem', borderRadius: '6px' }}
                />
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.4rem' }}>
                  Version #{renamingVersion.id} • {renamingVersion.is_published ? '🟢 Live Published' : '🟡 Sandbox Draft'}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setRenamingVersion(null)}
                  disabled={savingRename}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={savingRename || !newVersionName.trim()}
                >
                  {savingRename ? 'Saving...' : 'Save Name'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}