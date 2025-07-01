import React, { ReactNode } from 'react'; // Removed useState
import { Link, useNavigate } from 'react-router-dom';
import { ReactComponent as Logo } from '../../logo_cc.svg';
import './Layout.css';
import { useAuth } from '../../contexts/AuthContext';
import UserDropdownMenu from './UserDropdownMenu';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  // Removed isMobileMenuOpen state and toggleMobileMenu function
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
    // No need to manage isMobileMenuOpen here anymore
  };

  // closeMobileMenu is kept for now as links might still call it,
  // but it effectively does nothing if isMobileMenuOpen is removed.
  // Consider removing calls to closeMobileMenu if no mobile-specific menu is re-introduced.
  const closeMobileMenu = () => {
    // console.log("closeMobileMenu called, but no mobile menu state to change.");
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <Link to="/" className="app-title-link" onClick={closeMobileMenu}>
          <Logo className="app-logo" title="Campaign Crafter Logo" />
          <h1>Campaign Crafter</h1>
        </Link>

        {/* Hamburger menu button and its <nav> are now removed */}
        {/* Mobile navigation will need to be re-thought if a hamburger is desired only for mobile. */}
        {/* For now, this removes the hamburger functionality entirely. */}

        <div className="user-actions-area">
          {token && user ? (
            <UserDropdownMenu user={user} onLogout={handleLogout} />
          ) : (
            <ul>
              <li><Link to="/login" onClick={closeMobileMenu}>Login</Link></li>
            </ul>
          )}
        </div>
        {/* The erroneous extra </nav> tag that was here previously has been removed. */}
      </header>
      <main className="app-main-content">
        {children}
      </main>
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} Campaign Crafter. All rights reserved.</p>
        <nav className="footer-nav">
          <Link to="/about">About Us</Link>
          {/* Add other footer links here if needed */}
        </nav>
      </footer>
    </div>
  );
};

export default Layout;
