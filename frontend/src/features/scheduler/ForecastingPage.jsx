import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import api from '../../api/axios';
import StatCard from '../../components/StatCard';
import { HiOutlineUsers, HiOutlineOfficeBuilding, HiOutlineAcademicCap } from 'react-icons/hi';

export default function ForecastingPage() {
  const [growthPct, setGrowthPct] = useState(10);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  const fetchForecast = async (pct) => {
    setLoading(true);
    try {
      const res = await api.post('/api/scheduler/analytics/forecast/', {
        enrollment_growth_pct: pct
      });
      setData(res.data);
    } catch (err) {
      toast.error('Failed to load forecast data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast(growthPct);
    // eslint-disable-next-line
  }, []);

  const handleApply = () => {
    fetchForecast(growthPct);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Predictive Capacity Analytics</h1>
        <p>Simulate campus growth and forecast required resources.</p>
      </div>

      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h3 className="section-title">Growth Simulation</h3>
        <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
          Adjust the slider to simulate enrollment growth percentage.
        </p>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
          <input 
            type="range" 
            min="0" 
            max="100" 
            step="1" 
            value={growthPct} 
            onChange={(e) => setGrowthPct(Number(e.target.value))}
            style={{ flex: 1, accentColor: 'var(--color-accent-primary)', minWidth: '200px' }}
          />
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', width: '80px', color: 'var(--color-text)' }}>
            +{growthPct}%
          </div>
          <button className="btn btn-primary" onClick={handleApply} disabled={loading}>
            {loading ? 'Calculating...' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {data && (
        <>
          <h3 className="section-title" style={{ marginBottom: '1rem' }}>Projected Shortfalls (Needs)</h3>
          <div className="grid-3">
            <StatCard
              icon={<HiOutlineAcademicCap />}
              label="Additional Faculty Needed"
              value={data.projected_needs.additional_faculty_needed}
              gradient="orange"
            />
            <StatCard
              icon={<HiOutlineOfficeBuilding />}
              label="Additional Room Slots Needed"
              value={data.projected_needs.additional_rooms_needed}
              gradient="purple"
            />
            <StatCard
              icon={<HiOutlineUsers />}
              label="Additional TAs Needed"
              value={data.projected_needs.additional_tas_needed}
              gradient="emerald"
            />
          </div>

          <div className="glass-card" style={{ padding: '2rem', marginTop: '2rem' }}>
             <h3 className="section-title">Current vs Projected Overview</h3>
             <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
               <table className="data-table" style={{ width: '100%' }}>
                 <thead>
                   <tr>
                     <th style={{ textAlign: 'left', padding: '1rem' }}>Metric</th>
                     <th style={{ textAlign: 'right', padding: '1rem' }}>Current</th>
                     <th style={{ textAlign: 'right', padding: '1rem' }}>Projected (+{data.growth_assumptions.enrollment_growth_pct}%)</th>
                   </tr>
                 </thead>
                 <tbody>
                   <tr>
                     <td style={{ padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>Active Class Sessions</td>
                     <td style={{ textAlign: 'right', padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>{data.current_metrics.active_classes}</td>
                     <td style={{ textAlign: 'right', padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>{data.projected_needs.projected_classes}</td>
                   </tr>
                   <tr>
                     <td style={{ padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>Total Room Slots Available (Weekly)</td>
                     <td style={{ textAlign: 'right', padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>{data.current_metrics.total_room_slots}</td>
                     <td style={{ textAlign: 'right', padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>{data.current_metrics.total_room_slots}</td>
                   </tr>
                 </tbody>
               </table>
             </div>
          </div>
        </>
      )}
    </div>
  );
}
