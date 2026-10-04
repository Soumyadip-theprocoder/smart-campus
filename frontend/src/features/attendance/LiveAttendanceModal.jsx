import React, { useRef, useState, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';
import toast from 'react-hot-toast';
import api from '../../api/axios';
import { HiX, HiPlay, HiStop } from 'react-icons/hi';

const LiveAttendanceModal = ({ isOpen, onClose, subjectId, onSessionEnd }) => {
  const webcamRef = useRef(null);
  const canvasRef = useRef(null);
  
  const [sessionId, setSessionId] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const [recognizedStudents, setRecognizedStudents] = useState([]);
  const [unknownCount, setUnknownCount] = useState(0);

  // Start session on mount if subjectId is valid
  useEffect(() => {
    if (isOpen && subjectId) {
      startSession();
    }
    return () => {
      if (sessionId) {
        endSession();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, subjectId]);

  const startSession = async () => {
    try {
      const res = await api.post('/api/attendance/sessions/start/', { subject_id: subjectId });
      setSessionId(res.data.session_id);
      toast.success('Live Session Started!');
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed to start session');
      onClose();
    }
  };

  const endSession = async () => {
    if (sessionId) {
      setIsActive(false);
      try {
        await api.post(`/api/attendance/sessions/${sessionId}/end/`);
        toast.success('Session Ended.');
      } catch (e) {
        console.error(e);
      }
      setSessionId(null);
      if (onSessionEnd) onSessionEnd();
      onClose();
    }
  };

  const processFrame = useCallback(async () => {
    if (!isActive || !sessionId || !webcamRef.current) return;

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) return;

    try {
      const res = await api.post(`/api/attendance/sessions/${sessionId}/process-frame/`, {
        frame: imageSrc
      });

      const { recognized, unknown_count } = res.data;
      
      setUnknownCount(unknown_count);

      if (recognized.length > 0) {
        setRecognizedStudents(prev => {
          const newMap = new Map(prev.map(s => [s.student_id, s]));
          recognized.forEach(s => {
            newMap.set(s.student_id, s);
          });
          return Array.from(newMap.values());
        });
        
        // Draw boxes
        if (canvasRef.current && webcamRef.current.video) {
          const video = webcamRef.current.video;
          const canvas = canvasRef.current;
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          
          recognized.forEach(person => {
            const [top, right, bottom, left] = person.box;
            ctx.strokeStyle = '#10b981'; // Emerald
            ctx.lineWidth = 3;
            ctx.strokeRect(left, top, right - left, bottom - top);
            
            ctx.fillStyle = '#10b981';
            ctx.fillRect(left, bottom, right - left, 25);
            ctx.fillStyle = '#ffffff';
            ctx.font = '16px sans-serif';
            ctx.fillText(person.name, left + 5, bottom + 18);
          });
          
          // Clear boxes after a short delay
          setTimeout(() => {
            if (canvasRef.current) {
                const ctx2 = canvasRef.current.getContext('2d');
                ctx2.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            }
          }, 400);
        }
      }
    } catch (e) {
      console.error(e);
      // Optional: Stop on consecutive errors
    }
  }, [isActive, sessionId]);

  // Polling loop
  useEffect(() => {
    let interval;
    if (isActive) {
      interval = setInterval(processFrame, 500); // 2 FPS
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isActive, processFrame]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={{
        position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
        background: 'var(--color-bg-hover)', zIndex: 9999,
        display: 'flex', justifyContent: 'center', alignItems: 'center'
      }}>
        <div className="modal-content glass-card" style={{ padding: '2rem', maxWidth: '800px', width: '100%', position: 'relative' }}>
          <button 
            style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer' }}
            onClick={endSession}
          ><HiX /></button>
          
          <h2>Live Attendance Session</h2>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>Continuous Face Tracking Active.</p>

          <div style={{ display: 'flex', gap: '2rem' }}>
              <div style={{ flex: 1, position: 'relative', borderRadius: '12px', overflow: 'hidden', backgroundColor: '#000' }}>
                  <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    videoConstraints={{ facingMode: "user" }}
                    style={{ width: '100%', display: 'block' }}
                  />
                  <canvas 
                    ref={canvasRef}
                    style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
                  />
              </div>

              <div style={{ width: '250px', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ marginBottom: '1rem' }}>
                      <button 
                        className={`btn ${isActive ? 'btn-secondary' : 'btn-primary'}`} 
                        style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
                        onClick={() => setIsActive(!isActive)}
                        disabled={!sessionId}
                      >
                          {isActive ? <><HiStop /> Pause Tracker</> : <><HiPlay /> Start Tracker</>}
                      </button>
                  </div>
                  
                  <div style={{ background: 'var(--color-bg-glass)', padding: '1rem', borderRadius: '8px', flex: 1, overflowY: 'auto' }}>
                      <h4 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.5rem' }}>
                          Marked Present ({recognizedStudents.length})
                      </h4>
                      {unknownCount > 0 && (
                          <div style={{ color: 'var(--color-sunset)', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
                              ⚠️ {unknownCount} unknown face(s) in view
                          </div>
                      )}
                      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          {recognizedStudents.map(s => (
                              <li key={s.student_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                                  <span>✔️ {s.name}</span>
                              </li>
                          ))}
                      </ul>
                  </div>
              </div>
          </div>
        </div>
    </div>
  );
};

export default LiveAttendanceModal;
