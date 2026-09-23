import React, { useEffect, useRef, useState } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';

const QRCodeScanner = ({ onScanSuccess }) => {
  const [error, setError] = useState(null);
  const scannerRef = useRef(null);

  useEffect(() => {
    // Create instance of the scanner
    const scanner = new Html5QrcodeScanner(
      "qr-reader",
      { fps: 10, qrbox: { width: 250, height: 250 } },
      /* verbose= */ false
    );

    // Render it and handle success/error
    scanner.render(
      (decodedText) => {
        onScanSuccess(decodedText);
        // We do not stop the scanner here, allowing continuous scans 
        // if the parent wants to handle multiple students.
      },
      (err) => {
        // We only want to log or handle real errors, not the constant 'not found' spam
        if (err && typeof err === 'string' && !err.includes('NotFound')) {
            console.warn(err);
        }
      }
    );

    // Save instance for cleanup
    scannerRef.current = scanner;

    // Cleanup on unmount
    return () => {
      if (scannerRef.current) {
        scannerRef.current.clear().catch(e => console.error("Failed to clear scanner", e));
      }
    };
  }, [onScanSuccess]);

  return (
    <div className="qr-scanner-container" style={{ width: '100%', maxWidth: '500px', margin: '0 auto' }}>
      <div id="qr-reader" style={{ width: '100%', border: 'none', borderRadius: '12px', overflow: 'hidden' }}></div>
      {error && <div className="login-error" style={{ marginTop: '1rem' }}>{error}</div>}
    </div>
  );
};

export default QRCodeScanner;
