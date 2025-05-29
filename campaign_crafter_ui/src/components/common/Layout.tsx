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
        {/* Navigation links can be added here later */}
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
