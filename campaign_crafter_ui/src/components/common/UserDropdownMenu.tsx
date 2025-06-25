import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { User } from '../../types/userTypes';
import './UserDropdownMenu.css'; // We'll create this CSS file next

interface UserDropdownMenuProps {
  user: User;
  onLogout: () => void;
}

const UserDropdownMenu: React.FC<UserDropdownMenuProps> = ({ user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const toggleDropdown = () => setIsOpen(!isOpen);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="user-dropdown-menu" ref={dropdownRef}>
      <button onClick={toggleDropdown} className="dropdown-toggle">
        {user.username} ▼
      </button>
      {isOpen && (
        <ul className="dropdown-content">
          <li>
            <Link to="/user-settings" onClick={() => setIsOpen(false)}>
              User Settings
            </Link>
          </li>
          <li>
            {/* Placeholder for Subscription/Billing - links to '#' for now */}
            <Link to="#" onClick={() => setIsOpen(false)} style={{ opacity: 0.6, pointerEvents: 'none' }} title="Coming Soon!">
              Subscription
            </Link>
          </li>
          <li>
            <button onClick={() => { onLogout(); setIsOpen(false); }} className="dropdown-logout-button">
              Logout
            </button>
          </li>
        </ul>
      )}
    </div>
  );
};

export default UserDropdownMenu;
