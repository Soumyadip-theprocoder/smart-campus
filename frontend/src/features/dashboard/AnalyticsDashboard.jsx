import React, { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../../api/axios';

import { Suspense, lazy } from 'react';
import LocalErrorBoundary from '../../components/LocalErrorBoundary';

const StudentClustersChart = lazy(() => import('./StudentClustersChart'));

export default function AnalyticsDashboard() {
  const [departmentTrends, setDepartmentTrends] = useState([]);
  const [subjectAverages, setSubjectAverages] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [dailyTrends, setDailyTrends] = useState([]);
  const [dayOfWeek, setDayOfWeek] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [deptRes, subjRes, clustersRes, dailyRes, dayOfWeekRes] = await Promise.all([
        api.get('/api/analytics/department-trends/').catch(() => ({ data: [] })),
        api.get('/api/analytics/subject-averages/').catch(() => ({ data: [] })),
        api.get('/api/analytics/student-clusters/').catch(() => ({ data: [] })),
        api.get('/api/analytics/daily-trends/').catch(() => ({ data: [] })),
        api.get('/api/analytics/day-of-week-trends/').catch(() => ({ data: [] }))
      ]);
      setDepartmentTrends(deptRes.data || []);
      setSubjectAverages(subjRes.data || []);
      setClusters(clustersRes.data || []);
      setDailyTrends(dailyRes.data || []);
      setDayOfWeek(dayOfWeekRes.data || []);
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
                  contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
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
                  contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--color-accent-blue)' }}
                />
                <Bar dataKey="percentage" fill="var(--color-accent-blue)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* New Analytics Row */}
      <div className="grid-2" style={{ marginTop: '1.5rem' }}>
        {/* Daily Trends (14 days) */}
        <div className="glass-card dashboard-chart">
          <div className="section-header" style={{ padding: '1.5rem 1.5rem 0.5rem' }}>
            <h3 className="section-title">14-Day Attendance Trend</h3>
          </div>
          <div style={{ height: '300px', padding: '0 1.5rem 1.5rem 1.5rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="date" stroke="var(--color-text-muted)" />
                <YAxis stroke="var(--color-text-muted)" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--color-accent-purple)' }}
                />
                <Line type="monotone" dataKey="percentage" stroke="var(--color-accent-purple)" strokeWidth={3} activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Day of Week Radar */}
        <div className="glass-card dashboard-chart">
          <div className="section-header" style={{ padding: '1.5rem 1.5rem 0.5rem' }}>
            <h3 className="section-title">Attendance by Day of Week</h3>
          </div>
          <div style={{ height: '300px', padding: '0 1.5rem 1.5rem 1.5rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={dayOfWeek}>
                <PolarGrid stroke="rgba(255,255,255,0.2)" />
                <PolarAngleAxis dataKey="day" stroke="var(--color-text-muted)" />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="var(--color-text-muted)" />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                />
                <Radar name="Attendance %" dataKey="percentage" stroke="var(--color-accent-orange)" fill="var(--color-accent-orange)" fillOpacity={0.5} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid-1" style={{ marginTop: '1.5rem' }}>
        {/* Behavioral Clusters Chart */}
        <div className="glass-card dashboard-chart">
          <div className="section-header" style={{ padding: '1.5rem 1.5rem 0.5rem' }}>
            <h3 className="section-title">ML Behavioral Clusters (AI Analysis)</h3>
          </div>
          <div style={{ height: '350px', padding: '0 1.5rem 1.5rem 1.5rem' }}>
            {clusters.length === 0 ? (
              <div className="empty-state"><p>No clustering data available.</p></div>
            ) : (
              <LocalErrorBoundary>
                <Suspense fallback={<div className="loading-spinner"><div className="spinner" /></div>}>
                  <StudentClustersChart data={clusters} />
                </Suspense>
              </LocalErrorBoundary>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
