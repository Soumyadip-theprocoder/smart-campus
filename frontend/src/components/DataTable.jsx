import { useState } from 'react';

export default function DataTable({ columns, data, emptyMessage = 'No data available.', searchKey = null, onRowClick = null }) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredData = data?.filter((row) => {
    if (!searchKey || !searchTerm) return true;
    const value = row[searchKey];
    return String(value).toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <div className="data-table-wrapper">
      {searchKey && (
        <div style={{ marginBottom: '1rem', maxWidth: '300px' }}>
          <input
            type="text"
            className="form-input"
            placeholder={`Search...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      )}
      
      {!filteredData || filteredData.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>{emptyMessage}</h3>
        </div>
      ) : (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col.key}>{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredData.map((row, i) => (
                <tr key={row.id || i} onClick={() => onRowClick && onRowClick(row)} style={{ cursor: onRowClick ? 'pointer' : 'default' }}>
                  {columns.map((col) => (
                    <td key={col.key}>
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
