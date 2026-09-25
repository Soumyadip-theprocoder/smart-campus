import { useState, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';
import { Toaster } from 'react-hot-toast';

const LoginPage = lazy(() => import('./features/auth/LoginPage'));
const AdminDashboard = lazy(() => import('./features/dashboard/AdminDashboard'));
const AnalyticsDashboard = lazy(() => import('./features/dashboard/AnalyticsDashboard'));
const StudentDashboard = lazy(() => import('./features/dashboard/StudentDashboard'));
const AttendancePage = lazy(() => import('./features/attendance/AttendancePage'));
const TimetablePage = lazy(() => import('./features/scheduler/TimetablePage'));
const ManageTimetablePage = lazy(() => import('./features/scheduler/ManageTimetablePage'));
const NoticeDashboard = lazy(() => import('./features/communication/NoticeDashboard'));
const SubjectsPage = lazy(() => import('./features/scheduler/SubjectsPage'));
const FacultyPage = lazy(() => import('./features/scheduler/FacultyPage'));
const RoomsPage = lazy(() => import('./features/scheduler/RoomsPage'));
const StudentAttendancePage = lazy(() => import('./features/attendance/StudentAttendancePage'));
const StudentClassAttendancePage = lazy(() => import('./features/attendance/StudentClassAttendancePage'));
const FacultyDashboard = lazy(() => import('./features/dashboard/FacultyDashboard'));
const FacultySubjectsPage = lazy(() => import('./features/dashboard/FacultySubjectsPage'));

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

function RoleRedirect() {
  const { user } = useAuth();
  if (user?.role === 'student') return <Navigate to="/student" replace />;
  if (user?.role === 'faculty') return <Navigate to="/faculty" replace />;
  return <Navigate to="/admin" replace />;
}

function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <Suspense fallback={<div className="loading-spinner"><div className="spinner"></div></div>}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Suspense>
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
        <Suspense fallback={<div className="loading-spinner"><div className="spinner"></div></div>}>
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
              path="/admin/analytics"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AnalyticsDashboard />
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
            <Route path="/login" element={<RoleRedirect />} />
            <Route path="/" element={<RoleRedirect />} />
            <Route path="*" element={<RoleRedirect />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <AuthProvider>
          <Toaster 
            position="top-right" 
            toastOptions={{ 
              style: { 
                background: 'var(--color-bg-secondary)', 
                color: 'var(--color-text)', 
                border: '1px solid rgba(255,255,255,0.1)' 
              } 
            }} 
          />
          <AppLayout />
        </AuthProvider>
      </ErrorBoundary>
    </BrowserRouter>
  );
}
