import React, { ReactNode, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // Added useNavigate
import { ReactComponent as Logo } from '../../logo_cc.svg';
import './Layout.css';
import { useAuth } from '../../contexts/AuthContext'; // Import useAuth

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { user, logout, token } = useAuth(); // Get auth state and functions
  const navigate = useNavigate();

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleLogout = () => {
    logout();
    navigate('/login'); // Redirect to login page after logout
    if(isMobileMenuOpen) setIsMobileMenuOpen(false); // Close mobile menu if open
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <Link to="/" className="app-title-link" onClick={() => isMobileMenuOpen && setIsMobileMenuOpen(false)}>
          <Logo className="app-logo" title="Campaign Crafter Logo" />
          <h1>Campaign Crafter</h1>
        </Link>
        <button className="hamburger-menu" onClick={toggleMobileMenu} aria-label="Toggle navigation" aria-expanded={isMobileMenuOpen}>
          &#9776; {/* Hamburger icon */}
        </button>
        <nav className={`app-nav ${isMobileMenuOpen ? 'mobile-nav-active' : ''}`}>
          <ul>
            {token && user ? (
              <>
                <li><span className="welcome-message">Welcome, {user.username}!</span></li>
                <li><Link to="/" onClick={() => setIsMobileMenuOpen(false)}>Dashboard</Link></li>
                <li><Link to="/user-settings" onClick={() => setIsMobileMenuOpen(false)}>User Settings</Link></li> {/* New Link */}
                {/* Add more authenticated user links here */}
                {user.is_superuser && (
                  <li><Link to="/users" onClick={() => setIsMobileMenuOpen(false)}>User Management</Link></li>
                )}
                <li><Link to="/data-management" onClick={() => setIsMobileMenuOpen(false)}>Data Management</Link></li>
                <li><button onClick={handleLogout} className="nav-link-button">Logout</button></li>
              </>
            ) : (
              <li><Link to="/login" onClick={() => setIsMobileMenuOpen(false)}>Login</Link></li>
            )}
          </ul>
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
