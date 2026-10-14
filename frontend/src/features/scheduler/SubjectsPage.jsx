import toast from 'react-hot-toast';
import { useState, useEffect, useMemo } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';

/* ─── Tiny modal component ─────────────────────────────────────── */
function Modal({ open, onClose, title, children, maxWidth }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content glass-card"
        onClick={(e) => e.stopPropagation()}
        style={maxWidth ? { maxWidth, width: '92%' } : undefined}
      >
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

/* ─── Confirm dialog ───────────────────────────────────────────── */
function ConfirmDialog({ open, onClose, onConfirm, message }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content glass-card confirm-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <p style={{ marginBottom: '1.5rem', color: 'var(--color-text-secondary)' }}>
          {message}
        </p>
        <div className="confirm-actions">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-danger" onClick={onConfirm}>Delete</button>
        </div>
      </div>
    </div>
  );
}

/* ─── Course / Subject Form ────────────────────────────────────── */
function CourseForm({ initial, faculty, departments, amenitiesList, onSave, saving }) {
  const [form, setForm] = useState({
    code: initial?.code || '',
    name: initial?.name || '',
    faculty: initial?.faculty || '',
    semester: initial?.semester || 1,
    credits: initial?.credits !== undefined ? initial.credits : 3,
    required_capacity: initial?.required_capacity || 30,
    sessions_per_week: initial?.sessions_per_week || 3,
    subject_type: initial?.subject_type || 'lecture',
    description: initial?.description || '',
    amenities: initial?.amenities || [],
    departments: initial?.departments || [],
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleAmenityChange = (amenityId) => {
    setForm(prev => {
      const isSelected = prev.amenities.includes(amenityId);
      return {
        ...prev,
        amenities: isSelected 
          ? prev.amenities.filter(id => id !== amenityId)
          : [...prev.amenities, amenityId]
      };
    });
  };

  const handleDepartmentChange = (deptId) => {
    setForm(prev => {
      const isSelected = prev.departments.includes(deptId);
      return {
        ...prev,
        departments: isSelected
          ? prev.departments.filter(id => id !== deptId)
          : [...prev.departments, deptId]
      };
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      ...form,
      faculty: form.faculty ? parseInt(form.faculty) : null,
      semester: parseInt(form.semester) || 1,
      credits: parseFloat(form.credits) || 0,
      required_capacity: parseInt(form.required_capacity),
      sessions_per_week: parseInt(form.sessions_per_week),
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Course Code *</label>
          <input
            className="form-input"
            name="code"
            value={form.code}
            onChange={handleChange}
            placeholder="e.g. 26-BS-M101"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Semester *</label>
          <select
            className="form-select"
            name="semester"
            value={form.semester}
            onChange={handleChange}
          >
            <option value="1">Semester 1</option>
            <option value="2">Semester 2</option>
            <option value="3">Semester 3</option>
            <option value="4">Semester 4</option>
            <option value="5">Semester 5</option>
            <option value="6">Semester 6</option>
            <option value="7">Semester 7</option>
            <option value="8">Semester 8</option>
          </select>
        </div>
      </div>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Course Name *</label>
          <input
            className="form-input"
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="e.g. Mathematics - I"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Credits</label>
          <input
            className="form-input"
            type="number"
            step="0.5"
            name="credits"
            value={form.credits}
            onChange={handleChange}
            min="0"
            max="10"
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Faculty (Optional)</label>
        <select
          className="form-select"
          name="faculty"
          value={form.faculty}
          onChange={handleChange}
        >
          <option value="">-- Select faculty member (Optional) --</option>
          {faculty.map((f) => {
            const dept = departments.find(d => String(d.id) === String(f.department));
            const deptLabel = dept ? `${dept.dept_id ? `[${dept.dept_id}] ` : ''}${dept.name}` : (f.department_name || 'General');
            return (
              <option key={f.id} value={f.id}>
                {f.user?.first_name} {f.user?.last_name} ({f.employee_id || 'ID'}) — {deptLabel}
              </option>
            );
          })}
        </select>
      </div>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Type</label>
          <select
            className="form-select"
            name="subject_type"
            value={form.subject_type}
            onChange={handleChange}
          >
            <option value="lecture">Lecture (Theory)</option>
            <option value="lab">Laboratory (Practical)</option>
            <option value="seminar">Seminar / Workshop</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Required Capacity</label>
          <input
            className="form-input"
            type="number"
            name="required_capacity"
            value={form.required_capacity}
            onChange={handleChange}
            min="1"
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Sessions / Week</label>
        <input
          className="form-input"
          type="number"
          name="sessions_per_week"
          value={form.sessions_per_week}
          onChange={handleChange}
          min="1"
          max="7"
        />
      </div>
      <div className="form-group">
        <label className="form-label">Description</label>
        <textarea
          className="form-input"
          name="description"
          value={form.description}
          onChange={handleChange}
          placeholder="Optional course description"
          rows={3}
          style={{ resize: 'vertical' }}
        />
      </div>
      <div className="form-group" style={{ marginTop: '1rem' }}>
        <label className="form-label">Associated Departments</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem', maxHeight: '120px', overflowY: 'auto' }}>
          {departments.map(d => (
            <label key={d.id} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'var(--color-bg-glass)', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem' }}>
              <input 
                type="checkbox" 
                checked={form.departments.includes(d.id)}
                onChange={() => handleDepartmentChange(d.id)}
              />
              {d.dept_id ? `[${d.dept_id}] ` : ''}{d.name}
            </label>
          ))}
        </div>
      </div>
      <div className="form-group" style={{ marginTop: '1rem' }}>
        <label className="form-label">Required Amenities</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
          {amenitiesList.map(a => (
            <label key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--color-bg-glass)', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={form.amenities.includes(a.id)}
                onChange={() => handleAmenityChange(a.id)}
              />
              {a.name}
            </label>
          ))}
        </div>
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : initial?.id ? 'Update Course' : 'Add Course'}
      </button>
    </form>
  );
}

/* ─── Dynamic Degree & Academic Filter Definitions ────────────── */
export const getDepartmentDegree = (dept) => {
  if (!dept) return '';
  const progType = typeof dept === 'object' ? dept.program_type : '';
  if (progType && progType.trim()) {
    return progType.trim();
  }
  const name = typeof dept === 'object' ? dept.name || '' : String(dept);
  if (name.includes(' in ')) {
    return name.split(' in ')[0].trim();
  }
  return name.split(' ')[0].trim();
};

const DEGREE_METADATA = {
  'B.Tech': { label: 'B.Tech — Bachelor of Technology', icon: '🎓', color: '#3b82f6' },
  'B.Sc': { label: 'B.Sc — Bachelor of Science', icon: '🔬', color: '#10b981' },
  'M.Tech': { label: 'M.Tech — Master of Technology', icon: '⚡', color: '#6366f1' },
  'M.Sc': { label: 'M.Sc — Master of Science', icon: '🧪', color: '#059669' },
  'BBA': { label: 'BBA — Business Administration', icon: '📊', color: '#8b5cf6' },
  'MBA': { label: 'MBA — Business Administration', icon: '💼', color: '#9333ea' },
  'BCA': { label: 'BCA — Computer Applications', icon: '💻', color: '#06b6d4' },
  'MCA': { label: 'MCA — Computer Applications', icon: '🖥️', color: '#0284c7' },
  'B.Pharm': { label: 'B.Pharm — Pharmacy', icon: '💊', color: '#ec4899' },
  'M.Pharm': { label: 'M.Pharm — Pharmacy', icon: '💉', color: '#db2777' },
  'B.Arch': { label: 'B.Arch — Architecture', icon: '🏛️', color: '#f59e0b' },
  'M.Arch': { label: 'M.Arch — Architecture', icon: '📐', color: '#d97706' },
  'BHMCT': { label: 'BHMCT — Hotel Management', icon: '🏨', color: '#e11d48' },
  'BTTM': { label: 'BTTM — Travel & Tourism', icon: '✈️', color: '#14b8a6' },
  'M.A.': { label: 'M.A. — Master of Arts', icon: '📚', color: '#f97316' },
  'M.Phil': { label: 'M.Phil — Philosophy', icon: '📖', color: '#ea580c' },
  'MMS': { label: 'MMS — Management Studies', icon: '📑', color: '#7c3aed' },
  'B.Optom': { label: 'B.Optom — Optometry', icon: '👁️', color: '#2563eb' },
  'M.Optom': { label: 'M.Optom — Optometry', icon: '👁️', color: '#1d4ed8' },
  'BMLS': { label: 'BMLS — Medical Lab Science', icon: '🩺', color: '#0d9488' },
  'MMLS': { label: 'MMLS — Medical Lab Science', icon: '🔬', color: '#0f766e' },
  'BMRIT': { label: 'BMRIT — Radiology & Imaging', icon: '🩻', color: '#4f46e5' },
  'MMRIT': { label: 'MMRIT — Radiology & Imaging', icon: '🩻', color: '#4338ca' },
  'BND': { label: 'BND — Nutrition & Dietetics', icon: '🥗', color: '#16a34a' },
  'B.Psy': { label: 'B.Psy — Psychology', icon: '🧠', color: '#c026d3' },
  'MHA': { label: 'MHA — Hospital Administration', icon: '🏥', color: '#dc2626' },
  'MMA': { label: 'MMA — Management Administration', icon: '📋', color: '#7e22ce' },
  'MPH': { label: 'MPH — Public Health', icon: '🌐', color: '#0891b2' },
  'MTTM': { label: 'MTTM — Tourism & Travel', icon: '🌍', color: '#0d9488' },
};

const getDegreeMeta = (degCode) => {
  if (!degCode) return { label: 'All Degrees', icon: '🌐', color: 'var(--color-accent-blue)' };
  if (DEGREE_METADATA[degCode]) return DEGREE_METADATA[degCode];
  const isMaster = degCode.startsWith('M') || degCode.startsWith('Master');
  const isBachelor = degCode.startsWith('B') || degCode.startsWith('Bachelor');
  return {
    label: degCode,
    icon: isMaster ? '🎓' : isBachelor ? '📘' : '🏛️',
    color: '#6366f1',
  };
};

const YEAR_OPTIONS = [
  { value: '', label: 'All Years' },
  { value: '1', label: '1st Year (Sem 1 & 2)' },
  { value: '2', label: '2nd Year (Sem 3 & 4)' },
  { value: '3', label: '3rd Year (Sem 5 & 6)' },
  { value: '4', label: '4th Year (Sem 7 & 8)' },
  { value: '5', label: '5th Year (Sem 9 & 10)' },
];

const SEMESTER_OPTIONS = [
  { value: '', label: 'All Semesters' },
  { value: '1', label: 'Semester 1' },
  { value: '2', label: 'Semester 2' },
  { value: '3', label: 'Semester 3' },
  { value: '4', label: 'Semester 4' },
  { value: '5', label: 'Semester 5' },
  { value: '6', label: 'Semester 6' },
  { value: '7', label: 'Semester 7' },
  { value: '8', label: 'Semester 8' },
  { value: '9', label: 'Semester 9 (B.Arch)' },
  { value: '10', label: 'Semester 10 (B.Arch)' },
];

const CREDIT_OPTIONS = [
  { value: '', label: 'All Credits' },
  { value: '1-2', label: '1 – 2 Credits (Labs & Sessional)' },
  { value: '3', label: '3 Credits (Standard Theory)' },
  { value: '4-5', label: '4 – 5 Credits (Advanced Core / Honours)' },
  { value: '6+', label: '6+ Credits (Projects & Dissertation)' },
];

const FACULTY_STATUS_OPTIONS = [
  { value: '', label: 'All Faculty Status' },
  { value: 'assigned', label: '👤 Assigned Faculty' },
  { value: 'unassigned', label: '⚠️ Unassigned Faculty' },
];

const ELECTIVE_OPTIONS = [
  { value: '', label: 'All Courses (Core & Elective)' },
  { value: 'core', label: '🎯 Core Mandatory' },
  { value: 'elective', label: '🔀 Electives / Baskets' },
];

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function SubjectsPage() {
  const [subjects, setSubjects] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [amenitiesList, setAmenitiesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');

  /* Multi-dimensional filters */
  const [degreeFilter, setDegreeFilter] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('');
  const [creditsFilter, setCreditsFilter] = useState('');
  const [facultyFilter, setFacultyFilter] = useState('');
  const [electiveFilter, setElectiveFilter] = useState('');
  const [ordering, setOrdering] = useState('code');

  const [debouncedSearch, setDebouncedSearch] = useState(search);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [viewingItem, setViewingItem] = useState(null);
  const [deptModalCourse, setDeptModalCourse] = useState(null);
  const [deptSearch, setDeptSearch] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  /* Derived departments list for the active course's department modal */
  const modalDeptList = useMemo(() => {
    if (!deptModalCourse) return [];
    const deptIds = deptModalCourse.departments || [];
    let list = [];
    if (deptIds.length > 0) {
      list = deptIds.map((id) => departments.find((d) => d.id === id)).filter(Boolean);
    } else if (deptModalCourse.faculty_department) {
      const match = departments.find((d) => d.name === deptModalCourse.faculty_department);
      if (match) {
        list = [match];
      } else {
        list = [{
          id: 'faculty-dept',
          dept_id: deptModalCourse.faculty_dept_id,
          name: deptModalCourse.faculty_department,
          program_type: getDepartmentDegree(deptModalCourse.faculty_department),
          no_of_years: 4,
        }];
      }
    }
    return list;
  }, [deptModalCourse, departments]);

  const filteredDeptList = useMemo(() => {
    if (!deptSearch.trim()) return modalDeptList;
    const q = deptSearch.toLowerCase().trim();
    return modalDeptList.filter(
      (d) =>
        (d.name && d.name.toLowerCase().includes(q)) ||
        (d.dept_id && d.dept_id.toLowerCase().includes(q)) ||
        (d.program_type && d.program_type.toLowerCase().includes(q))
    );
  }, [modalDeptList, deptSearch]);

  const modalDegreesSummary = useMemo(() => {
    if (!modalDeptList.length) return [];
    const counts = {};
    modalDeptList.forEach((d) => {
      const deg = getDepartmentDegree(d) || 'Other';
      counts[deg] = (counts[deg] || 0) + 1;
    });
    return Object.entries(counts).map(([degree, count]) => ({ degree, count }));
  }, [modalDeptList]);

  /* Debounce search changes to prevent rapid request floods */
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  /* Load reference metadata (departments, faculty, amenities) once on mount */
  useEffect(() => {
    loadMetadata();
  }, []);

  const loadMetadata = async () => {
    try {
      const [depRes, facRes, amRes] = await Promise.allSettled([
        api.get('/api/scheduler/departments/?all=true'),
        api.get('/api/auth/faculty/?all=true'),
        api.get('/api/scheduler/amenities/'),
      ]);

      if (depRes.status === 'fulfilled') {
        setDepartments(depRes.value.data.results || depRes.value.data || []);
      }
      if (facRes.status === 'fulfilled') {
        setFaculty(facRes.value.data.results || facRes.value.data || []);
      }
      if (amRes.status === 'fulfilled') {
        setAmenitiesList(amRes.value.data.results || amRes.value.data || []);
      }
    } catch (err) {
      console.warn('Failed to load auxiliary course metadata:', err);
    }
  };

  /* Fetch courses catalog based on filters and pagination */
  const fetchCourses = async ({
    pageNum = page,
    searchQuery = debouncedSearch,
    degFilter = degreeFilter,
    deptFilter = departmentFilter,
    tFilter = typeFilter,
    yFilter = yearFilter,
    semFilter = semesterFilter,
    cFilter = creditsFilter,
    facFilter = facultyFilter,
    elecFilter = electiveFilter,
    orderingParam = ordering,
  } = {}) => {
    if (pageNum === 1) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }
    try {
      let url = `/api/scheduler/subjects/?page=${pageNum}`;
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
      if (degFilter) url += `&degree=${encodeURIComponent(degFilter)}`;
      if (deptFilter) url += `&department=${deptFilter}`;
      if (tFilter) url += `&subject_type=${tFilter}`;
      if (yFilter) url += `&year=${yFilter}`;
      if (semFilter) url += `&semester=${semFilter}`;
      if (cFilter) url += `&credits=${cFilter}`;
      if (facFilter === 'assigned') url += `&has_faculty=true`;
      if (facFilter === 'unassigned') url += `&has_faculty=false`;
      if (elecFilter === 'core') url += `&is_elective=false`;
      if (elecFilter === 'elective') url += `&is_elective=true`;
      if (orderingParam) url += `&ordering=${orderingParam}`;

      const res = await api.get(url);
      const data = res.data;
      const newResults = data.results || (Array.isArray(data) ? data : []);
      const count =
        data.count !== undefined
          ? data.count
          : Array.isArray(data)
          ? data.length
          : newResults.length;

      if (pageNum === 1) {
        setSubjects(newResults);
      } else {
        setSubjects((prev) => {
          const newIds = new Set(newResults.map((r) => r.id));
          const filteredPrev = prev.filter((r) => !newIds.has(r.id));
          return [...filteredPrev, ...newResults];
        });
      }
      setTotalCount(count);
    } catch (err) {
      console.error('Failed to load data:', err);
      toast.error('Failed to load courses data');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const fetchAll = fetchCourses;

  useEffect(() => {
    fetchCourses({
      pageNum: page,
      searchQuery: debouncedSearch,
      degFilter: degreeFilter,
      deptFilter: departmentFilter,
      tFilter: typeFilter,
      yFilter: yearFilter,
      semFilter: semesterFilter,
      cFilter: creditsFilter,
      facFilter: facultyFilter,
      elecFilter: electiveFilter,
      orderingParam: ordering,
    });
  }, [
    page,
    debouncedSearch,
    degreeFilter,
    departmentFilter,
    typeFilter,
    yearFilter,
    semesterFilter,
    creditsFilter,
    facultyFilter,
    electiveFilter,
    ordering,
  ]);

  /* ── Dynamic Degree Options derived from Loaded Departments ─── */
  const degreeOptions = useMemo(() => {
    const counts = {};
    departments.forEach((d) => {
      const deg = getDepartmentDegree(d);
      if (deg) {
        counts[deg] = (counts[deg] || 0) + 1;
      }
    });

    const sortedDegrees = Object.keys(counts).sort((a, b) => {
      if (counts[b] !== counts[a]) {
        return counts[b] - counts[a];
      }
      return a.localeCompare(b);
    });

    return [
      {
        value: '',
        label: 'All Degrees',
        icon: '🌐',
        color: 'var(--color-accent-blue)',
        count: departments.length,
      },
      ...sortedDegrees.map((deg) => {
        const meta = getDegreeMeta(deg);
        return {
          value: deg,
          label: meta.label || deg,
          icon: meta.icon || '🎓',
          color: meta.color || '#3b82f6',
          count: counts[deg],
        };
      }),
    ];
  }, [departments]);

  /* ── Filter Helpers ───────────────────────────────────────────── */
  const departmentMatchesDegree = (dept, degree) => {
    if (!degree) return true;
    const lower = degree.toLowerCase();
    const dDeg = getDepartmentDegree(dept).toLowerCase();
    const progType = (dept?.program_type || '').toLowerCase();
    const name = (dept?.name || '').toLowerCase();
    return dDeg === lower || progType === lower || name.startsWith(lower) || name.includes(lower);
  };

  const filteredDepartments = useMemo(() => {
    if (!degreeFilter) return departments;
    return departments.filter((d) => departmentMatchesDegree(d, degreeFilter));
  }, [departments, degreeFilter]);

  const handleDegreeChange = (newDegree) => {
    setDegreeFilter(newDegree);
    setPage(1);
    // If current selected department doesn't match new degree, reset it
    if (departmentFilter && newDegree) {
      const currentDept = departments.find(d => String(d.id) === String(departmentFilter));
      if (currentDept && !departmentMatchesDegree(currentDept, newDegree)) {
        setDepartmentFilter('');
      }
    }
  };

  const handleResetFilters = () => {
    setDegreeFilter('');
    setDepartmentFilter('');
    setTypeFilter('');
    setYearFilter('');
    setSemesterFilter('');
    setCreditsFilter('');
    setFacultyFilter('');
    setElectiveFilter('');
    setSearch('');
    setPage(1);
    toast.success('All filters reset');
  };

  const activeFiltersCount = [
    degreeFilter,
    departmentFilter,
    typeFilter,
    yearFilter,
    semesterFilter,
    creditsFilter,
    facultyFilter,
    electiveFilter,
    search,
  ].filter(Boolean).length;

  const getDegreeBadge = (deptNameOrDept) => {
    if (!deptNameOrDept) return null;
    let degCode = '';
    if (typeof deptNameOrDept === 'object') {
      degCode = getDepartmentDegree(deptNameOrDept);
    } else {
      const deptObj = departments.find(d => d.name === deptNameOrDept);
      if (deptObj) {
        degCode = getDepartmentDegree(deptObj);
      } else {
        degCode = getDepartmentDegree(deptNameOrDept);
      }
    }
    if (!degCode) return null;
    const meta = getDegreeMeta(degCode);
    return (
      <span
        style={{
          fontSize: '0.72rem',
          fontWeight: 700,
          padding: '2px 7px',
          borderRadius: '6px',
          background: `${meta.color}18`,
          color: meta.color,
          border: `1px solid ${meta.color}40`,
          marginRight: '6px',
          letterSpacing: '0.02em',
          display: 'inline-block',
        }}
      >
        {degCode}
      </span>
    );
  };

  /* ── CRUD ─────────────────────────────────────────────────────── */
  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingItem?.id) {
        await api.put(`/api/scheduler/subjects/${editingItem.id}/`, formData);
        toast.success('Course updated successfully');
      } else {
        await api.post('/api/scheduler/subjects/', formData);
        toast.success('Course added successfully');
      }
      setModalOpen(false);
      setEditingItem(null);
      fetchAll({ pageNum: page });
    } catch (err) {
      console.error('Save failed:', err);
      toast.error(err.response?.data ? JSON.stringify(err.response.data) : 'Failed to save.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await api.delete(`/api/scheduler/subjects/${confirmDelete.id}/`);
      setConfirmDelete(null);
      toast.success('Course deleted');
      fetchAll({ pageNum: page });
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete. It may be in use.');
    }
  };

  const openAdd = () => {
    setEditingItem(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditingItem(item);
    setModalOpen(true);
  };

  /* ── Table Columns ────────────────────────────────────────────── */
  const columns = [
    {
      key: 'code',
      label: 'Course Code',
      render: (val) => (
        <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
          {val}
        </span>
      ),
    },
    {
      key: 'name',
      label: 'Course Name',
      render: (val, row) => (
        <div style={{ maxWidth: '340px' }}>
          <strong
            style={{ display: 'block', color: 'var(--color-text-primary)', cursor: 'pointer' }}
            onClick={() => setViewingItem(row)}
            title="Click to view course details and syllabus"
          >
            {val}
          </strong>
          {row.is_elective && (
            <div style={{ marginTop: '4px' }}>
              <span
                className="badge"
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  background: 'rgba(139, 92, 246, 0.15)',
                  color: '#a78bfa',
                  border: '1px solid rgba(139, 92, 246, 0.35)',
                  borderRadius: '10px',
                  padding: '1px 7px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <span>⚡ Elective</span>
                {row.elective_group && <span style={{ opacity: 0.85 }}>({row.elective_group})</span>}
              </span>
            </div>
          )}
          {row.description && (
            <span
              title={row.description}
              style={{
                fontSize: '0.8rem',
                color: 'var(--color-text-muted)',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
                lineHeight: 1.35,
                marginTop: '3px',
                cursor: 'pointer',
              }}
              onClick={() => setViewingItem(row)}
            >
              {row.description}
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'semester',
      label: 'Semester',
      sortValue: (row) => Number(row.semester || 1),
      render: (val) => (
        <span
          className="badge"
          style={{
            fontWeight: 700,
            background: val === 2 ? 'rgba(16, 185, 129, 0.12)' : 'rgba(59, 130, 246, 0.12)',
            color: val === 2 ? 'var(--color-accent-emerald)' : 'var(--color-accent-blue)',
            border: `1px solid ${val === 2 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(59, 130, 246, 0.3)'}`,
            padding: '3px 8px',
            borderRadius: '12px',
          }}
        >
          Sem {val || 1}
        </span>
      ),
    },
    {
      key: 'department',
      label: 'Degree & Department / Group',
      sortValue: (row) => row.faculty_department || (departments.find((d) => d.id === row.departments?.[0])?.name || ''),
      render: (_, row) => {
        const deptCount = row.departments?.length || (row.faculty_department ? 1 : 0);

        let previewContent = null;
        if (row.departments && row.departments.length > 0) {
          if (row.departments.length >= 30) {
            previewContent = (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                <span className="badge badge-low" style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  🎓 All B.Tech Branches ({row.departments.length})
                </span>
                <span
                  className="badge badge-primary"
                  style={{ fontSize: '0.72rem', padding: '2px 7px', cursor: 'pointer' }}
                >
                  View All ({row.departments.length}) ↗
                </span>
              </div>
            );
          } else if (row.departments.length === 15 || row.departments.length === 16) {
            const code = row.code || '';
            const isGroupA =
              code.includes('PH101') ||
              code.includes('PH191') ||
              code.includes('ME191') ||
              code.includes('MC-181') ||
              code.includes('CH201') ||
              code.includes('CH291') ||
              code.includes('ME292') ||
              code.includes('MC-282');
            previewContent = (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                <span className="badge badge-low" style={{ fontWeight: 600 }}>
                  👥 {isGroupA ? 'Group A (CSE & Allied)' : 'Group B (Others)'} ({row.departments.length})
                </span>
                <span
                  className="badge badge-primary"
                  style={{ fontSize: '0.72rem', padding: '2px 7px', cursor: 'pointer' }}
                >
                  View All ({row.departments.length}) ↗
                </span>
              </div>
            );
          } else {
            const firstDept = departments.find((d) => d.id === row.departments[0]);
            if (firstDept) {
              previewContent = (
                <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '4px' }}>
                  {getDegreeBadge(firstDept.name)}
                  {firstDept.dept_id && (
                    <span className="badge badge-low" style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      {firstDept.dept_id}
                    </span>
                  )}
                  <span style={{ fontWeight: 500 }}>{firstDept.name}</span>
                  {row.departments.length > 1 ? (
                    <span
                      className="badge badge-primary"
                      style={{ fontSize: '0.72rem', padding: '2px 7px', cursor: 'pointer' }}
                      title={`Click to view all ${row.departments.length} departments`}
                    >
                      +{row.departments.length - 1} more ↗
                    </span>
                  ) : (
                    <span
                      className="badge badge-low"
                      style={{ fontSize: '0.7rem', opacity: 0.8, padding: '1px 6px', cursor: 'pointer' }}
                      title="View department details"
                    >
                      View ↗
                    </span>
                  )}
                </div>
              );
            }
          }
        } else if (row.faculty_department) {
          previewContent = (
            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '4px' }}>
              {getDegreeBadge(row.faculty_department)}
              {row.faculty_dept_id && (
                <span className="badge badge-low" style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {row.faculty_dept_id}
                </span>
              )}
              <span style={{ fontWeight: 500 }}>{row.faculty_department}</span>
              <span
                className="badge badge-low"
                style={{ fontSize: '0.7rem', opacity: 0.8, padding: '1px 6px', cursor: 'pointer' }}
                title="View department details"
              >
                View ↗
              </span>
            </div>
          );
        } else {
          previewContent = (
            <span style={{ color: 'var(--color-text-muted)' }}>
              General Elective ↗
            </span>
          );
        }

        return (
          <div
            onClick={(e) => {
              e.stopPropagation();
              setDeptModalCourse(row);
            }}
            className="dept-cell-clickable"
            style={{
              cursor: 'pointer',
              padding: '6px 10px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'inline-block',
              maxWidth: '100%',
            }}
            title={`Click to view all departments for ${row.code} (${deptCount} total)`}
          >
            {previewContent}
          </div>
        );
      },
    },
    {
      key: 'faculty_name',
      label: 'Faculty',
      sortValue: (row) => row.faculty_name || '',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600, color: val ? 'var(--color-text-primary)' : 'var(--color-accent-orange)' }}>
            {val || '⚠️ Unassigned'}
          </div>
          {row.faculty_employee_id && (
            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
              {row.faculty_employee_id}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'subject_type',
      label: 'Type',
      render: (val) => {
        if (val === 'lab') return <span className="badge badge-present">🧪 Lab</span>;
        if (val === 'seminar') return <span className="badge badge-high">🎙️ Seminar</span>;
        return <span className="badge badge-low">📖 Lecture</span>;
      },
    },
    {
      key: 'credits',
      label: 'Credits',
      sortValue: (row) => Number(row.credits || 0),
      render: (val) => <span className="badge badge-low">{val} Credits</span>,
    },
    {
      key: 'sessions_per_week',
      label: 'Sessions/Week',
      sortValue: (row) => Number(row.sessions_per_week || 0),
      render: (val) => <span className="badge badge-medium">{val} / wk</span>,
    },
    {
      key: 'required_capacity',
      label: 'Capacity',
      sortValue: (row) => Number(row.required_capacity || 0),
      render: (val) => <span className="badge badge-medium">Cap: {val}</span>,
    },
    {
      key: 'amenities',
      label: 'Req. Amenities',
      sortable: false,
      render: (val) => {
        if (!val || val.length === 0) return <span className="badge badge-low">None</span>;
        return (
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {val.map((id) => {
              const am = amenitiesList.find((a) => a.id === id);
              return (
                <span key={id} className="badge badge-medium">
                  {am ? am.name : id}
                </span>
              );
            })}
          </div>
        );
      },
    },
    {
      key: 'actions',
      label: 'Actions',
      sortable: false,
      render: (_, row) => (
        <div className="action-btns" style={{ display: 'flex', gap: '4px' }}>
          <button
            className="btn btn-sm btn-secondary"
            onClick={(e) => {
              e.stopPropagation();
              setViewingItem(row);
            }}
            title="View Course Syllabus & Description"
          >
            Info
          </button>
          <button
            className="btn btn-sm btn-secondary"
            onClick={(e) => {
              e.stopPropagation();
              openEdit(row);
            }}
          >
            Edit
          </button>
          <button
            className="btn btn-sm btn-danger"
            onClick={(e) => {
              e.stopPropagation();
              setConfirmDelete(row);
            }}
          >
            Delete
          </button>
        </div>
      ),
    },
  ];

  const totalPages = Math.ceil(totalCount / 100) || 1;

  if (loading && subjects.length === 0) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Page Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span>Courses & Curriculum</span>
          </h1>
          <p>
            Browse, search, and manage all academic syllabus courses across MAKAUT departments with multi-criteria filtering.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {activeFiltersCount > 0 && (
            <button className="btn btn-secondary" onClick={handleResetFilters}>
              Clear Filters ({activeFiltersCount})
            </button>
          )}
          <button className="btn btn-primary" id="btn-add-course" onClick={openAdd}>
            + Add Course
          </button>
        </div>
      </div>

      {/* Quick Summary Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)', fontSize: '1.3rem' }}>
            📖
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{totalCount}</h3>
            <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
              {activeFiltersCount > 0 ? 'Filtered Courses' : 'Total Course Catalog'}
            </span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)', fontSize: '1.3rem' }}>
            🎓
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>
              {degreeFilter ? degreeFilter : `${degreeOptions.length > 1 ? degreeOptions.length - 1 : 0} Degrees`}
            </h3>
            <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
              {degreeFilter ? `${filteredDepartments.length} Departments in ${degreeFilter}` : `All ${departments.length} University Depts`}
            </span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(139, 92, 246, 0.1)', color: 'var(--color-accent-purple)', fontSize: '1.3rem' }}>
            👥
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{faculty.length}</h3>
            <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>Assigned Faculty</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: 'var(--color-accent-orange)', fontSize: '1.3rem' }}>
            📜
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>
              {subjects.length} / {totalCount}
            </h3>
            <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
              Courses Loaded (Scroll for more)
            </span>
          </div>
        </div>
      </div>

      {/* Modern Filter Panel */}
      <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        {/* Row 1: Quick Degree Pills (Horizontal Segmented Control) */}
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Filter by Degree Program
            </span>
            {degreeFilter && (
              <button
                className="btn btn-sm btn-secondary"
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}
                onClick={() => handleDegreeChange('')}
              >
                Reset Degree (Show All)
              </button>
            )}
          </div>
          <div
            style={{
              display: 'flex',
              gap: '0.4rem',
              overflowX: 'auto',
              paddingBottom: '0.35rem',
              scrollbarWidth: 'thin',
            }}
          >
            {degreeOptions.map((deg) => {
              const isSelected = degreeFilter === deg.value;
              return (
                <button
                  key={deg.value || 'all'}
                  type="button"
                  className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    whiteSpace: 'nowrap',
                    padding: '0.35rem 0.75rem',
                    fontSize: '0.82rem',
                    fontWeight: isSelected ? 700 : 500,
                    borderColor: isSelected ? deg.color : undefined,
                    boxShadow: isSelected ? `0 0 12px ${deg.color}40` : undefined,
                  }}
                  onClick={() => handleDegreeChange(deg.value)}
                >
                  <span>{deg.icon}</span>
                  <span>{deg.value || 'All Degrees'}</span>
                  {deg.count !== undefined && (
                    <span
                      style={{
                        fontSize: '0.7rem',
                        opacity: 0.8,
                        background: 'rgba(255,255,255,0.12)',
                        padding: '1px 5px',
                        borderRadius: '10px',
                      }}
                    >
                      {deg.count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Row 2: Detailed Filters Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '0.75rem',
            alignItems: 'center',
            paddingTop: '0.75rem',
            borderTop: '1px solid var(--color-border)',
          }}
        >
          {/* Degree Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              Degree
            </label>
            <select
              className="form-input"
              style={{ width: '100%', padding: '0.45rem 0.7rem', fontSize: '0.85rem' }}
              value={degreeFilter}
              onChange={(e) => handleDegreeChange(e.target.value)}
            >
              {degreeOptions.map((d) => (
                <option key={d.value || 'all'} value={d.value}>
                  {d.icon} {d.label} {d.count !== undefined ? `(${d.count})` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Department Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              Department {degreeFilter ? `(${filteredDepartments.length} in ${degreeFilter})` : `(All ${departments.length})`}
            </label>
            <select
              className="form-input"
              style={{ width: '100%', padding: '0.45rem 0.7rem', fontSize: '0.85rem' }}
              value={departmentFilter}
              onChange={(e) => {
                setPage(1);
                setDepartmentFilter(e.target.value);
              }}
            >
              <option value="">-- All Departments --</option>
              {degreeFilter ? (
                filteredDepartments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.dept_id ? `[${d.dept_id}] ` : ''}
                    {d.name}
                  </option>
                ))
              ) : (
                <>
                  {degreeOptions.filter((deg) => deg.value).map((deg) => {
                    const deptsInDeg = departments.filter((d) => {
                      const dDeg = getDepartmentDegree(d);
                      return dDeg.toLowerCase() === deg.value.toLowerCase();
                    });
                    if (deptsInDeg.length === 0) return null;
                    return (
                      <optgroup key={deg.value} label={`${deg.icon} ${deg.value} (${deptsInDeg.length})`}>
                        {deptsInDeg.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.dept_id ? `[${d.dept_id}] ` : ''}
                            {d.name}
                          </option>
                        ))}
                      </optgroup>
                    );
                  })}
                </>
              )}
            </select>
          </div>

          {/* Academic Year */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              Academic Year
            </label>
            <select
              className="form-input"
              style={{ width: '100%', padding: '0.45rem 0.7rem', fontSize: '0.85rem' }}
              value={yearFilter}
              onChange={(e) => {
                setPage(1);
                setYearFilter(e.target.value);
              }}
            >
              {YEAR_OPTIONS.map((y) => (
                <option key={y.value} value={y.value}>
                  {y.label}
                </option>
              ))}
            </select>
          </div>

          {/* Semester Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              Semester
            </label>
            <select
              className="form-input"
              style={{ width: '100%', padding: '0.45rem 0.7rem', fontSize: '0.85rem' }}
              value={semesterFilter}
              onChange={(e) => {
                setPage(1);
                setSemesterFilter(e.target.value);
              }}
            >
              {SEMESTER_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Course Type */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              Course Type
            </label>
            <select
              className="form-input"
              style={{ width: '100%', padding: '0.45rem 0.7rem', fontSize: '0.85rem' }}
              value={typeFilter}
              onChange={(e) => {
                setPage(1);
                setTypeFilter(e.target.value);
              }}
            >
              <option value="">All Types (Lectures, Labs, Seminars)</option>
              <option value="lecture">📖 Lectures (Theory)</option>
              <option value="lab">🧪 Laboratories (Practical)</option>
              <option value="seminar">🎙️ Seminars / Projects</option>
            </select>
          </div>

          {/* Credits Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              Credits
            </label>
            <select
              className="form-input"
              style={{ width: '100%', padding: '0.45rem 0.7rem', fontSize: '0.85rem' }}
              value={creditsFilter}
              onChange={(e) => {
                setPage(1);
                setCreditsFilter(e.target.value);
              }}
            >
              {CREDIT_OPTIONS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Faculty Assignment Status */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              Faculty Assignment
            </label>
            <select
              className="form-input"
              style={{ width: '100%', padding: '0.45rem 0.7rem', fontSize: '0.85rem' }}
              value={facultyFilter}
              onChange={(e) => {
                setPage(1);
                setFacultyFilter(e.target.value);
              }}
            >
              {FACULTY_STATUS_OPTIONS.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>

          {/* Core vs Elective */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              Curriculum Nature
            </label>
            <select
              className="form-input"
              style={{ width: '100%', padding: '0.45rem 0.7rem', fontSize: '0.85rem' }}
              value={electiveFilter}
              onChange={(e) => {
                setPage(1);
                setElectiveFilter(e.target.value);
              }}
            >
              {ELECTIVE_OPTIONS.map((el) => (
                <option key={el.value} value={el.value}>
                  {el.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Row 3: Active Filters Tags Bar */}
        {activeFiltersCount > 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '0.4rem',
              marginTop: '1rem',
              paddingTop: '0.75rem',
              borderTop: '1px solid var(--color-border)',
            }}
          >
            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', fontWeight: 600, marginRight: '0.3rem' }}>
              Active Filters:
            </span>

            {degreeFilter && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                🎓 Degree: {degreeFilter}
                <button
                  type="button"
                  onClick={() => handleDegreeChange('')}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            {departmentFilter && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                🏛️ Dept: {departments.find((d) => String(d.id) === String(departmentFilter))?.name || departmentFilter}
                <button
                  type="button"
                  onClick={() => { setPage(1); setDepartmentFilter(''); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            {typeFilter && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                📖 Type: {typeFilter}
                <button
                  type="button"
                  onClick={() => { setPage(1); setTypeFilter(''); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            {yearFilter && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                📅 Year: {yearFilter}
                <button
                  type="button"
                  onClick={() => { setPage(1); setYearFilter(''); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            {semesterFilter && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                📘 Sem: {semesterFilter}
                <button
                  type="button"
                  onClick={() => { setPage(1); setSemesterFilter(''); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            {creditsFilter && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                ⚡ Credits: {creditsFilter}
                <button
                  type="button"
                  onClick={() => { setPage(1); setCreditsFilter(''); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            {facultyFilter && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                👤 Faculty: {facultyFilter}
                <button
                  type="button"
                  onClick={() => { setPage(1); setFacultyFilter(''); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            {electiveFilter && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                🎯 Nature: {electiveFilter}
                <button
                  type="button"
                  onClick={() => { setPage(1); setElectiveFilter(''); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            {search && (
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                🔍 Search: &quot;{search}&quot;
                <button
                  type="button"
                  onClick={() => { setPage(1); setSearch(''); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            )}

            <button
              className="btn btn-sm btn-secondary"
              onClick={handleResetFilters}
              style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem', marginLeft: 'auto' }}
            >
              Clear All Filters
            </button>
          </div>
        )}
      </div>

      {/* Main Table Card */}
      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)' }}>
              📖
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', margin: 0, fontWeight: 700 }}>
                {degreeFilter ? `${degreeFilter} Courses` : 'All Courses'}
              </h3>
              <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                Showing {subjects.length} of {totalCount} courses (infinite scroll enabled)
              </span>
            </div>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={subjects}
          loading={loading || loadingMore}
          infiniteScroll={true}
          totalCount={totalCount}
          serverPage={page}
          pageSize={100}
          onPageChange={setPage}
          searchValue={search}
          onSearchChange={(val) => {
            setSearch(val);
            setPage(1);
          }}
          defaultSortKey="code"
          defaultSortDir="asc"
          onSortChange={({ sortKey, sortDir }) => {
            const backendSortMap = {
              code: 'code',
              name: 'name',
              semester: 'semester',
              credits: 'credits',
              required_capacity: 'required_capacity',
              sessions_per_week: 'sessions_per_week',
              subject_type: 'subject_type',
              department: 'department',
              faculty_name: 'faculty_name',
            };
            const field = backendSortMap[sortKey];
            if (field) {
              setOrdering(sortDir === 'desc' ? `-${field}` : field);
              setPage(1);
            }
          }}
          emptyMessage="No courses matching your filter criteria. Try broadening your filter selection."
        />
      </div>

      {/* Add/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditingItem(null);
        }}
        title={editingItem?.id ? 'Edit Course' : 'Add Course'}
      >
        <CourseForm
          initial={editingItem}
          faculty={faculty}
          departments={departments}
          amenitiesList={amenitiesList}
          onSave={handleSave}
          saving={saving}
        />
      </Modal>

      {/* Course Details Modal */}
      <Modal
        open={!!viewingItem}
        onClose={() => setViewingItem(null)}
        title={viewingItem ? `[${viewingItem.code}] ${viewingItem.name}` : 'Course Details'}
        maxWidth="680px"
      >
        {viewingItem && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
              <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                {viewingItem.code}
              </span>
              <span className="badge" style={{ background: 'rgba(59,130,246,0.12)', color: 'var(--color-accent-blue)' }}>
                Semester {viewingItem.semester}
              </span>
              <span className="badge badge-low">
                {viewingItem.credits} Credits
              </span>
              <span className="badge badge-low" style={{ textTransform: 'capitalize' }}>
                {viewingItem.subject_type === 'lab' ? '🔬 Laboratory' : viewingItem.subject_type === 'seminar' ? '🗣️ Seminar' : '📖 Lecture'}
              </span>
              <span className="badge badge-medium">
                {viewingItem.sessions_per_week || 3} sessions / wk
              </span>
              {viewingItem.is_elective && (
                <span
                  className="badge"
                  style={{
                    background: 'rgba(139, 92, 246, 0.15)',
                    color: '#a78bfa',
                    border: '1px solid rgba(139, 92, 246, 0.35)',
                  }}
                >
                  ⚡ Elective: {viewingItem.elective_group || 'General Elective'}
                </span>
              )}
            </div>

            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Official Syllabus Description & Scope
              </h4>
              <div
                style={{
                  background: 'var(--color-bg-input)',
                  padding: '1rem',
                  borderRadius: '8px',
                  border: '1px solid var(--color-border)',
                  lineHeight: 1.6,
                  color: 'var(--color-text-primary)',
                  fontSize: '0.92rem',
                }}
              >
                {viewingItem.description || 'No description available for this course.'}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.3rem' }}>
                  Assigned Faculty
                </h4>
                <div style={{ fontWeight: 500 }}>
                  {viewingItem.faculty_name ? (
                    <>
                      <span>{viewingItem.faculty_name}</span>
                      {viewingItem.faculty_employee_id && (
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginLeft: '0.4rem' }}>
                          ({viewingItem.faculty_employee_id})
                        </span>
                      )}
                    </>
                  ) : (
                    <span style={{ color: 'var(--color-accent-orange)' }}>⚠️ Unassigned</span>
                  )}
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.3rem' }}>
                  Target Capacity
                </h4>
                <div>{viewingItem.required_capacity || 30} students</div>
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Associated Academic Programs ({viewingItem.departments?.length || (viewingItem.faculty_department ? 1 : 0)})
                </h4>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => {
                    const item = viewingItem;
                    setViewingItem(null);
                    setDeptModalCourse(item);
                  }}
                  style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}
                >
                  🏛️ View Full Department List ↗
                </button>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', maxHeight: '120px', overflowY: 'auto' }}>
                {viewingItem.departments && viewingItem.departments.length > 0 ? (
                  viewingItem.departments.map((dId) => {
                    const dept = departments.find((d) => d.id === dId);
                    return (
                      <span
                        key={dId}
                        className="badge badge-low"
                        style={{ fontSize: '0.8rem', cursor: 'pointer' }}
                        onClick={() => {
                          const item = viewingItem;
                          setViewingItem(null);
                          setDeptModalCourse(item);
                        }}
                        title="Click to view all associated departments"
                      >
                        {dept ? (dept.dept_id ? `[${dept.dept_id}] ${dept.name}` : dept.name) : `Dept #${dId}`}
                      </span>
                    );
                  })
                ) : viewingItem.faculty_department ? (
                  <span className="badge badge-low">{viewingItem.faculty_department}</span>
                ) : (
                  <span style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>General Campus Elective</span>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  const item = viewingItem;
                  setViewingItem(null);
                  openEdit(item);
                }}
              >
                ✏️ Edit Course
              </button>
              <button className="btn btn-primary" onClick={() => setViewingItem(null)}>
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Associated Degrees & Academic Departments Modal */}
      <Modal
        open={!!deptModalCourse}
        onClose={() => {
          setDeptModalCourse(null);
          setDeptSearch('');
        }}
        title="Associated Academic Degrees & Departments"
        maxWidth="780px"
      >
        {deptModalCourse && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Course Summary Banner */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--color-border)',
                borderRadius: '10px',
                padding: '1rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap', marginBottom: '0.35rem' }}>
                  <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '0.85rem' }}>
                    {deptModalCourse.code}
                  </span>
                  <span
                    className="badge"
                    style={{
                      background: 'rgba(59, 130, 246, 0.12)',
                      color: 'var(--color-accent-blue)',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      fontWeight: 600,
                    }}
                  >
                    Semester {deptModalCourse.semester}
                  </span>
                  <span className="badge badge-low">
                    {deptModalCourse.credits} Credits
                  </span>
                  <span className="badge badge-low" style={{ textTransform: 'capitalize' }}>
                    {deptModalCourse.subject_type === 'lab'
                      ? '🧪 Lab'
                      : deptModalCourse.subject_type === 'seminar'
                      ? '🎙️ Seminar'
                      : '📖 Lecture'}
                  </span>
                </div>
                <h3 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>
                  {deptModalCourse.name}
                </h3>
              </div>
              <div style={{ textAlign: 'right', minWidth: '110px' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-primary)' }}>
                  {modalDeptList.length}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  {modalDeptList.length === 1 ? 'Department Offering' : 'Departments Offering'}
                </div>
              </div>
            </div>

            {/* Degree Breakdown Chips */}
            {modalDegreesSummary.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
                  Degrees:
                </span>
                {modalDegreesSummary.map(({ degree, count }) => {
                  const meta = getDegreeMeta(degree);
                  return (
                    <span
                      key={degree}
                      className="badge"
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        background: `${meta.color}18`,
                        color: meta.color,
                        border: `1px solid ${meta.color}40`,
                      }}
                    >
                      {meta?.icon || '🎓'} {degree} ({count})
                    </span>
                  );
                })}
              </div>
            )}

            {/* Quick Search */}
            {modalDeptList.length > 3 && (
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Filter departments by name, code (DEP-XXXX), or degree..."
                  value={deptSearch}
                  onChange={(e) => setDeptSearch(e.target.value)}
                  style={{ flex: 1, padding: '0.45rem 0.8rem', fontSize: '0.85rem' }}
                />
                {deptSearch && (
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setDeptSearch('')}
                    style={{ fontSize: '0.78rem', padding: '0.45rem 0.75rem' }}
                  >
                    Clear
                  </button>
                )}
              </div>
            )}

            {/* Department List Grid */}
            {filteredDeptList.length > 0 ? (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                  gap: '0.65rem',
                  maxHeight: '380px',
                  overflowY: 'auto',
                  paddingRight: '4px',
                }}
              >
                {filteredDeptList.map((dept) => (
                  <div
                    key={dept.id}
                    style={{
                      background: 'var(--color-bg-input)',
                      border: '1px solid var(--color-border)',
                      borderRadius: '8px',
                      padding: '0.75rem 0.9rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.35rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        {getDegreeBadge(dept.name)}
                        {dept.dept_id && (
                          <span className="badge badge-low" style={{ fontFamily: 'monospace', fontSize: '0.72rem', fontWeight: 600 }}>
                            {dept.dept_id}
                          </span>
                        )}
                      </div>
                      <span className="badge badge-low" style={{ fontSize: '0.68rem' }}>
                        {dept.program_type || 'UG'} • {dept.no_of_years || 4}Y
                      </span>
                    </div>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '0.88rem' }}>
                      {dept.name}
                    </div>
                    {deptModalCourse.faculty_department === dept.name && (
                      <div style={{ fontSize: '0.72rem', color: 'var(--color-accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>👤 Assigned Faculty Home Dept</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : modalDeptList.length === 0 ? (
              <div className="empty-state" style={{ padding: '2rem 1rem' }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🌐</div>
                <h4 style={{ margin: '0 0 0.5rem 0' }}>University-Wide Course Offering</h4>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', margin: 0 }}>
                  This course is open across university departments without restriction to a single branch.
                </p>
              </div>
            ) : (
              <div className="empty-state" style={{ padding: '2rem 1rem' }}>
                <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>🔍</div>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', margin: 0 }}>
                  No departments matching &quot;{deptSearch}&quot;.
                </p>
              </div>
            )}

            {/* Modal Actions */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingTop: '0.75rem',
                borderTop: '1px solid var(--color-border)',
                marginTop: '0.25rem',
              }}
            >
              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                Showing {filteredDeptList.length} of {modalDeptList.length} departments
              </span>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setDeptModalCourse(null);
                  setDeptSearch('');
                }}
              >
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Confirm delete */}
      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        message="Are you sure you want to delete this course? This action cannot be undone."
      />
    </div>
  );
}
