export default function StatCard({ icon, label, value, change, gradient, delay = 0, onClick = null }) {
  const gradientMap = {
    blue: 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.05))',
    emerald: 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.05))',
    purple: 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(139,92,246,0.05))',
    orange: 'linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.05))',
    red: 'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.05))',
  };

  const iconBgMap = {
    blue: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    emerald: 'linear-gradient(135deg, #10b981, #059669)',
    purple: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    orange: 'linear-gradient(135deg, #f59e0b, #d97706)',
    red: 'linear-gradient(135deg, #ef4444, #dc2626)',
  };

  return (
    <div
      className={`glass-card stat-card animate-fade-in-up stagger-${delay} ${onClick ? 'clickable' : ''}`}
      style={{ opacity: 0, cursor: onClick ? 'pointer' : 'default', transition: 'all 0.2s ease' }}
      onClick={onClick}
    >
      <div
        className="stat-icon"
        style={{ background: iconBgMap[gradient] || iconBgMap.blue }}
      >
        {icon}
      </div>
      <div className="stat-info">
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
        {change && (
          <div className={`stat-change ${change.startsWith('-') ? 'negative' : ''}`}>
            {change}
          </div>
        )}
      </div>
    </div>
  );
}
