import React, { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../../api/axios';

export default function AnalyticsDashboard() {
  const [departmentTrends, setDepartmentTrends] = useState([]);
  const [subjectAverages, setSubjectAverages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [deptRes, subjRes] = await Promise.all([
        api.get('/api/analytics/department-trends/').catch(() => ({ data: [] })),
        api.get('/api/analytics/subject-averages/').catch(() => ({ data: [] }))
      ]);
      setDepartmentTrends(deptRes.data || []);
      setSubjectAverages(subjRes.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Campus Analytics</h1>
        <p>Deep dive into attendance data</p>
      </div>

      <div className="grid-2" style={{ marginTop: '1.5rem' }}>
        {/* Department Trends */}
        <div className="glass-card dashboard-chart">
          <div className="section-header" style={{ padding: '1.5rem 1.5rem 0.5rem' }}>
            <h3 className="section-title">Department Trends</h3>
          </div>
          <div style={{ height: '300px', padding: '0 1.5rem 1.5rem 1.5rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={departmentTrends}>
                <defs>
                  <linearGradient id="colorDept" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-accent-emerald)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--color-accent-emerald)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="department" stroke="var(--color-text-muted)" />
                <YAxis stroke="var(--color-text-muted)" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--color-accent-emerald)' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="percentage" 
                  stroke="var(--color-accent-emerald)" 
                  strokeWidth={3}
                  fillOpacity={1} 
                  fill="url(#colorDept)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Subject Averages */}
        <div className="glass-card dashboard-chart">
          <div className="section-header" style={{ padding: '1.5rem 1.5rem 0.5rem' }}>
            <h3 className="section-title">Subject Averages</h3>
          </div>
          <div style={{ height: '300px', padding: '0 1.5rem 1.5rem 1.5rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={subjectAverages}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="subject_code" stroke="var(--color-text-muted)" />
                <YAxis stroke="var(--color-text-muted)" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--color-accent-blue)' }}
                />
                <Bar dataKey="percentage" fill="var(--color-accent-blue)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
