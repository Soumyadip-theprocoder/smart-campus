import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  HiOutlineViewGrid,
  HiOutlineClipboardCheck,
  HiOutlineCalendar,
  HiOutlineSpeakerphone,
  HiOutlineUsers,
  HiOutlineAcademicCap,
} from 'react-icons/hi';
import { FiSettings } from 'react-icons/fi';
import './Sidebar.css';

export default function Sidebar({ collapsed }) {
  const { isAdmin, isStudent, isFaculty } = useAuth();

  const adminLinks = [
    { to: '/admin', icon: <HiOutlineViewGrid />, label: 'Dashboard', end: true },
    { to: '/admin/courses', icon: <HiOutlineAcademicCap />, label: 'Courses' },
    { to: '/admin/faculty', icon: <HiOutlineUsers />, label: 'Faculty' },
    { to: '/admin/rooms', icon: <HiOutlineViewGrid />, label: 'Rooms' },
    { to: '/timetable', icon: <HiOutlineCalendar />, label: 'Timetables' },
    { to: '/notices', icon: <HiOutlineSpeakerphone />, label: 'Notifications' },
  ];

  const studentLinks = [
    { to: '/student', icon: <HiOutlineViewGrid />, label: 'Dashboard', end: true },
    { to: '/timetable', icon: <HiOutlineCalendar />, label: 'Timetable' },
    { to: '/student/class-attendance', icon: <HiOutlineClipboardCheck />, label: 'Attendance' },
    { to: '/notices', icon: <HiOutlineSpeakerphone />, label: 'Notices' },
  ];

  const facultyLinks = [
    { to: '/faculty', icon: <HiOutlineViewGrid />, label: 'Dashboard', end: true },
    { to: '/timetable', icon: <HiOutlineCalendar />, label: 'Timetable' },
    { to: '/notices', icon: <HiOutlineSpeakerphone />, label: 'Notices' },
  ];

  let links = studentLinks;
  if (isAdmin) links = adminLinks;
  if (isFaculty) links = facultyLinks;

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-icon">🎓</div>
        <div className="brand-text">
          <div className="brand-name">Smart Campus</div>
          <div className="brand-subtitle">Management System</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-title">Main Menu</div>
        {links.map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'active' : ''}`
            }
            id={`nav-${link.label.toLowerCase().replace(/\s+/g, '-')}`}
          >
            <span className="link-icon">{link.icon}</span>
            <span className="link-text">{link.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
