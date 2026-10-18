import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../api/axios';

const TaskProgressContext = createContext(null);

export const useTaskProgress = () => {
  const context = useContext(TaskProgressContext);
  if (!context) {
    throw new Error('useTaskProgress must be used within a TaskProgressProvider');
  }
  return context;
};

export const TaskProgressProvider = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [activeTask, setActiveTask] = useState(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [confirmingCancel, setConfirmingCancel] = useState(false);

  const pollIntervalRef = useRef(null);
  const tickerIntervalRef = useRef(null);
  const cancelConfirmTimerRef = useRef(null);
  const targetPercentRef = useRef(5);

  const formatSeconds = (sec) => {
    if (!sec || isNaN(sec) || sec <= 0) return '00:00';
    const s = Math.round(sec);
    if (s >= 3600) {
      const h = Math.floor(s / 3600);
      const m = Math.floor((s % 3600) / 60);
      const rem = s % 60;
      return `${h}:${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
    }
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
  };

  const formatDurationDisplay = (sec) => {
    if (!sec || isNaN(sec) || sec <= 0) return '0s';
    const s = Math.round(sec);
    if (s < 60) return `${s}s`;
    if (s >= 3600) {
      const h = Math.floor(s / 3600);
      const m = Math.floor((s % 3600) / 60);
      return m ? `${h}h ${m}m` : `${h}h`;
    }
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return rem ? `${m}m ${rem}s` : `${m}m`;
  };

  // Second-by-second live clock ticker to guarantee smooth countdown and advancing progress
  useEffect(() => {
    const isRunning = activeTask && (activeTask.status === 'running' || activeTask.status === 'queued' || activeTask.status === 'processing');

    if (isRunning) {
      if (!tickerIntervalRef.current) {
        tickerIntervalRef.current = setInterval(() => {
          setActiveTask(prev => {
            if (!prev) return null;
            if (prev.status !== 'running' && prev.status !== 'queued' && prev.status !== 'processing') {
              return prev;
            }

            const nextElapsed = (prev.elapsedSeconds || 0) + 1;
            const nextEta = Math.max(1, (prev.etaRemainingSeconds || 5) - 1);
            
            // Creep percent forward smoothly towards targetPercent
            let currentPct = prev.percent || 5;
            const target = targetPercentRef.current || 5;
            if (currentPct < target) {
              currentPct = Math.min(target, currentPct + 0.5);
            } else if (currentPct < 94) {
              // Gentle organic drift during long solver phases
              currentPct = Math.min(94, currentPct + 0.15);
            }

            return {
              ...prev,
              elapsedSeconds: nextElapsed,
              etaRemainingSeconds: nextEta,
              percent: Math.round(currentPct * 10) / 10,
            };
          });
        }, 1000);
      }
    } else {
      if (tickerIntervalRef.current) {
        clearInterval(tickerIntervalRef.current);
        tickerIntervalRef.current = null;
      }
    }

    return () => {
      if (tickerIntervalRef.current) {
        clearInterval(tickerIntervalRef.current);
        tickerIntervalRef.current = null;
      }
    };
  }, [activeTask?.status]);

  // Network polling loop
  const pollTask = async (taskId) => {
    try {
      const res = await api.get(`/api/scheduler/task-status/${taskId}/`);
      const data = res.data;

      if (data.progress) {
        const prog = data.progress;
        if (prog.percent) {
          targetPercentRef.current = prog.percent;
        }

        setActiveTask(prev => ({
          ...prev,
          taskId,
          status: data.status,
          percent: prog.percent !== undefined ? prog.percent : (prev?.percent || 5),
          currentWave: prog.current_wave || prev?.currentWave || 0,
          totalWaves: prog.total_waves || prev?.totalWaves || 1,
          currentWaveName: prog.current_wave_name || prev?.currentWaveName || 'Processing...',
          sessionsScheduled: prog.sessions_scheduled !== undefined ? prog.sessions_scheduled : (prev?.sessionsScheduled || 0),
          elapsedSeconds: prog.elapsed_seconds !== undefined ? prog.elapsed_seconds : (prev?.elapsedSeconds || 0),
          etaRemainingSeconds: prog.eta_remaining_seconds !== undefined ? prog.eta_remaining_seconds : (prev?.etaRemainingSeconds || 5),
          scopeLabel: prog.scope_label || prev?.scopeLabel || 'Timetable Generator',
          scopeType: prog.scope_type || prev?.scopeType || 'department',
        }));
      }

      if (data.status === 'completed') {
        const resData = data.result || {};
        const isSuccess = resData.success !== false;

        setActiveTask(prev => ({
          ...prev,
          status: isSuccess ? 'completed' : 'failed',
          percent: 100,
          etaRemainingSeconds: 0,
          currentWaveName: isSuccess ? 'All schedules co-scheduled and committed!' : (resData.error || 'Solver failed'),
          result: resData,
          error: isSuccess ? null : (resData.error || 'Solver could not find solution'),
        }));

        localStorage.removeItem('smartcampus_active_task_id');
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

        if (isSuccess) {
          const unscheduledCount = resData.unscheduled_waves?.length || 0;
          const sessionCount = resData.count || 0;
          const msg = unscheduledCount > 0
            ? `🎉 Draft saved with ${sessionCount} sessions (${unscheduledCount} conflict cohorts skipped)`
            : `🎉 Timetable draft generated with ${sessionCount} sessions!`;

          toast.success(
            (t) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span>{msg}</span>
                <button
                  className="btn btn-sm btn-primary"
                  style={{ padding: '0.2rem 0.6rem', fontSize: '0.78rem' }}
                  onClick={() => {
                    toast.dismiss(t.id);
                    goToTimetable(resData.version_id, {
                      scopeType: resData.scope_type || activeTask?.scopeType,
                      blockName: activeTask?.blockName,
                      deptId: activeTask?.departmentId,
                    });
                  }}
                >
                  View Routine ↗
                </button>
              </div>
            ),
            { duration: 9000 }
          );

          // Dispatch window event so TimetablePage can reload entries if open
          window.dispatchEvent(new CustomEvent('smartcampus:timetable-generated', { detail: resData }));
        } else {
          toast.error(`Generation failed: ${resData.error || 'Conflict detected'}`);
        }
      } else if (data.status === 'failed') {
        setActiveTask(prev => ({
          ...prev,
          status: 'failed',
          error: data.error || 'Execution failed',
        }));
        localStorage.removeItem('smartcampus_active_task_id');
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        toast.error(`Generation failed: ${data.error || 'Unknown error'}`);
      } else if (data.status === 'cancelled') {
        setActiveTask(prev => ({
          ...prev,
          status: 'cancelled',
          etaRemainingSeconds: 0,
          currentWaveName: 'Generation cancelled by user',
          error: data.error || 'Generation was cancelled',
        }));
        localStorage.removeItem('smartcampus_active_task_id');
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        toast('Timetable generation cancelled', { icon: '🛑' });
      }
    } catch (err) {
      console.warn('Waiting for scheduler task telemetry...', err);
    }
  };

  // Start polling
  const startPolling = (taskId) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    pollTask(taskId);
    pollIntervalRef.current = setInterval(() => pollTask(taskId), 1500);
  };

  // Check active tasks on mount or route transition
  useEffect(() => {
    const savedTaskId = localStorage.getItem('smartcampus_active_task_id');
    if (savedTaskId) {
      startPolling(savedTaskId);
    } else {
      // Query backend for any running task across the system
      api.get('/api/scheduler/active-task/')
        .then(res => {
          if (res.data?.has_active_task && res.data?.task_id) {
            localStorage.setItem('smartcampus_active_task_id', res.data.task_id);
            startPolling(res.data.task_id);
          }
        })
        .catch(() => {});
    }

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const startTracking = (taskId, options = {}) => {
    const {
      initialEta = 10,
      scopeLabel = 'Timetable Generator',
      scopeType = 'department',
      blockName = null,
      departmentId = null,
    } = options;
    localStorage.setItem('smartcampus_active_task_id', taskId);
    targetPercentRef.current = 5;

    setActiveTask({
      taskId,
      status: 'running',
      percent: 5,
      elapsedSeconds: 0,
      etaRemainingSeconds: initialEta,
      currentWave: 0,
      totalWaves: 1,
      currentWaveName: 'Submitting configuration to solver cluster...',
      sessionsScheduled: 0,
      scopeLabel,
      scopeType,
      blockName,
      departmentId,
      result: null,
      error: null,
    });

    startPolling(taskId);
  };

  const goToTimetable = (targetVersionId = null, targetScope = null) => {
    setShowDetailModal(false);
    const version = targetVersionId || activeTask?.result?.version_id;
    const scopeType = targetScope?.scopeType || activeTask?.result?.scope_type || activeTask?.scopeType;
    const blockName = targetScope?.blockName || activeTask?.blockName;
    const deptId = targetScope?.deptId || activeTask?.departmentId;

    const params = new URLSearchParams();
    if (version) params.set('version', version);
    if (scopeType) params.set('scope', scopeType);
    if (blockName) params.set('block', blockName);
    if (deptId) params.set('dept', deptId);

    const query = params.toString() ? `?${params.toString()}` : '';

    if (location.pathname === '/timetable') {
      window.dispatchEvent(new CustomEvent('smartcampus:switch-timetable-view', {
        detail: {
          versionId: version,
          scopeType,
          blockName,
          deptId,
        }
      }));
      setTimeout(() => {
        const el = document.getElementById('timetable-grid-section');
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          window.scrollTo({ top: 320, behavior: 'smooth' });
        }
      }, 100);
    } else {
      navigate(`/timetable${query}`);
    }
  };

  const dismissTask = () => {
    if (cancelConfirmTimerRef.current) clearTimeout(cancelConfirmTimerRef.current);
    setConfirmingCancel(false);
    localStorage.removeItem('smartcampus_active_task_id');
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setActiveTask(null);
    setShowDetailModal(false);
  };

  const cancelTask = async (taskIdToCancel, force = false) => {
    const id = taskIdToCancel || activeTask?.taskId;
    if (!id) return;

    if (!force && !confirmingCancel) {
      setConfirmingCancel(true);
      if (cancelConfirmTimerRef.current) clearTimeout(cancelConfirmTimerRef.current);
      cancelConfirmTimerRef.current = setTimeout(() => {
        setConfirmingCancel(false);
      }, 4000);
      return;
    }

    if (cancelConfirmTimerRef.current) {
      clearTimeout(cancelConfirmTimerRef.current);
      cancelConfirmTimerRef.current = null;
    }
    setConfirmingCancel(false);

    try {
      setIsCancelling(true);
      setActiveTask(prev => prev ? ({
        ...prev,
        status: 'cancelling',
        currentWaveName: 'Cancelling timetable generation...',
        etaRemainingSeconds: 0,
      }) : null);

      await api.post(`/api/scheduler/task-cancel/${id}/`);
      toast('Cancelling timetable generation...', { icon: '🛑' });

      setActiveTask(prev => prev ? ({
        ...prev,
        status: 'cancelled',
        currentWaveName: 'Generation cancelled by user',
        etaRemainingSeconds: 0,
      }) : null);

      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      localStorage.removeItem('smartcampus_active_task_id');
      toast.success('Timetable generation cancelled.');
    } catch (err) {
      console.error('Failed to cancel task:', err);
      toast.error(err.response?.data?.error || 'Failed to cancel generation.');
    } finally {
      setIsCancelling(false);
    }
  };

  const isGenerating = activeTask && (
    activeTask.status === 'running' ||
    activeTask.status === 'queued' ||
    activeTask.status === 'processing' ||
    activeTask.status === 'cancelling'
  );

  return (
    <TaskProgressContext.Provider
      value={{
        activeTask,
        isGenerating,
        isCancelling,
        confirmingCancel,
        setConfirmingCancel,
        isMinimized,
        setIsMinimized,
        showDetailModal,
        setShowDetailModal,
        startTracking,
        dismissTask,
        cancelTask,
        goToTimetable,
        formatSeconds,
        formatDurationDisplay,
      }}
    >
      {children}

      {/* ── Global Floating Progress Pill (Persistent Across All Pages) ── */}
      {isGenerating && (
        <div
          className="global-floating-progress-pill animate-fade-in-up"
          style={{
            position: 'fixed',
            bottom: '1.5rem',
            right: '1.5rem',
            zIndex: 99999,
            display: 'flex',
            alignItems: 'center',
            gap: '0.85rem',
            padding: '0.75rem 1.15rem',
            background: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(59, 130, 246, 0.45)',
            borderRadius: '30px',
            boxShadow: '0 12px 35px rgba(0, 0, 0, 0.6), 0 0 20px rgba(59, 130, 246, 0.25)',
            color: '#fff',
            cursor: 'pointer',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            minWidth: '320px',
            maxWidth: '450px',
          }}
          onClick={() => setShowDetailModal(true)}
          title="Click to view live generator details"
        >
          {/* Circular Percentage Spinner */}
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div
              className="spinner"
              style={{
                width: '24px',
                height: '24px',
                borderWidth: '2.5px',
                borderColor: 'rgba(59, 130, 246, 0.3)',
                borderTopColor: '#3b82f6',
              }}
            />
            <span style={{ position: 'absolute', fontSize: '0.62rem', fontWeight: 800 }}>
              {Math.round(activeTask.percent || 5)}%
            </span>
          </div>

          {/* Details & Live Countdown */}
          <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.84rem', fontWeight: 700, color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {activeTask.scopeLabel || 'Timetable Generator'}
              </span>
              <span style={{ fontSize: '0.76rem', fontWeight: 700, color: 'var(--color-accent-emerald, #10b981)', whiteSpace: 'nowrap' }}>
                ~{formatSeconds(activeTask.etaRemainingSeconds)}
              </span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: '0.1rem' }}>
              {activeTask.totalWaves > 1
                ? `Wave ${activeTask.currentWave || 0}/${activeTask.totalWaves} · ${activeTask.currentWaveName || 'Processing...'}`
                : (activeTask.currentWaveName || 'Solving timetable...')}
            </div>
          </div>

          {/* Action Buttons: In-Place View and Direct Timetable Link */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              style={{
                padding: '0.25rem 0.55rem',
                fontSize: '0.72rem',
                borderRadius: '14px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                background: 'rgba(255, 255, 255, 0.08)',
              }}
              onClick={(e) => {
                e.stopPropagation();
                setShowDetailModal(true);
              }}
            >
              🔍 Details
            </button>
            <button
              type="button"
              className="btn btn-sm btn-danger"
              style={{
                padding: '0.25rem 0.55rem',
                fontSize: '0.72rem',
                borderRadius: '14px',
                background: confirmingCancel ? 'rgba(239, 68, 68, 0.4)' : 'rgba(239, 68, 68, 0.2)',
                border: confirmingCancel ? '1px solid #ef4444' : '1px solid rgba(239, 68, 68, 0.45)',
                color: confirmingCancel ? '#ffffff' : '#f87171',
                fontWeight: confirmingCancel ? 700 : 500,
                transition: 'all 0.2s ease',
              }}
              onClick={(e) => {
                e.stopPropagation();
                cancelTask(activeTask.taskId);
              }}
              title={confirmingCancel ? "Click again to confirm cancellation" : "Cancel timetable generation"}
              disabled={isCancelling}
            >
              {isCancelling ? '...' : confirmingCancel ? '⚠️ Confirm?' : '🛑 Cancel'}
            </button>
            {location.pathname !== '/timetable' ? (
              <button
                type="button"
                className="btn btn-sm btn-primary"
                style={{
                  padding: '0.25rem 0.55rem',
                  fontSize: '0.72rem',
                  borderRadius: '14px',
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  goToTimetable(activeTask?.result?.version_id, {
                    scopeType: activeTask?.result?.scope_type || activeTask?.scopeType,
                    blockName: activeTask?.blockName,
                    deptId: activeTask?.departmentId,
                  });
                }}
              >
                ↗ View
              </button>
            ) : (
              <button
                type="button"
                className="btn btn-sm btn-primary"
                style={{
                  padding: '0.25rem 0.55rem',
                  fontSize: '0.72rem',
                  borderRadius: '14px',
                  background: 'rgba(59, 130, 246, 0.25)',
                  border: '1px solid rgba(59, 130, 246, 0.5)',
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  const el = document.getElementById('timetable-grid-section');
                  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  else window.scrollTo({ top: 320, behavior: 'smooth' });
                }}
                title="Scroll to timetable grid"
              >
                ↓ Grid
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── Global In-Place Detail Progress Modal (Available on Any Page) ── */}
      {showDetailModal && activeTask && (
        <div
          className="modal-overlay"
          style={{ zIndex: 100000 }}
          onClick={() => setShowDetailModal(false)}
        >
          <div
            className="modal-content glass-card animate-fade-in-up"
            style={{
              maxWidth: '520px',
              width: '90%',
              padding: '1.75rem',
              background: 'linear-gradient(145deg, rgba(30, 41, 59, 0.98), rgba(15, 23, 42, 0.98))',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              borderRadius: '16px',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 25px rgba(59, 130, 246, 0.25)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  {activeTask.status === 'completed' ? (
                    <span style={{ fontSize: '1.25rem' }}>🎉</span>
                  ) : activeTask.status === 'failed' ? (
                    <span style={{ fontSize: '1.25rem' }}>❌</span>
                  ) : activeTask.status === 'cancelled' ? (
                    <span style={{ fontSize: '1.25rem' }}>🛑</span>
                  ) : (
                    <div
                      className="spinner"
                      style={{
                        width: '20px',
                        height: '20px',
                        borderWidth: '2.5px',
                        borderColor: 'rgba(59, 130, 246, 0.3)',
                        borderTopColor: '#3b82f6',
                      }}
                    />
                  )}
                  <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#fff' }}>
                    {activeTask.status === 'completed'
                      ? '🎉 Generation Complete'
                      : activeTask.status === 'failed'
                        ? '❌ Generation Failed'
                        : activeTask.status === 'cancelled'
                          ? '🛑 Generation Cancelled'
                          : activeTask.status === 'cancelling'
                            ? '⏳ Cancelling Generation...'
                            : `Generating Timetable (${Math.round(activeTask.percent || 5)}%)`}
                  </h3>
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                  {activeTask.scopeLabel || 'Campus Timetable Sandbox'}
                </div>
              </div>

              <button
                type="button"
                className="btn btn-sm btn-secondary"
                style={{ borderRadius: '50%', width: '32px', height: '32px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                onClick={() => setShowDetailModal(false)}
              >
                ✕
              </button>
            </div>

            {/* Progress Bar with smooth animation */}
            <div style={{
              width: '100%',
              height: '12px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              overflow: 'hidden',
              marginBottom: '1rem',
            }}>
              <div style={{
                height: '100%',
                width: `${Math.max(5, Math.min(100, activeTask.percent || 5))}%`,
                background: activeTask.status === 'failed'
                  ? '#ef4444'
                  : activeTask.status === 'cancelled'
                    ? '#f59e0b'
                    : 'linear-gradient(90deg, #3b82f6, #8b5cf6, #10b981)',
                borderRadius: '6px',
                transition: 'width 0.4s ease-out',
              }} />
            </div>

            {/* Current Wave description */}
            <div style={{
              fontSize: '0.86rem',
              fontWeight: 600,
              color: activeTask.status === 'cancelled' ? '#fcd34d' : 'var(--color-accent-blue-light, #93c5fd)',
              marginBottom: '1.25rem',
              padding: '0.65rem 0.85rem',
              background: activeTask.status === 'cancelled' ? 'rgba(245, 158, 11, 0.12)' : 'rgba(59, 130, 246, 0.1)',
              borderRadius: '8px',
              border: activeTask.status === 'cancelled' ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid rgba(59, 130, 246, 0.25)',
            }}>
              {activeTask.status === 'cancelled'
                ? `🛑 ${activeTask.currentWaveName || 'Generation cancelled by user'}`
                : activeTask.totalWaves > 1
                  ? `🌊 Wave ${activeTask.currentWave || 0} of ${activeTask.totalWaves}: ${activeTask.currentWaveName || 'Processing...'}`
                  : `⚙️ ${activeTask.currentWaveName || 'Solving constraint graph...'}`}
            </div>

            {/* Telemetry Grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '0.75rem',
              padding: '0.85rem',
              background: 'rgba(0, 0, 0, 0.3)',
              borderRadius: '10px',
              textAlign: 'center',
              marginBottom: '1.5rem',
            }}>
              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>Elapsed Time</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: '#fff', marginTop: '0.2rem' }}>
                  {formatSeconds(activeTask.elapsedSeconds)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>Remaining ETA</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-accent-emerald, #10b981)', marginTop: '0.2rem' }}>
                  {activeTask.status === 'completed' || activeTask.status === 'cancelled' ? '00:00' : `~${formatSeconds(activeTask.etaRemainingSeconds)}`}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>Sessions Placed</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-accent-blue-light, #93c5fd)', marginTop: '0.2rem' }}>
                  {activeTask.sessionsScheduled || 0}
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {isGenerating && (
                  <button
                    type="button"
                    className="btn btn-danger"
                    id="btn-cancel-generation-modal"
                    disabled={isCancelling}
                    onClick={() => cancelTask(activeTask.taskId)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      background: confirmingCancel ? 'rgba(239, 68, 68, 0.35)' : 'rgba(239, 68, 68, 0.18)',
                      color: confirmingCancel ? '#ffffff' : '#f87171',
                      border: confirmingCancel ? '1px solid #ef4444' : '1px solid rgba(239, 68, 68, 0.45)',
                      padding: '0.45rem 0.95rem',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      borderRadius: '8px',
                      cursor: isCancelling ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: confirmingCancel ? '0 0 14px rgba(239, 68, 68, 0.45)' : 'none',
                    }}
                  >
                    {isCancelling ? (
                      <>
                        <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px', borderColor: 'rgba(248, 113, 113, 0.3)', borderTopColor: '#f87171' }} />
                        Cancelling...
                      </>
                    ) : confirmingCancel ? (
                      <>⚠️ Confirm Cancel (Click again)</>
                    ) : (
                      <>🛑 Cancel Generation</>
                    )}
                  </button>
                )}
                {confirmingCancel && !isCancelling && (
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => setConfirmingCancel(false)}
                    style={{ fontSize: '0.78rem', padding: '0.45rem 0.75rem', borderRadius: '8px' }}
                  >
                    Keep Generating
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    if (activeTask.status === 'completed' || activeTask.status === 'failed' || activeTask.status === 'cancelled') {
                      dismissTask();
                    } else {
                      setShowDetailModal(false);
                    }
                  }}
                >
                  {activeTask.status === 'completed' || activeTask.status === 'failed' || activeTask.status === 'cancelled'
                    ? 'Dismiss'
                    : 'Minimize to Pill ↘'}
                </button>
                {activeTask.status !== 'cancelled' && activeTask.status !== 'failed' && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      goToTimetable(activeTask?.result?.version_id, {
                        scopeType: activeTask?.result?.scope_type || activeTask?.scopeType,
                        blockName: activeTask?.blockName,
                        deptId: activeTask?.departmentId,
                      });
                    }}
                  >
                    {activeTask.status === 'completed'
                      ? 'View Generated Timetable ↗'
                      : location.pathname === '/timetable'
                        ? 'Scroll to Timetable Grid ↓'
                        : 'Go to Timetable View ↗'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </TaskProgressContext.Provider>
  );
};
