import { useState, useMemo, useEffect, useRef } from 'react';

/**
 * Natural comparison helper supporting numbers, numeric strings, and alphanumeric text.
 */
function naturalCompare(a, b) {
  if (a === b) return 0;
  // Push null/undefined/empty to the end
  if (a === null || a === undefined || a === '') return 1;
  if (b === null || b === undefined || b === '') return -1;

  if (typeof a === 'number' && typeof b === 'number') {
    return a - b;
  }
  if (typeof a === 'boolean' && typeof b === 'boolean') {
    return a === b ? 0 : a ? 1 : -1;
  }

  const strA = String(a).trim();
  const strB = String(b).trim();

  // If both strings represent valid numbers, compare numerically
  const numA = Number(strA);
  const numB = Number(strB);
  if (!isNaN(numA) && !isNaN(numB) && strA !== '' && strB !== '') {
    return numA - numB;
  }

  // Natural alphanumeric comparison (e.g. STU-0001 < STU-0010)
  return strA.localeCompare(strB, undefined, { numeric: true, sensitivity: 'base' });
}

export default function DataTable({ 
  columns = [], 
  data = [], 
  emptyMessage = 'No data available.', 
  searchKey = null, 
  searchValue = undefined,
  onSearchChange = null,
  onRowClick = null, 
  pageSize = 20,
  serverPagination = false, 
  totalCount = 0, 
  serverPage = 1, 
  onPageChange = null, 
  infiniteScroll = false,
  defaultSortKey = null,
  defaultSortDir = 'asc',
  onSortChange = null,
  sortable = true,
  showSortToolbar = true,
  loading = false,
  isSearching = false
}) {
  const [internalSearch, setInternalSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortKey, setSortKey] = useState(defaultSortKey);
  const [sortDir, setSortDir] = useState(defaultSortDir);
  const observerRef = useRef(null);

  const isServerDriven = serverPagination || infiniteScroll;
  const isControlledSearch = searchValue !== undefined;
  const currentSearchTerm = isControlledSearch ? searchValue : internalSearch;

  // Sync sort state if default props update
  useEffect(() => {
    if (defaultSortKey !== undefined && defaultSortKey !== null) {
      setSortKey(defaultSortKey);
    }
  }, [defaultSortKey]);

  useEffect(() => {
    if (defaultSortDir) {
      setSortDir(defaultSortDir);
    }
  }, [defaultSortDir]);

  const handleSearch = (e) => {
    const val = e.target.value;
    if (!isControlledSearch) {
      setInternalSearch(val);
    }
    if (onSearchChange) {
      onSearchChange(val);
    }
    if (!isServerDriven) {
      setCurrentPage(1);
    }
  };

  // Find sortable columns
  const sortableColumns = useMemo(() => {
    if (!sortable) return [];
    return columns.filter(c => c.sortable !== false && c.key !== 'actions');
  }, [columns, sortable]);

  // Handle column header click
  const handleColumnSort = (key) => {
    if (!sortable) return;
    const col = columns.find(c => c.key === key);
    if (!col || col.sortable === false || key === 'actions') return;

    let nextDir = 'asc';
    if (sortKey === key) {
      nextDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      nextDir = 'asc';
    }

    setSortKey(key);
    setSortDir(nextDir);

    if (onSortChange) {
      onSortChange({ sortKey: key, sortDir: nextDir });
    }
  };

  const handleSortKeySelect = (key) => {
    setSortKey(key);
    if (onSortChange) {
      onSortChange({ sortKey: key, sortDir });
    }
  };

  const toggleSortDir = () => {
    const nextDir = sortDir === 'asc' ? 'desc' : 'asc';
    setSortDir(nextDir);
    if (onSortChange && sortKey) {
      onSortChange({ sortKey, sortDir: nextDir });
    }
  };

  // 1. Filter data (client-side if not server driven)
  const filteredData = useMemo(() => {
    if (isServerDriven) return data || [];
    if (!data) return [];
    if (!searchKey || !currentSearchTerm) return data;
    return data.filter((row) => {
      const value = row[searchKey];
      return String(value ?? '').toLowerCase().includes(currentSearchTerm.toLowerCase());
    });
  }, [data, searchKey, currentSearchTerm, isServerDriven]);

  // 2. Sort data
  const sortedData = useMemo(() => {
    // When pagination/infinite scrolling is server-driven, the backend SQL query
    // handles ordering. Client-side re-sorting of accumulated paginated chunks
    // is redundant, causes performance degradation on large sets, and can scramble
    // the append sequence.
    if (isServerDriven) {
      return filteredData || [];
    }

    if (!filteredData || filteredData.length === 0 || !sortKey || !sortable) {
      return filteredData || [];
    }

    const col = columns.find(c => c.key === sortKey);
    if (!col || col.sortable === false || col.key === 'actions') {
      return filteredData;
    }

    return [...filteredData].sort((a, b) => {
      const valA = typeof col.sortValue === 'function' ? col.sortValue(a) : a[sortKey];
      const valB = typeof col.sortValue === 'function' ? col.sortValue(b) : b[sortKey];

      const cmp = naturalCompare(valA, valB);
      return sortDir === 'desc' ? -cmp : cmp;
    });
  }, [filteredData, sortKey, sortDir, columns, sortable, isServerDriven]);

  const activePage = isServerDriven ? serverPage : currentPage;
  const activeTotalPages = isServerDriven 
    ? (Math.ceil(totalCount / pageSize) || 1)
    : (Math.ceil(sortedData.length / pageSize) || 1);
  const activeTotalCount = isServerDriven ? totalCount : sortedData.length;
  
  const startIndex = (activePage - 1) * pageSize;
  const paginatedData = isServerDriven 
    ? sortedData 
    : sortedData.slice(startIndex, startIndex + pageSize);

  const handlePageChange = (newPage) => {
    if (isServerDriven && onPageChange) {
      if (newPage !== activePage && !loading) {
        onPageChange(newPage);
      }
    } else {
      setCurrentPage(newPage);
    }
  };

  useEffect(() => {
    if (!infiniteScroll) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && activePage < activeTotalPages && !loading) {
          handlePageChange(activePage + 1);
        }
      },
      { threshold: 0.1, rootMargin: '200px' }
    );
    if (observerRef.current) {
      observer.observe(observerRef.current);
    }
    return () => observer.disconnect();
  }, [infiniteScroll, activePage, activeTotalPages, loading, onPageChange]);

  const currentSortCol = columns.find(c => c.key === sortKey);

  return (
    <div className="data-table-wrapper">
      {/* Table Toolbar: Search + Sort controls */}
      {(searchKey || onSearchChange || (sortable && showSortToolbar && sortableColumns.length > 0)) && (
        <div className="data-table-toolbar">
          {(searchKey || onSearchChange) ? (
            <div style={{ flex: '1 1 200px', maxWidth: '320px', position: 'relative' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Search by ID, name, email..."
                value={currentSearchTerm || ''}
                onChange={handleSearch}
                aria-label="Search table data"
                style={{ paddingRight: (isSearching || currentSearchTerm) ? '2.2rem' : '0.8rem' }}
              />
              {isSearching && (
                <span className="spinner" style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', width: '14px', height: '14px', borderWidth: '2px' }} />
              )}
              {!isSearching && currentSearchTerm && (
                <button
                  type="button"
                  onClick={() => handleSearch({ target: { value: '' } })}
                  style={{ position: 'absolute', right: '0.5rem', top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: '1.1rem', lineHeight: 1, padding: '0 0.25rem' }}
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}
            </div>
          ) : <div />}

          {sortable && showSortToolbar && sortableColumns.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap', marginLeft: 'auto' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
                Sort by:
              </span>
              <select
                className="form-input"
                style={{
                  padding: '0.35rem 0.65rem',
                  fontSize: '0.82rem',
                  width: 'auto',
                  minWidth: '130px',
                  cursor: 'pointer'
                }}
                value={sortKey || ''}
                onChange={(e) => handleSortKeySelect(e.target.value)}
                aria-label="Select column to sort"
              >
                {sortableColumns.map(c => (
                  <option key={c.key} value={c.key}>
                    {c.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={toggleSortDir}
                title={`Currently ${sortDir === 'asc' ? 'Ascending (A→Z, 0→9)' : 'Descending (Z→A, 9→0)'}. Click to reverse.`}
                style={{
                  padding: '0.35rem 0.65rem',
                  fontSize: '0.8rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  fontWeight: 600
                }}
                aria-label="Toggle sort direction"
              >
                <span>{sortDir === 'asc' ? '▲ Asc' : '▼ Desc'}</span>
              </button>

              {currentSortCol && (
                <span 
                  className="badge badge-low" 
                  style={{ 
                    fontSize: '0.75rem', 
                    padding: '0.2rem 0.5rem',
                    fontFamily: 'var(--font-mono, monospace)'
                  }}
                  title="Active sort column"
                >
                  {currentSortCol.label} ({sortDir.toUpperCase()})
                </span>
              )}
            </div>
          )}
        </div>
      )}
      
      {sortedData.length === 0 ? (
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
                  {columns.map((col) => {
                    const isColSortable = sortable && col.sortable !== false && col.key !== 'actions';
                    const isCurrent = sortKey === col.key;
                    return (
                      <th 
                        key={col.key}
                        className={`${isColSortable ? 'sortable-header' : ''} ${isCurrent ? 'sort-active' : ''}`}
                        onClick={() => isColSortable && handleColumnSort(col.key)}
                        style={{
                          cursor: isColSortable ? 'pointer' : 'default',
                          userSelect: 'none',
                          ...(col.headerStyle || {})
                        }}
                        title={
                          isColSortable 
                            ? `Sort by ${col.label} (${isCurrent && sortDir === 'asc' ? 'switch to descending' : 'ascending'})` 
                            : undefined
                        }
                        aria-sort={isCurrent ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined}
                      >
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', width: '100%', justifyContent: 'space-between' }}>
                          <span>{col.label}</span>
                          {isColSortable && (
                            <span 
                              style={{ 
                                fontSize: '0.75rem', 
                                opacity: isCurrent ? 1 : 0.25,
                                color: isCurrent ? 'var(--color-primary)' : 'inherit',
                                display: 'inline-flex',
                                alignItems: 'center',
                                minWidth: '14px',
                                fontWeight: 'bold'
                              }}
                            >
                              {isCurrent ? (sortDir === 'asc' ? '▲' : '▼') : '⇅'}
                            </span>
                          )}
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {paginatedData.map((row, i) => (
                  <tr 
                    key={row.id || i} 
                    onClick={() => onRowClick && onRowClick(row)} 
                    style={{ cursor: onRowClick ? 'pointer' : 'default' }}
                  >
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
              <div ref={observerRef} style={{ padding: '1.25rem', textAlign: 'center', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem' }}>
                {loading ? (
                  <>
                    <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
                    <span style={{ fontSize: '0.85rem' }}>Loading more...</span>
                  </>
                ) : activePage < activeTotalPages ? (
                  <span style={{ fontSize: '0.85rem', opacity: 0.7 }}>Scroll down to load more...</span>
                ) : (
                  <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>All {activeTotalCount.toLocaleString()} entries loaded</span>
                )}
              </div>
            )}
          </div>
          
          {!infiniteScroll && activeTotalPages > 1 && (
            <div className="pagination-controls" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
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
