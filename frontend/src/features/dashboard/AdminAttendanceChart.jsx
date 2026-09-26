import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AdminAttendanceChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="empty-state"><p>No attendance data available.</p></div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorAttendance" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--color-accent-emerald)" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="var(--color-accent-emerald)" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
        <XAxis dataKey="department" stroke="var(--color-text-muted)" />
        <YAxis stroke="var(--color-text-muted)" />
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
          fill="url(#colorAttendance)" 
          activeDot={{ r: 8 }} 
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
