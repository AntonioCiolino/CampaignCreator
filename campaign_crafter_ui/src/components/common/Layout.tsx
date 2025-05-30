import React, { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import './Layout.css'; // We'll create this CSS file next

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="app-layout">
      <header className="app-header">
        <Link to="/" className="app-title-link">
          <h1>Campaign Crafter</h1>
        </Link>
        <nav className="app-nav">
          <ul>
            <li>
              <Link to="/">Dashboard</Link>
               </li>
               <li>
                 <Link to="/">Campaign Management</Link> {/* Added link */}
            </li>
            <li>
              <Link to="/users">User Management</Link>
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
