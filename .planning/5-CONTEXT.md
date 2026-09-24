# Phase 5 Context: PDF Feature Parity

## 1. Face Data Registration
- **Webcam Image Processing**: The backend will process the captured webcam image **synchronously**. During the HTTP upload request, the backend will immediately extract the 128-d face encoding using OpenCV/face_recognition and return a success/failure response without deferring to a background worker.
- **Image Storage**: The raw image captured by the webcam will be **saved to the database** (using the existing `face_image` ImageField) along with the extracted encoding vector. This will serve as a visual reference for administrators.

## 2. Data Visualization & Reporting
- **Report Export Format**: 
  - **Administrators**: Will be able to download reports (e.g., attendance statistics, schedules) in **CSV** format for easy spreadsheet manipulation.
  - **Students**: Will have the option to download their specific reports/records in **PDF** format (suitable for formal, printable reports).
