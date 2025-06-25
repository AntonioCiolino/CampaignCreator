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

        {/* Hamburger menu button is now always controlling the main nav links */}
        <button
          className="hamburger-menu global-hamburger-menu" /* Added global class for distinct styling if needed */
          onClick={toggleMobileMenu}
          aria-label="Toggle navigation"
          aria-expanded={isMobileMenuOpen}
        >
          &#9776; {/* Hamburger icon */}
        </button>

        {/* app-nav will now primarily be for the hamburger-controlled menu (nav-links-left) */}
        {/* The UserDropdownMenu (nav-links-right) will be positioned separately if it's to remain always visible */}
        <nav className={`app-nav ${isMobileMenuOpen ? 'mobile-nav-active' : ''}`}>
          {/* This UL is for links that appear inside the hamburger menu */}
          <ul className="nav-links-hamburger">
            {/* Example: Future links would go here */}
            {/* <li><Link to="/help" onClick={closeMobileMenu}>Help</Link></li> */}
            {/* <li><Link to="/features" onClick={closeMobileMenu}>Features</Link></li> */}

            {/* If Data Management & User Management were to be here (they are in UserDropdown as per last change) */}
            {/* {token && user && (
              <>
                <li><Link to="/data-management" onClick={closeMobileMenu}>Data Management</Link></li>
                {user.is_superuser && (
                  <li><Link to="/users" onClick={closeMobileMenu}>User Management</Link></li>
                )}
              </>
            )} */}
          </ul>
        </nav>

        {/* User Dropdown Menu - positioned to the right, independent of hamburger */}
        <div className="user-actions-area">
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
