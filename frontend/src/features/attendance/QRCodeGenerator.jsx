import React from 'react';
import { QRCodeSVG } from 'qrcode.react';

const QRCodeGenerator = ({ sessionData }) => {
  // We'll stringify the session data (like subject ID, date, secret token) to encode in the QR
  const qrValue = typeof sessionData === 'string' ? sessionData : JSON.stringify(sessionData);

  return (
    <div className="qr-generator-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem', background: 'white', borderRadius: '12px' }}>
      <QRCodeSVG 
        value={qrValue} 
        size={256}
        bgColor={"#ffffff"}
        fgColor={"#000000"}
        level={"H"}
        includeMargin={true}
      />
      <p style={{ marginTop: '1rem', color: '#64748b', fontSize: '0.9rem', textAlign: 'center' }}>
        Students can scan this QR code using their Smart Campus app to mark attendance.
      </p>
    </div>
  );
};

export default QRCodeGenerator;
