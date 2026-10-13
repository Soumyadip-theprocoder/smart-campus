import { useState, useMemo, useEffect, useRef } from 'react';

export default function DataTable({ 
  columns, data, emptyMessage = 'No data available.', searchKey = null, onRowClick = null, pageSize = 20,
  serverPagination = false, totalCount = 0, serverPage = 1, onPageChange = null, onSearchChange = null,
  infiniteScroll = false
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const observerRef = useRef(null);

  const isServerDriven = serverPagination || infiniteScroll;

  const handleSearch = (e) => {
    const val = e.target.value;
    setSearchTerm(val);
    if (isServerDriven && onSearchChange) {
      onSearchChange(val);
    } else {
      setCurrentPage(1);
    }
  };

  const filteredData = useMemo(() => {
    if (isServerDriven) return data || [];
    return data?.filter((row) => {
      if (!searchKey || !searchTerm) return true;
      const value = row[searchKey];
      return String(value).toLowerCase().includes(searchTerm.toLowerCase());
    }) || [];
  }, [data, searchKey, searchTerm, isServerDriven]);

  const activePage = isServerDriven ? serverPage : currentPage;
  const activeTotalPages = isServerDriven 
    ? (Math.ceil(totalCount / pageSize) || 1)
    : (Math.ceil(filteredData.length / pageSize) || 1);
  const activeTotalCount = isServerDriven ? totalCount : filteredData.length;
  
  const startIndex = (activePage - 1) * pageSize;
  const paginatedData = isServerDriven 
    ? filteredData 
    : filteredData.slice(startIndex, startIndex + pageSize);

  const handlePageChange = (newPage) => {
    if (isServerDriven && onPageChange) {
      onPageChange(newPage);
    } else {
      setCurrentPage(newPage);
    }
  };

  useEffect(() => {
    if (!infiniteScroll) return;
    const observer = new IntersectionObserver(
      (entries) => {
        // Only fetch if intersecting, and we haven't reached the end, 
        // AND the current data length reflects the current activePage 
        // (to prevent rapid-fire requests while waiting for network)
        const expectedItems = activePage * pageSize;
        const isDataLoaded = filteredData.length >= Math.min(expectedItems, activeTotalCount);
        
        if (entries[0].isIntersecting && activePage < activeTotalPages && isDataLoaded) {
          handlePageChange(activePage + 1);
        }
      },
      { threshold: 0.1, rootMargin: '100px' }
    );
    if (observerRef.current) {
      observer.observe(observerRef.current);
    }
    return () => observer.disconnect();
  }, [infiniteScroll, activePage, activeTotalPages, filteredData.length, activeTotalCount, pageSize]);

  return (
    <div className="data-table-wrapper">
      {searchKey && (
        <div style={{ marginBottom: '1rem', maxWidth: '300px' }}>
          <input
            type="text"
            className="form-input"
            placeholder={`Search...`}
            value={searchTerm}
            onChange={handleSearch}
          />
        </div>
      )}
      
      {filteredData.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>{emptyMessage}</h3>
        </div>
      ) : (
        <>
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
                {paginatedData.map((row, i) => (
                  <tr key={row.id || i} onClick={() => onRowClick && onRowClick(row)} style={{ cursor: onRowClick ? 'pointer' : 'default' }}>
                    {columns.map((col) => (
                      <td key={col.key} data-label={col.label}>
                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {infiniteScroll && (
              <div ref={observerRef} style={{ height: '20px', margin: '1rem 0', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                {activePage < activeTotalPages ? 'Loading more...' : 'No more data'}
              </div>
            )}
          </div>
          
          {!infiniteScroll && activeTotalPages > 1 && (
            <div className="pagination-controls" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                Showing {startIndex + 1} to {Math.min(startIndex + pageSize, activeTotalCount)} of {activeTotalCount} entries
              </span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button 
                  className="btn btn-secondary" 
                  disabled={activePage === 1}
                  onClick={() => handlePageChange(Math.max(1, activePage - 1))}
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.9rem' }}
                >
                  Previous
                </button>
                <span style={{ padding: '0.4rem 0.8rem', background: 'var(--color-bg-secondary)', borderRadius: '4px', fontSize: '0.9rem', fontWeight: 500 }}>
                  Page {activePage} of {activeTotalPages}
                </span>
                <button 
                  className="btn btn-secondary" 
                  disabled={activePage === activeTotalPages}
                  onClick={() => handlePageChange(Math.min(activeTotalPages, activePage + 1))}
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.9rem' }}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
