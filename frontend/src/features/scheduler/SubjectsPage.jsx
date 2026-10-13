import toast from 'react-hot-toast';
import { useState, useEffect } from 'react';
import api from '../../api/axios';
import DataTable from '../../components/DataTable';

/* ─── Tiny modal component ─────────────────────────────────────── */
function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content glass-card"
        onClick={(e) => e.stopPropagation()}
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

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function SubjectsPage() {
  const [subjects, setSubjects] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [amenitiesList, setAmenitiesList] = useState([]);
  const [loading, setLoading] = useState(true);

  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('');

  /* Modal state */
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchAll(page, search, departmentFilter, typeFilter, semesterFilter);
  }, [page, search, departmentFilter, typeFilter, semesterFilter]);

  const fetchAll = async (pageNum = 1, searchQuery = '', deptFilter = '', tFilter = '', semFilter = '') => {
    setLoading(true);
    try {
      let url = `/api/scheduler/subjects/?page=${pageNum}`;
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
      if (deptFilter) url += `&department=${deptFilter}`;
      if (tFilter) url += `&subject_type=${tFilter}`;
      if (semFilter) url += `&semester=${semFilter}`;

      const [subRes, facRes, depRes, amRes] = await Promise.all([
        api.get(url),
        api.get('/api/auth/faculty/?all=true'),
        api.get('/api/scheduler/departments/?all=true'),
        api.get('/api/scheduler/amenities/').catch(() => ({ data: { results: [] } }))
      ]);

      const newResults = subRes.data.results || subRes.data || [];
      if (pageNum === 1) {
        setSubjects(newResults);
      } else {
        setSubjects(prev => {
          const newIds = new Set(newResults.map(r => r.id));
          const filteredPrev = prev.filter(r => !newIds.has(r.id));
          return [...filteredPrev, ...newResults];
        });
      }
      setTotalCount(subRes.data.count || (subRes.data.results ? subRes.data.results.length : (subRes.data.length || 0)));
      setFaculty(facRes.data.results || facRes.data || []);
      setDepartments(depRes.data.results || depRes.data || []);
      setAmenitiesList(amRes.data.results || amRes.data || []);
    } catch (err) {
      console.error('Failed to load data:', err);
      toast.error('Failed to load courses data');
    } finally {
      setLoading(false);
    }
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
      fetchAll(page, search, departmentFilter, typeFilter);
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
      fetchAll(page, search, departmentFilter, typeFilter);
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

  const columns = [
    {
      key: 'code',
      label: 'Course Code',
      render: (val) => (
        <span className="badge badge-low" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
          {val}
        </span>
      )
    },
    {
      key: 'name',
      label: 'Course Name',
      render: (val, row) => (
        <div>
          <strong style={{ display: 'block' }}>{val}</strong>
          {row.description && (
            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
              {row.description.length > 50 ? `${row.description.substring(0, 50)}...` : row.description}
            </span>
          )}
        </div>
      )
    },
    {
      key: 'semester',
      label: 'Semester',
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
      )
    },
    {
      key: 'department',
      label: 'Department / Group',
      render: (_, row) => {
        // If row has associated departments
        if (row.departments && row.departments.length > 0) {
          if (row.departments.length >= 30) {
            return (
              <span className="badge badge-low" style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                🌐 All B.Tech Branches ({row.departments.length})
              </span>
            );
          }
          if (row.departments.length === 15) {
            const isGroupA = row.code.includes('PH101') || row.code.includes('PH191') || row.code.includes('ME191') || row.code.includes('MC-181') || row.code.includes('CH201') || row.code.includes('CH291') || row.code.includes('ME292') || row.code.includes('MC-282');
            return (
              <span className="badge badge-low" style={{ fontWeight: 600 }}>
                👥 {isGroupA ? 'Group A (CSE & Allied)' : 'Group B (Others)'} (15)
              </span>
            );
          }
          const firstDept = departments.find(d => d.id === row.departments[0]);
          if (firstDept) {
            return (
              <div>
                {firstDept.dept_id && (
                  <span className="badge badge-low" style={{ marginRight: '0.4rem', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    {firstDept.dept_id}
                  </span>
                )}
                <span style={{ fontWeight: 500 }}>{firstDept.name}</span>
                {row.departments.length > 1 && (
                  <span className="badge badge-low" style={{ marginLeft: '0.3rem', fontSize: '0.7rem' }}>
                    +{row.departments.length - 1}
                  </span>
                )}
              </div>
            );
          }
        }
        const deptId = row.faculty_dept_id;
        const deptName = row.faculty_department;
        if (deptName) {
          return (
            <div>
              {deptId && (
                <span className="badge badge-low" style={{ marginRight: '0.4rem', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {deptId}
                </span>
              )}
              <span style={{ fontWeight: 500 }}>{deptName}</span>
            </div>
          );
        }
        return <span style={{ color: 'var(--color-text-tertiary)' }}>General</span>;
      }
    },
    {
      key: 'faculty_name',
      label: 'Faculty',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600 }}>{val || 'Unassigned'}</div>
          {row.faculty_employee_id && (
            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
              {row.faculty_employee_id}
            </div>
          )}
        </div>
      )
    },
    {
      key: 'subject_type',
      label: 'Type',
      render: (val) => {
        if (val === 'lab') {
          return <span className="badge badge-present">🧪 Lab</span>;
        }
        if (val === 'seminar') {
          return <span className="badge badge-high">🎙️ Seminar</span>;
        }
        return <span className="badge badge-low">📖 Lecture</span>;
      }
    },
    {
      key: 'credits',
      label: 'Credits',
      render: (val) => <span className="badge badge-low">{val} Credits</span>
    },
    {
      key: 'sessions_per_week',
      label: 'Sessions/Week',
      render: (val) => <span className="badge badge-medium">{val} / wk</span>
    },
    {
      key: 'required_capacity',
      label: 'Capacity',
      render: (val) => <span className="badge badge-medium">Cap: {val}</span>
    },
    {
      key: 'amenities',
      label: 'Req. Amenities',
      render: (val) => {
        if (!val || val.length === 0) return <span className="badge badge-low">None</span>;
        return (
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {val.map(id => {
              const am = amenitiesList.find(a => a.id === id);
              return <span key={id} className="badge badge-medium">{am ? am.name : id}</span>;
            })}
          </div>
        );
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="action-btns">
          <button className="btn btn-sm btn-secondary" onClick={(e) => { e.stopPropagation(); openEdit(row); }}>Edit</button>
          <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); setConfirmDelete(row); }}>Delete</button>
        </div>
      )
    },
  ];

  const totalPages = Math.ceil(totalCount / 100) || 1;

  if (loading && subjects.length === 0) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Courses</h1>
          <p>Manage academic courses, subject details, faculty assignments, and department mappings.</p>
        </div>
        <button className="btn btn-primary" id="btn-add-course" onClick={openAdd}>+ Add Course</button>
      </div>

      {/* Quick Summary Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)', fontSize: '1.4rem' }}>
            📖
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{totalCount}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Total Courses</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-accent-emerald)', fontSize: '1.4rem' }}>
            👥
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{faculty.length}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Assigned Faculty</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--color-primary)', fontSize: '1.4rem' }}>
            🏛️
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{departments.length}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Active Departments</span>
          </div>
        </div>
      </div>

      {/* Filter Bar with Type Tabs and Department Selector */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem', justifyContent: 'space-between' }}>
        <div className="tabs" style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.25rem', margin: 0 }}>
          <button 
            className={`btn btn-sm ${typeFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setTypeFilter(''); }}
          >
            All Types
          </button>
          <button 
            className={`btn btn-sm ${typeFilter === 'lecture' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setTypeFilter('lecture'); }}
          >
            📖 Lectures
          </button>
          <button 
            className={`btn btn-sm ${typeFilter === 'lab' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setTypeFilter('lab'); }}
          >
            🧪 Laboratories
          </button>
          <button 
            className={`btn btn-sm ${typeFilter === 'seminar' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setPage(1); setTypeFilter('seminar'); }}
          >
            🎙️ Seminars
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <select
            className="form-input"
            style={{ width: 'auto', minWidth: '160px', padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
            value={semesterFilter}
            onChange={(e) => { setPage(1); setSemesterFilter(e.target.value); }}
          >
            <option value="">-- All Semesters --</option>
            <option value="1">Semester 1 (1st Year)</option>
            <option value="2">Semester 2 (1st Year)</option>
            <option value="3">Semester 3</option>
            <option value="4">Semester 4</option>
            <option value="5">Semester 5</option>
            <option value="6">Semester 6</option>
            <option value="7">Semester 7</option>
            <option value="8">Semester 8</option>
          </select>

          <select
            className="form-input"
            style={{ width: 'auto', minWidth: '220px', padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
            value={departmentFilter}
            onChange={(e) => { setPage(1); setDepartmentFilter(e.target.value); }}
          >
            <option value="">-- All Departments --</option>
            {departments.map(d => (
              <option key={d.id} value={d.id}>
                {d.dept_id ? `[${d.dept_id}] ` : ''}{d.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="glass-card animate-fade-in-up" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-accent-blue)' }}>
            📖
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>All Courses</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{totalCount} courses registered in the system</span>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={subjects}
          loading={loading}
          serverPagination={{
            currentPage: page,
            totalPages,
            totalCount,
            onPageChange: (p) => setPage(p)
          }}
          searchValue={search}
          onSearchChange={(val) => { setSearch(val); setPage(1); }}
          emptyMessage="No courses registered yet."
        />
      </div>

      {/* Add/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditingItem(null); }}
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
