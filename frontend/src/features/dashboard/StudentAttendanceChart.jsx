import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function StudentAttendanceChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="empty-state"><p>No attendance data available.</p></div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(255,255,255,0.1)" />
          ))}
        </Pie>
        <Tooltip 
          contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
          itemStyle={{ color: 'var(--color-text)' }}
          formatter={(value) => [`${value}%`, 'Attendance']}
        />
        <Legend wrapperStyle={{ fontSize: '0.8rem' }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
