import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import api from '../../api/axios';

const QRCodeGenerator = ({ sessionData }) => {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sessionData?.subject_id) return;

    const fetchToken = async () => {
      try {
        const res = await api.get(`/api/attendance/generate-qr-token/?subject_id=${sessionData.subject_id}`);
        setToken(res.data.token);
        setError("");
      } catch (err) {
        console.error("Failed to fetch QR token:", err);
        setError("Failed to generate secure QR code");
      }
    };

    fetchToken();
    // Refresh token every 10 seconds to keep it valid (expires in 15s on backend)
    const interval = setInterval(fetchToken, 10000);
    return () => clearInterval(interval);
  }, [sessionData]);

  if (error) {
    return <div style={{ color: 'red', textAlign: 'center', padding: '2rem' }}>{error}</div>;
  }

  if (!token) {
    return <div style={{ textAlign: 'center', padding: '2rem' }}>Generating secure QR code...</div>;
  }

  return (
    <div className="qr-generator-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem', background: 'white', borderRadius: '12px' }}>
      <QRCodeSVG 
        value={token} 
        size={256}
        bgColor={"#ffffff"}
        fgColor={"#000000"}
        level={"H"}
        includeMargin={true}
      />
      <p style={{ marginTop: '1rem', color: '#64748b', fontSize: '0.9rem', textAlign: 'center' }}>
        Scan this QR code using the Smart Campus app.
        <br/><span style={{ fontSize: '0.8rem', color: 'var(--color-accent-emerald)' }}>Updates automatically for security</span>
      </p>
    </div>
  );
};

export default QRCodeGenerator;
