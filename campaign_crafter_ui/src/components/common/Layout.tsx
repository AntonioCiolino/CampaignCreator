import React, { ReactNode, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ReactComponent as Logo } from '../../logo_cc.svg';
import './Layout.css';
import { useAuth } from '../../contexts/AuthContext';
import UserDropdownMenu from './UserDropdownMenu'; // Import the new component

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    if(isMobileMenuOpen) setIsMobileMenuOpen(false);
  };

  // Function to close mobile menu, can be passed to links if needed
  const closeMobileMenu = () => {
    if (isMobileMenuOpen) {
      setIsMobileMenuOpen(false);
    }
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <Link to="/" className="app-title-link" onClick={closeMobileMenu}>
          <Logo className="app-logo" title="Campaign Crafter Logo" />
          <h1>Campaign Crafter</h1>
        </Link>
        <button className="hamburger-menu" onClick={toggleMobileMenu} aria-label="Toggle navigation" aria-expanded={isMobileMenuOpen}>
          &#9776; {/* Hamburger icon */}
        </button>
        <nav className={`app-nav ${isMobileMenuOpen ? 'mobile-nav-active' : ''}`}>
          <ul className="nav-links-left"> {/* Wrapper for left-aligned links */}
            {token && user ? (
              <>
                {/* The "Dashboard" link is removed as per redundancy requirement */}
                {/* User settings and logout are now in UserDropdownMenu */}
                {user.is_superuser && (
                  <li><Link to="/users" onClick={closeMobileMenu}>User Management</Link></li>
                )}
                <li><Link to="/data-management" onClick={closeMobileMenu}>Data Management</Link></li>
                {/* Add other main navigation links here if any */}
              </>
            ) : (
              // Non-authenticated users might see some links here or just login
              <></>
            )}
          </ul>
          <div className="nav-links-right"> {/* Wrapper for right-aligned items */}
            {token && user ? (
              <UserDropdownMenu user={user} onLogout={handleLogout} />
            ) : (
              <ul> {/* Ensure login is also in a ul for consistent structure if needed */}
                <li><Link to="/login" onClick={closeMobileMenu}>Login</Link></li>
              </ul>
            )}
          </div>
        </nav>
      </header>
      <main className="app-main-content">
        {children}
      </main>
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} Campaign Crafter. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Layout;
