import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#10b981', '#ef4444', '#f59e0b', '#3b82f6'];

export default function StudentClustersChart({ data }) {
  // Aggregate data by profile_name
  const groupedData = data.reduce((acc, curr) => {
    const name = curr.profile_name;
    const existing = acc.find(item => item.name === name);
    if (existing) {
      existing.value += 1;
    } else {
      acc.push({ name, value: 1 });
    }
    return acc;
  }, []);

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={groupedData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
        >
          {groupedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => [`${value} Students`, 'Count']} />
        <Legend verticalAlign="bottom" height={36} />
      </PieChart>
    </ResponsiveContainer>
  );
}
