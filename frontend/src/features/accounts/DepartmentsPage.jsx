import toast from 'react-hot-toast';
import { useState, useEffect, useMemo } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';

/* ─── Modal component ─────────────────────────────────────── */
function Modal({ open, onClose, title, children, maxWidth = '560px' }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1100 }}>
      <div
        className="modal-content glass-card"
        style={{ maxWidth, width: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div style={{ overflowY: 'auto', flex: 1, paddingRight: '0.25rem' }}>
          {children}
        </div>
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

/* ─── Add Department Form ───────────────────────────────────────────── */
function DepartmentForm({ initialData, onSave, saving, faculties, availablePrograms = [] }) {
  const [form, setForm] = useState({
    dept_id: initialData?.dept_id || '',
    program_type: initialData?.program_type || '',
    core_department: initialData?.core_department || '',
    no_of_years: initialData?.no_of_years || 4,
    hod: initialData?.hod || '',
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (!initialData) {
      api.get('/scheduler/departments/next-id/')
        .then(res => {
          if (res.data?.next_id) {
            setForm(prev => ({ ...prev, dept_id: prev.dept_id || res.data.next_id }));
          }
        })
        .catch(err => console.error('Error fetching next department ID', err));
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.core_department) {
      setError('Please provide a core department name.');
      return;
    }
    const submitData = { ...form };
    if (!submitData.hod) {
      submitData.hod = null;
    }
    if (!submitData.dept_id) {
      delete submitData.dept_id;
    }
    
    // Maintain the unique 'name' field for backward compatibility
    submitData.name = submitData.program_type 
      ? `${submitData.program_type} in ${submitData.core_department}`
      : submitData.core_department;
      
    onSave(submitData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div style={{
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          borderRadius: '0.5rem',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#ef4444',
          fontSize: '0.85rem',
        }}>
          {error}
        </div>
      )}
      <div className="form-group">
        <label className="form-label">
          Department ID {!initialData && <span style={{ fontSize: '0.8rem', color: 'var(--color-primary)' }}>(Auto-generated)</span>}
        </label>
        <input
          className="form-input"
          name="dept_id"
          value={form.dept_id}
          onChange={handleChange}
          placeholder="e.g. DEP-0001"
        />
      </div>
      <div className="form-group">
        <label className="form-label">Degree / Program Type</label>
        <input
          className="form-input"
          name="program_type"
          value={form.program_type}
          onChange={handleChange}
          placeholder="e.g. B.Tech, B.Sc, BBA (select or type)"
          list="dept-program-types-list"
          autoComplete="off"
        />
        <datalist id="dept-program-types-list">
          {availablePrograms.map(p => {
            const val = typeof p === 'string' ? p : p.program_type;
            return <option key={val} value={val} />;
          })}
        </datalist>
      </div>
      <div className="form-group">
        <label className="form-label">Department Discipline *</label>
        <input
          className="form-input"
          name="core_department"
          value={form.core_department}
          onChange={handleChange}
          placeholder="e.g. Civil, Mechanical, Computer Science"
          required
        />
      </div>
      <div className="form-group">
        <label className="form-label">Program Years</label>
        <input
          type="number"
          className="form-input"
          name="no_of_years"
          value={form.no_of_years}
          onChange={handleChange}
          min="1"
          required
        />
      </div>
      <div className="form-group">
        <label className="form-label">Head of Department</label>
        <select
          className="form-input"
          name="hod"
          value={form.hod || ''}
          onChange={handleChange}
          disabled={!initialData || !faculties?.some(f => f.department === initialData.id)}
        >
          <option value="">
            {!initialData 
              ? "-- Save department first to add HOD --" 
              : !faculties?.some(f => f.department === initialData.id)
                ? "-- No faculty in this department --"
                : "-- Select HOD (Optional) --"}
          </option>
          {faculties
            ?.filter(f => initialData ? f.department === initialData.id : false)
            .map(f => (
            <option key={f.id} value={f.id}>
              {f.user?.first_name} {f.user?.last_name} ({f.employee_id})
            </option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : (initialData ? 'Save Changes' : 'Add Department')}
      </button>
    </form>
  );
}

/* ─── Department Details Modal (Faculty, Students, Courses) ─────── */
function DepartmentDetailsModal({ department, faculties = [], initialTab = 'faculty', onClose }) {
  const [activeTab, setActiveTab] = useState(initialTab || 'faculty');
  const [loading, setLoading] = useState(true);
  const [facultyList, setFacultyList] = useState([]);
  const [studentsList, setStudentsList] = useState([]);
  const [coursesList, setCoursesList] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (!department) return;
    setActiveTab(initialTab || 'faculty');
    setSearchTerm('');
    fetchDetails();
  }, [department, initialTab]);

  const fetchDetails = async () => {
    if (!department?.id) return;
    setLoading(true);
    try {
      const [facRes, studRes, courseRes] = await Promise.all([
        api.get(`/api/auth/faculty/?department=${department.id}&all=true`),
        api.get(`/api/auth/students/?department=${department.id}&all=true`),
        api.get(`/api/scheduler/subjects/?department=${department.id}&all=true`),
      ]);
      setFacultyList(facRes.data.results || facRes.data || []);
      setStudentsList(studRes.data.results || studRes.data || []);
      setCoursesList(courseRes.data.results || courseRes.data || []);
    } catch (err) {
      console.error('Failed to load department details:', err);
      toast.error('Failed to load department details');
    } finally {
      setLoading(false);
    }
  };

  const hod = faculties.find((f) => f.id === department?.hod);
  const q = searchTerm.toLowerCase().trim();

  const filteredFaculty = useMemo(() => {
    if (!q) return facultyList;
    return facultyList.filter(
      (f) =>
        `${f.user?.first_name || ''} ${f.user?.last_name || ''}`.toLowerCase().includes(q) ||
        (f.employee_id && f.employee_id.toLowerCase().includes(q)) ||
        (f.user?.email && f.user.email.toLowerCase().includes(q)) ||
        (f.designation && f.designation.toLowerCase().includes(q))
    );
  }, [facultyList, q]);

  const filteredStudents = useMemo(() => {
    if (!q) return studentsList;
    return studentsList.filter(
      (s) =>
        `${s.user?.first_name || ''} ${s.user?.last_name || ''}`.toLowerCase().includes(q) ||
        (s.enrollment_number && s.enrollment_number.toLowerCase().includes(q)) ||
        (s.user?.email && s.user.email.toLowerCase().includes(q))
    );
  }, [studentsList, q]);

  const filteredCourses = useMemo(() => {
    if (!q) return coursesList;
    return coursesList.filter(
      (c) =>
        (c.code && c.code.toLowerCase().includes(q)) ||
        (c.name && c.name.toLowerCase().includes(q)) ||
        (c.description && c.description.toLowerCase().includes(q)) ||
        (c.faculty_name && c.faculty_name.toLowerCase().includes(q))
    );
  }, [coursesList, q]);

  if (!department) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', minHeight: '380px' }}>
      {/* Department Summary Header Card */}
      <div
        style={{
          background: 'var(--color-bg-secondary)',
          borderRadius: 'var(--radius-md)',
          padding: '0.9rem 1.1rem',
          border: '1px solid var(--color-border)',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {department.dept_id && (
            <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.8rem' }}>
              {department.dept_id}
            </span>
          )}
          {department.program_type && (
            <span
              className="badge"
              style={{
                backgroundColor: 'var(--color-primary-light)',
                color: 'var(--color-primary-dark)',
                fontWeight: 600,
                fontSize: '0.8rem',
              }}
            >
              {department.program_type}
            </span>
          )}
          <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
            Program: <strong>{department.no_of_years || 4} Years</strong>
          </span>
          {hod && (
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
              • HOD: <strong>{hod.user?.first_name} {hod.user?.last_name}</strong>
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <span className="badge" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)', fontWeight: 600 }}>
            👥 {facultyList.length} Faculty
          </span>
          <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)', fontWeight: 600 }}>
            👨‍🎓 {studentsList.length} Students
          </span>
          <span className="badge" style={{ backgroundColor: 'rgba(99, 102, 241, 0.12)', color: '#6366f1', fontWeight: 600 }}>
            📚 {coursesList.length} Courses
          </span>
        </div>
      </div>

      {/* Tabs & Search Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '0.75rem',
          flexWrap: 'wrap',
          borderBottom: '1px solid var(--color-border)',
          paddingBottom: '0.75rem',
        }}
      >
        <div className="tabs" style={{ display: 'flex', gap: '0.4rem', margin: 0 }}>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'faculty' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: activeTab === 'faculty' ? 700 : 500 }}
            onClick={() => setActiveTab('faculty')}
          >
            <span>👥 Faculty</span>
            <span
              className="badge"
              style={{
                fontSize: '0.7rem',
                padding: '0.1rem 0.4rem',
                backgroundColor: activeTab === 'faculty' ? 'rgba(255,255,255,0.25)' : 'var(--color-bg-tertiary)',
                color: 'inherit',
              }}
            >
              {facultyList.length}
            </span>
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'students' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: activeTab === 'students' ? 700 : 500 }}
            onClick={() => setActiveTab('students')}
          >
            <span>👨‍🎓 Students</span>
            <span
              className="badge"
              style={{
                fontSize: '0.7rem',
                padding: '0.1rem 0.4rem',
                backgroundColor: activeTab === 'students' ? 'rgba(255,255,255,0.25)' : 'var(--color-bg-tertiary)',
                color: 'inherit',
              }}
            >
              {studentsList.length}
            </span>
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'courses' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: activeTab === 'courses' ? 700 : 500 }}
            onClick={() => setActiveTab('courses')}
          >
            <span>📚 Courses</span>
            <span
              className="badge"
              style={{
                fontSize: '0.7rem',
                padding: '0.1rem 0.4rem',
                backgroundColor: activeTab === 'courses' ? 'rgba(255,255,255,0.25)' : 'var(--color-bg-tertiary)',
                color: 'inherit',
              }}
            >
              {coursesList.length}
            </span>
          </button>
        </div>

        <div style={{ flex: '1 1 200px', maxWidth: '300px' }}>
          <input
            className="form-input"
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.85rem', width: '100%' }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={`Filter ${activeTab}...`}
          />
        </div>
      </div>

      {/* Main Tab Content */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '220px', gap: '0.75rem' }}>
          <div className="spinner" />
          <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Loading department data...</span>
        </div>
      ) : activeTab === 'faculty' ? (
        filteredFaculty.length === 0 ? (
          <div className="empty-state" style={{ padding: '2.5rem 1rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>👥</div>
            <h4 style={{ margin: '0 0 0.5rem 0' }}>No Faculty Members Found</h4>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', margin: 0 }}>
              {searchTerm ? `No faculty matching "${searchTerm}".` : 'No faculty members are currently assigned to this department.'}
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '0.75rem' }}>
            {filteredFaculty.map((f) => {
              const isHead = department.hod === f.id;
              return (
                <div
                  key={f.id}
                  style={{
                    background: 'var(--color-bg-secondary)',
                    border: isHead ? '1px solid var(--color-primary)' : '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.85rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.4rem',
                    boxShadow: isHead ? '0 0 10px rgba(99, 102, 241, 0.15)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                    <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.75rem' }}>
                      {f.employee_id || 'ID N/A'}
                    </span>
                    {isHead && (
                      <span className="badge badge-high" style={{ fontSize: '0.7rem', fontWeight: 700 }}>
                        👑 HOD
                      </span>
                    )}
                  </div>
                  <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '0.95rem' }}>
                    {f.user?.first_name} {f.user?.last_name}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                    📧 {f.user?.email || 'No email registered'}
                  </div>
                  <div
                    style={{
                      fontSize: '0.8rem',
                      color: 'var(--color-text-secondary)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginTop: '0.25rem',
                      paddingTop: '0.35rem',
                      borderTop: '1px solid rgba(255,255,255,0.06)',
                    }}
                  >
                    <span>{f.designation || 'Faculty'}</span>
                    {f.max_hours_per_week && <span>⏳ {f.max_hours_per_week} hrs/wk</span>}
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : activeTab === 'students' ? (
        filteredStudents.length === 0 ? (
          <div className="empty-state" style={{ padding: '2.5rem 1rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>👨‍🎓</div>
            <h4 style={{ margin: '0 0 0.5rem 0' }}>No Students Found</h4>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', margin: 0 }}>
              {searchTerm ? `No students matching "${searchTerm}".` : 'No students are currently enrolled in this department.'}
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '0.75rem' }}>
            {filteredStudents.map((s) => (
              <div
                key={s.id}
                style={{
                  background: 'var(--color-bg-secondary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                  <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.75rem' }}>
                    {s.enrollment_number}
                  </span>
                  <span className="badge badge-medium" style={{ fontSize: '0.72rem' }}>
                    Sem {s.semester || 1}
                  </span>
                </div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '0.95rem' }}>
                  {s.user?.first_name} {s.user?.last_name}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  📧 {s.user?.email || 'No email registered'}
                </div>
                <div
                  style={{
                    fontSize: '0.78rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginTop: '0.25rem',
                    paddingTop: '0.35rem',
                    borderTop: '1px solid rgba(255,255,255,0.06)',
                  }}
                >
                  <span style={{ color: s.has_face_encoding ? 'var(--color-accent-emerald)' : 'var(--color-text-muted)' }}>
                    {s.has_face_encoding ? '✅ Face Registered' : '❌ No Face ID'}
                  </span>
                  {s.is_ta && (
                    <span className="badge" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', fontSize: '0.7rem' }}>
                      ⭐ TA
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        filteredCourses.length === 0 ? (
          <div className="empty-state" style={{ padding: '2.5rem 1rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📚</div>
            <h4 style={{ margin: '0 0 0.5rem 0' }}>No Courses Found</h4>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', margin: 0 }}>
              {searchTerm ? `No courses matching "${searchTerm}".` : 'No curriculum courses are registered for this department.'}
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '0.75rem' }}>
            {filteredCourses.map((c) => (
              <div
                key={c.id}
                style={{
                  background: 'var(--color-bg-secondary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                  <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '0.78rem' }}>
                    {c.code}
                  </span>
                  <span className="badge" style={{ fontSize: '0.72rem', backgroundColor: 'rgba(99, 102, 241, 0.15)', color: '#6366f1' }}>
                    Sem {c.semester || '-'} • {c.credits || 0} Credits
                  </span>
                </div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '0.92rem', lineHeight: 1.3 }}>
                  {c.name}
                </div>
                {c.faculty_name && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-accent-emerald)' }}>
                    👤 {c.faculty_name}
                  </div>
                )}
                {c.description && (
                  <div
                    style={{
                      fontSize: '0.76rem',
                      color: 'var(--color-text-muted)',
                      lineHeight: 1.4,
                      marginTop: '0.2rem',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {c.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function DepartmentsPage() {
  const [departments, setDepartments] = useState([]);
  const [faculties, setFaculties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  /* Department Details Modal State (Faculty, Students, Courses) */
  const [viewingDeptModal, setViewingDeptModal] = useState(null);
  const [deptDetailsTab, setDeptDetailsTab] = useState('faculty');

  const openDetailsModal = (dept, tab = 'faculty') => {
    setViewingDeptModal(dept);
    setDeptDetailsTab(tab);
  };

  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  
  const [programFilter, setProgramFilter] = useState('');
  const [ordering, setOrdering] = useState('dept_id');

  const [availablePrograms, setAvailablePrograms] = useState([]);

  const fetchProgramTypes = async () => {
    try {
      const res = await api.get('/api/scheduler/departments/program-types/');
      if (Array.isArray(res.data)) {
        setAvailablePrograms(res.data);
      }
    } catch (err) {
      console.error('Failed to load program types:', err);
    }
  };

  // Fetch program types and faculties once on mount
  useEffect(() => {
    fetchProgramTypes();
    api.get('/api/auth/faculty/?all=true')
      .then(res => setFaculties(res.data.results || res.data || []))
      .catch(err => console.error('Failed to load faculties for departments', err));
  }, []);

  const totalDegreesCount = useMemo(() => {
    return availablePrograms.reduce((acc, curr) => acc + (Number(curr.count) || 0), 0);
  }, [availablePrograms]);

  useEffect(() => {
    fetchDepartments(page, search, programFilter, ordering);
  }, [page, search, programFilter, ordering]);

  const fetchDepartments = async (pageNum = 1, searchQuery = '', pFilter = '', orderingParam = ordering) => {
    if (pageNum === 1) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }
    try {
      let url = `/api/scheduler/departments/?page=${pageNum}`;
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
      if (pFilter) url += `&program_type=${pFilter}`;
      if (orderingParam) url += `&ordering=${orderingParam}`;
      
      const depRes = await api.get(url);
      const newResults = depRes.data.results || depRes.data || [];
      if (pageNum === 1) {
        setDepartments(newResults);
      } else {
        setDepartments(prev => {
          const newIds = new Set(newResults.map(r => r.id));
          const filteredPrev = prev.filter(r => !newIds.has(r.id));
          return [...filteredPrev, ...newResults];
        });
      }
      setTotalCount(depRes.data.count || (depRes.data.results ? depRes.data.results.length : (depRes.data.length || 0)));
    } catch (err) {
      console.error(err);
      toast.error('Failed to load departments');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleSave = async (formData) => {
    setSaving(true);
    try {
      if (editingDepartment) {
        await api.put(`/api/scheduler/departments/${editingDepartment.id}/`, formData);
        toast.success('Department updated successfully');
      } else {
        await api.post('/api/scheduler/departments/', formData);
        toast.success('Department created successfully');
      }
      setModalOpen(false);
      setEditingDepartment(null);
      fetchDepartments(page, search, programFilter);
      fetchProgramTypes();
    } catch (err) {
      console.error('Save failed:', err);
      toast.error(err.response?.data?.name?.[0] || 'Failed to save department.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await api.delete(`/api/scheduler/departments/${confirmDelete.id}/`);
      setConfirmDelete(null);
      toast.success('Department deleted');
      fetchDepartments(page, search, programFilter);
      fetchProgramTypes();
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete department.');
    }
  };

  const openEditModal = (department) => {
    setEditingDepartment(department);
    setModalOpen(true);
  };

  const openCreateModal = () => {
    setEditingDepartment(null);
    setModalOpen(true);
  };

  const columns = [
    {
      key: 'dept_id',
      label: 'Dept ID',
      render: (val) => val ? (
        <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
          {val}
        </span>
      ) : '-'
    },
    {
      key: 'program_type',
      label: 'Degree',
      render: (val) => val ? <span className="badge" style={{ backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary-dark)' }}>{val}</span> : <span style={{color:'var(--color-text-tertiary)'}}>General</span>
    },
    {
      key: 'name',
      label: 'Department Name',
      sortValue: (row) => row.name || '',
      render: (val, row) => (
        <div
          style={{ cursor: 'pointer' }}
          onClick={() => openDetailsModal(row, 'faculty')}
          title="Click to view department overview & members"
        >
          <div
            style={{
              fontWeight: 600,
              fontSize: '1rem',
              color: 'var(--color-primary)',
              textDecoration: 'underline',
              textDecorationColor: 'transparent',
              transition: 'text-decoration-color 0.2s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.textDecorationColor = 'var(--color-primary)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.textDecorationColor = 'transparent'; }}
          >
            {row.name}
          </div>
          {row.core_department && row.core_department !== row.name && (
            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
              Discipline: {row.core_department}
            </span>
          )}
        </div>
      )
    },
    {
      key: 'no_of_years',
      label: 'Program Years',
      sortValue: (row) => Number(row.no_of_years || 0),
      render: (val) => val || '-'
    },
    {
      key: 'faculty_count',
      label: 'Faculty',
      sortValue: (row) => Number(row.faculty_count || 0),
      render: (val, row) => (
        <button
          type="button"
          className="badge badge-low"
          style={{
            cursor: 'pointer',
            border: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.25rem',
            padding: '0.35rem 0.65rem',
            fontWeight: 600,
            transition: 'transform 0.15s ease, filter 0.15s ease',
          }}
          onClick={(e) => {
            e.stopPropagation();
            openDetailsModal(row, 'faculty');
          }}
          title="View Faculty members"
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.06)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          👥 {val || 0}
        </button>
      )
    },
    {
      key: 'student_count',
      label: 'Students',
      sortValue: (row) => Number(row.student_count || 0),
      render: (val, row) => (
        <button
          type="button"
          className="badge badge-medium"
          style={{
            cursor: 'pointer',
            border: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.25rem',
            padding: '0.35rem 0.65rem',
            fontWeight: 600,
            transition: 'transform 0.15s ease, filter 0.15s ease',
          }}
          onClick={(e) => {
            e.stopPropagation();
            openDetailsModal(row, 'students');
          }}
          title="View Enrolled Students"
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.06)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          👨‍🎓 {val || 0}
        </button>
      )
    },
    {
      key: 'subject_count',
      label: 'Courses',
      sortValue: (row) => Number(row.subject_count || 0),
      render: (val, row) => (
        <button
          type="button"
          className="badge"
          style={{
            cursor: 'pointer',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            backgroundColor: 'rgba(99, 102, 241, 0.12)',
            color: '#6366f1',
            fontWeight: 600,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.25rem',
            padding: '0.35rem 0.65rem',
            transition: 'transform 0.15s ease, filter 0.15s ease',
          }}
          onClick={(e) => {
            e.stopPropagation();
            openDetailsModal(row, 'courses');
          }}
          title="View Curriculum Courses"
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.06)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          📚 {val || 0}
        </button>
      )
    },
    {
      key: 'hod',
      label: 'Head of Dept',
      sortValue: (row) => {
        const hod = faculties.find(f => f.id === row.hod);
        return hod ? `${hod.user?.first_name || ''} ${hod.user?.last_name || ''}`.trim() : '';
      },
      render: (val) => {
        const hod = faculties.find(f => f.id === val);
        return hod ? `${hod.user?.first_name} ${hod.user?.last_name}` : '-';
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      sortable: false,
      render: (_, row) => (
        <div className="action-btns" style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          <button
            className="btn btn-sm btn-secondary"
            onClick={(e) => { e.stopPropagation(); openDetailsModal(row, 'faculty'); }}
            title="View Department details (Faculty, Students, Courses)"
            style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}
          >
            <span>👁️</span> Details
          </button>
          <button
            className="btn btn-sm btn-secondary"
            onClick={(e) => { e.stopPropagation(); openEditModal(row); }}
          >
            Edit
          </button>
          <button
            className="btn btn-sm btn-danger"
            onClick={(e) => { e.stopPropagation(); setConfirmDelete(row); }}
          >
            Delete
          </button>
        </div>
      )
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Departments</h1>
          <p>Manage academic departments, degree programs, and head of department assignments.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-department" onClick={openCreateModal}>+ Add Department</button>
      </div>

      {/* Quick Summary Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--color-primary)', fontSize: '1.4rem' }}>
            🏛️
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{totalCount}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Total Departments</span>
          </div>
        </div>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)', fontSize: '1.4rem' }}>
            👥
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{faculties.length}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Total Faculty</span>
          </div>
        </div>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)', fontSize: '1.4rem' }}>
            👨‍🎓
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>
              {departments.reduce((sum, d) => sum + (d.student_count || 0), 0)}
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Enrolled Students</span>
          </div>
        </div>
      </div>

      <div className="tabs" style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', overflowX: 'auto', paddingBottom: '0.5rem', scrollbarWidth: 'thin' }}>
        <button 
          className={`btn btn-sm ${programFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: programFilter === '' ? 700 : 500 }}
          onClick={() => { setPage(1); setProgramFilter(''); }}
        >
          <span>All Degrees</span>
          <span className="badge" style={{ fontSize: '0.72rem', padding: '0.15rem 0.45rem', backgroundColor: programFilter === '' ? 'rgba(255,255,255,0.25)' : 'var(--color-bg-tertiary)', color: 'inherit' }}>
            {totalDegreesCount || totalCount}
          </span>
        </button>
        {availablePrograms.map(item => {
          const progName = typeof item === 'string' ? item : item.program_type;
          const progCount = typeof item === 'object' ? item.count : undefined;
          const isSelected = programFilter === progName;
          return (
            <button 
              key={progName}
              className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
              style={{ whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: isSelected ? 700 : 500 }}
              onClick={() => { setPage(1); setProgramFilter(progName); }}
            >
              <span>{progName}</span>
              {progCount !== undefined && (
                <span className="badge" style={{ fontSize: '0.72rem', padding: '0.15rem 0.45rem', backgroundColor: isSelected ? 'rgba(255,255,255,0.25)' : 'var(--color-bg-tertiary)', color: 'inherit' }}>
                  {progCount}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--color-primary)' }}>
            🏛️
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Departments</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{totalCount} academic departments registered</span>
          </div>
        </div>
        {loading && departments.length === 0 ? (
           <div className="loading-spinner" style={{ margin: '3rem auto' }}><div className="spinner" /></div>
        ) : (
          <DataTable
            columns={columns}
            data={departments}
            searchKey="name"
            emptyMessage={programFilter ? `No ${programFilter} departments found.` : "No departments created yet."}
            infiniteScroll={true}
            totalCount={totalCount}
            serverPage={page}
            onPageChange={setPage}
            onSearchChange={(s) => { setPage(1); setSearch(s); }}
            pageSize={100}
            loading={loading || loadingMore}
            defaultSortKey="dept_id"
            defaultSortDir="asc"
            onSortChange={({ sortKey, sortDir }) => {
              const backendSortMap = {
                dept_id: 'dept_id',
                name: 'name',
                program_type: 'program_type',
                no_of_years: 'no_of_years',
              };
              const field = backendSortMap[sortKey];
              if (field) {
                setOrdering(sortDir === 'desc' ? `-${field}` : field);
                setPage(1);
              }
            }}
          />
        )}
      </div>

      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingDepartment(null); }}
        title={editingDepartment ? "Edit Department" : "Add Department"}
      >
        <DepartmentForm 
          initialData={editingDepartment} 
          onSave={handleSave} 
          saving={saving} 
          faculties={faculties}
          availablePrograms={availablePrograms}
        />
      </Modal>

      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        message={`Are you sure you want to delete ${confirmDelete?.name}?`}
      />

      {/* Department Details Modal (Faculty, Students, Courses) */}
      <Modal
        open={!!viewingDeptModal}
        onClose={() => setViewingDeptModal(null)}
        title={viewingDeptModal ? `${viewingDeptModal.name} — Overview & Members` : 'Department Details'}
        maxWidth="880px"
      >
        {viewingDeptModal && (
          <DepartmentDetailsModal
            department={viewingDeptModal}
            faculties={faculties}
            initialTab={deptDetailsTab}
            onClose={() => setViewingDeptModal(null)}
          />
        )}
      </Modal>
    </div>
  );
}
