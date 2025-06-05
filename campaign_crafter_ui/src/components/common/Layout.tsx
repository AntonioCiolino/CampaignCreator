import React, { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ReactComponent as Logo } from '../../../logo_cc.svg';
import './Layout.css';
// Assuming logo_placeholder.svg is in the public folder,
// it can be referenced directly by path in Vite/CRA.
// For specific import behavior, ensure your bundler (e.g., Vite) handles SVG as ReactComponent or provides its URL.
// If using Vite and want to use it as a component: import { ReactComponent as Logo } from '/logo_placeholder.svg';
// For simplicity, we'll use it as a direct src path.
// const logoUrl = '/logo_placeholder.svg'; // This is how you'd typically reference public assets

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="app-layout">
      <header className="app-header">
        <Link to="/" className="app-title-link">
          <Logo className="app-logo" title="Campaign Crafter Logo" />
          <h1>Campaign Crafter</h1>
        </Link>
        <nav className="app-nav">
          <ul>
            <li>
              <Link to="/">Campaigns</Link> {/* Renamed */}
            </li>
            {/* The "Campaign Management" li element is removed */}
            <li>
              <Link to="/users">User Management</Link>
            </li>
            <li>
              <Link to="/data-management">Data Management</Link>
            </li>
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
