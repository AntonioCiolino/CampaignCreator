import React, { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ReactComponent as Logo } from '../../logo_cc.svg';
import './Layout.css';
import { useAuth } from '../../contexts/AuthContext';
import UserDropdownMenu, { AdditionalNavItem } from './UserDropdownMenu'; // Import AdditionalNavItem

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // This function is currently not used as mobile menu specific behavior was removed.
  // Keeping it in case a simplified mobile toggle (not a full separate menu) is added back later.
  // const closeMobileMenu = () => {
  //   // console.log("closeMobileMenu called, but no mobile menu state to change.");
  // };

  const userDropdownNavItems: AdditionalNavItem[] = [];
  if (token && user) {
    userDropdownNavItems.push({
      path: '/characters',
      label: 'My Characters',
      // onClick: closeMobileMenu, // Not needed if closeMobileMenu does nothing or is removed
      separatorBefore: false, // Characters link will appear after Dashboard, before the next separator
    });
    // Add more items here if needed, e.g.
    // userDropdownNavItems.push({ path: '/campaigns', label: 'My Campaigns', separatorBefore: true });
  }


  return (
    <div className="app-layout">
      <header className="app-header">
        <Link to="/" className="app-title-link" /*onClick={closeMobileMenu}*/>
          <Logo className="app-logo" title="Campaign Crafter Logo" />
          <h1>Campaign Crafter</h1>
        </Link>

        {/* The main-nav is now empty or can be repurposed for other global links if any */}
        <nav className="main-nav">
          {/* {token && user && (
            <ul>
              {/* Characters link was here, now moved to UserDropdownMenu * /}
              {/* Add other main navigation links here if needed * /}
            </ul>
          )} */}
        </nav>


        <div className="user-actions-area">
          {token && user ? (
            <UserDropdownMenu
              user={user}
              onLogout={handleLogout}
              additionalNavItems={userDropdownNavItems}
            />
          ) : (
            <ul className="logged-out-links"> {/* Added a class for potential styling */}
              <li><Link to="/login" /*onClick={closeMobileMenu}*/>Login</Link></li>
            </ul>
          )}
        </div>
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
