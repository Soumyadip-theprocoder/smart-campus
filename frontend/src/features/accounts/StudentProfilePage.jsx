import toast from 'react-hot-toast';
import { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import FaceRegistrationModal from './FaceRegistrationModal';
import EditMarksForm from '../../components/EditMarksForm';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function StudentProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [isFaceModalOpen, setIsFaceModalOpen] = useState(false);
  const [isMarksModalOpen, setIsMarksModalOpen] = useState(false);
  const [savingMarks, setSavingMarks] = useState(false);
  
  const [isAccessModalOpen, setIsAccessModalOpen] = useState(false);
  const [amenities, setAmenities] = useState([]);
  const [accessNeeds, setAccessNeeds] = useState([]);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    setLoading(true);
    try {
      const [meRes, amRes] = await Promise.all([
        api.get('/api/auth/me/'),
        api.get('/api/scheduler/amenities/').catch(() => ({ data: { results: [] } }))
      ]);

      setProfile(meRes.data);
      setAmenities(amRes.data.results || amRes.data || []);
      setAccessNeeds(meRes.data.profile?.accessibility_needs || []);
    } catch (err) {
      console.error('Failed to load profile data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAccess = async () => {
    try {
      await api.put('/api/auth/me/', { accessibility_needs: accessNeeds });
      toast.success('Accessibility preferences saved!');
      setIsAccessModalOpen(false);
      loadProfileData();
    } catch (e) {
      toast.error('Failed to save accessibility preferences.');
    }
  };

  const handleSaveMarks = async (marksData) => {
    if (!profile?.profile?.id) return;
    setSavingMarks(true);
    try {
      await api.patch(`/api/auth/students/${profile.profile.id}/`, marksData);
      toast.success('Marks updated successfully!');
      setIsMarksModalOpen(false);
      loadProfileData();
    } catch (e) {
      toast.error('Failed to update marks.');
    } finally {
      setSavingMarks(false);
    }
  };

  if (loading) {
    return <div className="loading-spinner"><div className="spinner" /></div>;
  }

  // Completeness logic
  const p = profile?.profile || {};
  const dataPoints = [
    { name: 'Face Data', complete: p.has_face_encoding },
    { name: '10th Marks', complete: p.marks_10th !== null && p.marks_10th !== undefined },
    { name: '12th Marks', complete: p.marks_12th !== null && p.marks_12th !== undefined },
    { name: 'Accessibility', complete: p.accessibility_needs !== undefined && p.accessibility_needs !== null }
  ];

  const completedCount = dataPoints.filter(d => d.complete).length;
  const incompleteCount = dataPoints.length - completedCount;
  
  const chartData = [
    { name: 'Complete', value: completedCount, color: '#10b981' },
    { name: 'Incomplete', value: incompleteCount, color: '#ef4444' }
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>My Profile</h1>
        <p>Manage your face data, academic records, and accessibility preferences.</p>
      </div>

      <div className="grid-2">
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>Profile Completeness</h3>
          <div style={{ height: '200px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <p style={{ textAlign: 'center', marginTop: '1rem' }}>
            {completedCount} of {dataPoints.length} profile sections completed.
          </p>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 className="section-title">Profile Actions</h3>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'var(--color-bg-secondary)', borderRadius: '0.5rem' }}>
            <div>
              <h4 style={{ margin: '0 0 0.25rem 0' }}>Face Registration</h4>
              <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                {p.has_face_encoding ? '✅ Face data registered' : '❌ Not registered'}
              </span>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setIsFaceModalOpen(true)}>
              {p.has_face_encoding ? 'Update Face' : 'Register Face'}
            </button>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'var(--color-bg-secondary)', borderRadius: '0.5rem' }}>
            <div>
              <h4 style={{ margin: '0 0 0.25rem 0' }}>Academic Records</h4>
              <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                {(p.marks_10th && p.marks_12th) ? '✅ Marks uploaded' : '❌ Incomplete marks'}
              </span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => setIsMarksModalOpen(true)}>
              Update Marks
            </button>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'var(--color-bg-secondary)', borderRadius: '0.5rem' }}>
            <div>
              <h4 style={{ margin: '0 0 0.25rem 0' }}>Accessibility Preferences</h4>
              <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                {p.accessibility_needs !== undefined ? '✅ Preferences saved' : '❌ Not saved'}
              </span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => setIsAccessModalOpen(true)}>
              Update Preferences
            </button>
          </div>
        </div>
      </div>

      <FaceRegistrationModal 
        isOpen={isFaceModalOpen} 
        onClose={() => setIsFaceModalOpen(false)} 
        onSuccess={loadProfileData}
        studentId={p.id}
      />

      {isAccessModalOpen && (
        <div className="modal-overlay" onClick={() => setIsAccessModalOpen(false)}>
          <div className="modal-content glass-card" onClick={e => e.stopPropagation()}>
            <h3>♿ Accessibility Preferences</h3>
            <p>Select any accommodations you require for your classes.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
              {amenities.map(a => (
                <label key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem', background: 'var(--color-bg-glass)', borderRadius: '4px' }}>
                  <input
                    type="checkbox"
                    checked={accessNeeds.includes(a.name)}
                    onChange={(e) => {
                      if (e.target.checked) setAccessNeeds([...accessNeeds, a.name]);
                      else setAccessNeeds(accessNeeds.filter(n => n !== a.name));
                    }}
                  />
                  {a.name} - <span style={{fontSize: '0.8rem', color: 'var(--color-text-muted)'}}>{a.description || 'Accommodation'}</span>
                </label>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" onClick={() => setIsAccessModalOpen(false)} style={{flex: 1}}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveAccess} style={{flex: 1}}>Save Preferences</button>
            </div>
          </div>
        </div>
      )}

      {isMarksModalOpen && (
        <div className="modal-overlay" onClick={() => setIsMarksModalOpen(false)}>
          <div className="modal-content glass-card" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🎓 Update Academic Records</h2>
              <button className="modal-close" onClick={() => setIsMarksModalOpen(false)}>×</button>
            </div>
            <EditMarksForm 
              initialData={p} 
              onSave={handleSaveMarks} 
              saving={savingMarks} 
            />
          </div>
        </div>
      )}
    </div>
  );
}
