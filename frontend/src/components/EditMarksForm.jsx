import { useState } from 'react';

export default function EditMarksForm({ initialData, onSave, saving }) {
  const [form, setForm] = useState({
    marks_10th: initialData?.marks_10th || '',
    marks_12th: initialData?.marks_12th || '',
    cgpa_semesters: initialData?.cgpa_semesters || {},
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleCgpaChange = (sem, value) => {
    setForm((prev) => ({
      ...prev,
      cgpa_semesters: {
        ...prev.cgpa_semesters,
        [sem]: value
      }
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    let parsedCgpa = { ...form.cgpa_semesters };
    const maxSem = (parseInt(initialData?.semester) || 1) - 1;
    
    // Clean up CGPA object: remove empty values and semesters >= current
    Object.keys(parsedCgpa).forEach(key => {
      if (parseInt(key) > maxSem || !parsedCgpa[key]) {
        delete parsedCgpa[key];
      } else {
        parsedCgpa[key] = parseFloat(parsedCgpa[key]);
      }
    });

    onSave({
      marks_10th: form.marks_10th ? parseFloat(form.marks_10th) : null,
      marks_12th: form.marks_12th ? parseFloat(form.marks_12th) : null,
      cgpa_semesters: parsedCgpa,
    });
  };

  const semesterCount = parseInt(initialData?.semester) || 1;

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">10th Marks (%)</label>
          <input
            className="form-input"
            type="number"
            step="0.01"
            name="marks_10th"
            value={form.marks_10th}
            onChange={handleChange}
            placeholder="e.g. 85.50"
          />
        </div>
        <div className="form-group">
          <label className="form-label">12th Marks (%)</label>
          <input
            className="form-input"
            type="number"
            step="0.01"
            name="marks_12th"
            value={form.marks_12th}
            onChange={handleChange}
            placeholder="e.g. 90.00"
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Semester-wise CGPA</label>
        {semesterCount > 1 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '0.75rem', marginTop: '0.5rem' }}>
            {Array.from({ length: semesterCount - 1 }, (_, i) => i + 1).map(sem => (
              <div key={sem}>
                <label style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem', display: 'block' }}>
                  Sem {sem} CGPA
                </label>
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  min="0"
                  max="10"
                  value={form.cgpa_semesters[sem] || ''}
                  onChange={(e) => handleCgpaChange(sem, e.target.value)}
                  placeholder="e.g. 8.5"
                />
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontStyle: 'italic', padding: '0.5rem 0' }}>
            N/A (Student is in 1st semester)
          </div>
        )}
      </div>
      <button
        type="submit"
        className="btn btn-primary btn-lg"
        style={{ width: '100%', marginTop: '0.5rem' }}
        disabled={saving}
      >
        {saving ? 'Saving...' : 'Save Marks'}
      </button>
    </form>
  );
}
