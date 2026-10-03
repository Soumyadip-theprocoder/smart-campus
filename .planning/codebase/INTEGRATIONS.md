# INTEGRATIONS

## Third-Party APIs and Services
- **Calendar Apps (Apple, Google, Outlook)**: Supported via 1-Click Calendar Sync (iCal `.ics` feed endpoint) exporting `RRULE` mapped classes and `EXDATE` blackout dates.
- None explicitly required via external API at this time, though the app relies on Docker container environments and is prepared for Render deployment.

## Internal Subsystems
- **Face Recognition Engine**: An internal service/module for extracting facial embeddings using OpenCV and potentially `face-recognition`/`dlib` (though heavy dependencies might be constrained by RAM in production).
- **QR Code Scanning**: Utilizes HTML5-QRCode and qrcode.react in the frontend for barcode/QR based operations.

## Webhooks
- Not identified in current scanning.
