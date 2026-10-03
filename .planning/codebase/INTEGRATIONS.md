# INTEGRATIONS

## Third-Party APIs and Services
- **Calendar Apps (Apple, Google, Outlook)**: Supported via 1-Click Calendar Sync (iCal `.ics` feed endpoint) exporting `RRULE` mapped classes and `EXDATE` blackout dates.
- **Exporting**: PDF exports are handled both via backend (`reportlab`) and frontend (`html2canvas`/`jspdf`).

## Internal Subsystems
- **Face Recognition Engine**: An internal service/module for extracting facial embeddings using OpenCV and potentially `face-recognition`/`dlib` (though heavy dependencies might be constrained by RAM in production).
- **QR Code Scanning**: Utilizes `html5-qrcode` and `qrcode.react` in the frontend for barcode/QR based operations.

## Webhooks
- Not identified in current scanning.
