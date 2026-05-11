import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import LoginPage from './features/auth/LoginPage';
import AdminDashboard from './features/dashboard/AdminDashboard';
import StudentDashboard from './features/dashboard/StudentDashboard';
import AttendancePage from './features/attendance/AttendancePage';
import TimetablePage from './features/scheduler/TimetablePage';
import ManageTimetablePage from './features/scheduler/ManageTimetablePage';
import NoticeDashboard from './features/communication/NoticeDashboard';
import SubjectsPage from './features/scheduler/SubjectsPage';
import FacultyPage from './features/scheduler/FacultyPage';
import RoomsPage from './features/scheduler/RoomsPage';
import StudentAttendancePage from './features/attendance/StudentAttendancePage';
import StudentClassAttendancePage from './features/attendance/StudentClassAttendancePage';
import FacultyDashboard from './features/dashboard/FacultyDashboard';
import FacultySubjectsPage from './features/dashboard/FacultySubjectsPage';

function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard
    if (user.role === 'admin') return <Navigate to="/admin" replace />;
    if (user.role === 'student') return <Navigate to="/student" replace />;
    if (user.role === 'faculty') return <Navigate to="/faculty" replace />;
    return <Navigate to="/timetable" replace />;
  }

  return children;
}

function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar collapsed={sidebarCollapsed} />
      <Navbar
        collapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <main className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <Routes>
          {/* Admin routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/courses"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <SubjectsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/faculty"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <FacultyPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/rooms"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <RoomsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/attendance"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AttendancePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/manage-timetable"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <ManageTimetablePage />
              </ProtectedRoute>
            }
          />

          {/* Student routes */}
          <Route
            path="/student"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <StudentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/attendance"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <StudentAttendancePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/class-attendance"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <StudentClassAttendancePage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/faculty"
            element={
              <ProtectedRoute allowedRoles={['faculty']}>
                <FacultyDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/faculty/subjects"
            element={
              <ProtectedRoute allowedRoles={['faculty']}>
                <FacultySubjectsPage />
              </ProtectedRoute>
            }
          />

          {/* Shared routes */}
          <Route
            path="/timetable"
            element={
              <ProtectedRoute>
                <TimetablePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notices"
            element={
              <ProtectedRoute>
                <NoticeDashboard />
              </ProtectedRoute>
            }
          />

          {/* Redirects */}
          <Route path="/login" element={<Navigate to="/admin" replace />} />
          <Route path="/" element={<Navigate to="/admin" replace />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </BrowserRouter>
  );
}
