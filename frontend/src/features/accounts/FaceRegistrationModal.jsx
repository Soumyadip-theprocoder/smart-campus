import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { HiX, HiCamera } from 'react-icons/hi';
import api from '../../api/axios';
import LocalErrorBoundary from '../../components/LocalErrorBoundary';
import './FaceRegistrationModal.css';

const FaceRegistrationModal = ({ isOpen, onClose, onSuccess, studentId }) => {
  const webcamRef = useRef(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [consentGiven, setConsentGiven] = useState(false);

  const capture = useCallback(async () => {
    if (!consentGiven) {
        setError('You must consent to biometric data processing.');
        return;
    }
    setIsCapturing(true);
    setError('');
    
    try {
      const imageSrc = webcamRef.current.getScreenshot();
      if (!imageSrc) {
        throw new Error("Could not capture image from webcam.");
      }

      // Convert base64 to Blob
      const res = await fetch(imageSrc);
      const blob = await res.blob();
      const file = new File([blob], 'face.jpg', { type: 'image/jpeg' });

      const formData = new FormData();
      formData.append('face_image', file);

      // Upload directly to backend
      const response = await api.post(`/api/auth/students/${studentId}/faces/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess(response.data.message || 'Face registered successfully!');
      
      // Notify parent to refresh user context
      setTimeout(() => {
        if (onSuccess) onSuccess();
        onClose();
        setIsCapturing(false);
        setSuccess('');
      }, 2000);
      
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to capture face.');
      setIsCapturing(false);
    }
  }, [webcamRef, onClose, onSuccess, consentGiven, studentId]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content glass-panel">
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          <HiX />
        </button>
        
        <h2>Register Face Data</h2>
        <p className="modal-subtitle">Please ensure your face is clearly visible in the frame.</p>
        
        <div className="consent-container" style={{ margin: '1rem 0', textAlign: 'left', fontSize: '0.9rem' }}>
            <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'start' }}>
                <input 
                    type="checkbox" 
                    checked={consentGiven} 
                    onChange={(e) => setConsentGiven(e.target.checked)} 
                    style={{ marginTop: '0.2rem' }}
                />
                <span>I consent to the collection and processing of my facial biometric data for the purpose of attendance marking, in accordance with the institution's privacy policy and the DPDP Act 2023. I understand I can request deletion at any time.</span>
            </label>
        </div>

        {error && <div className="alert error-alert">{error}</div>}
        {success && <div className="alert success-alert">{success}</div>}

        <div className="webcam-container">
          <LocalErrorBoundary>
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              className="webcam-video"
              videoConstraints={{
                width: 400,
                height: 400,
                facingMode: "user"
              }}
            />
            {isCapturing && (
              <div className="webcam-overlay">
                <div className="spinner"></div>
              </div>
            )}
          </LocalErrorBoundary>
        </div>

        <button 
          className="btn btn-primary capture-btn" 
          onClick={capture}
          disabled={isCapturing || success !== '' || !consentGiven}
        >
          <HiCamera className="btn-icon" />
          {isCapturing ? 'Processing...' : 'Capture'}
        </button>
      </div>
    </div>
  );
};

export default FaceRegistrationModal;
