import { useAuth } from '../context/AuthContext';
import { HiOutlineMenuAlt2 } from 'react-icons/hi';
import { FiLogOut } from 'react-icons/fi';
import './Navbar.css';

export default function Navbar({ collapsed, onToggleSidebar, title }) {
  const { user, logout } = useAuth();

  const getInitials = (name) => {
    if (!name) return '?';
    const parts = name.split(' ');
    return parts.map(p => p[0]).join('').toUpperCase().slice(0, 2);
  };

  const fullName = user ? `${user.first_name} ${user.last_name}` : '';

  return (
    <nav className={`navbar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="navbar-left">
        <button
          className="navbar-toggle"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
          id="sidebar-toggle-btn"
        >
          <HiOutlineMenuAlt2 />
        </button>
        <span className="navbar-title">{title || 'Dashboard'}</span>
      </div>

      <div className="navbar-right">
        <div className="navbar-user" id="navbar-user-profile">
          <div className="navbar-avatar">
            {getInitials(fullName)}
          </div>
          <div className="navbar-user-info">
            <div className="navbar-user-name">{fullName}</div>
            <div className="navbar-user-role">{user?.role}</div>
          </div>
        </div>

        <button
          className="navbar-logout"
          onClick={logout}
          title="Logout"
          id="logout-btn"
        >
          <FiLogOut />
        </button>
      </div>
    </nav>
  );
}
