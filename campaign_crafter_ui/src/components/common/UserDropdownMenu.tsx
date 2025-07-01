import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom'; // Added useLocation
import { User } from '../../types/userTypes';
import './UserDropdownMenu.css'; // We'll create this CSS file next

interface UserDropdownMenuProps {
  user: User;
  onLogout: () => void;
}

const UserDropdownMenu: React.FC<UserDropdownMenuProps> = ({ user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const location = useLocation(); // Initialize useLocation

  // Log user from context to check avatar_url
  useEffect(() => {
    console.log('User in dropdown:', user);
  }, [user]);

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
        {user.avatar_url ? (
          <img src={user.avatar_url} alt={`${user.username}'s avatar`} className="user-avatar-icon" />
        ) : (
          <span className="user-icon-placeholder" aria-hidden="true">👤</span>
        )}
        <span className="user-username">{user.username}</span>
        <span className="dropdown-arrow">▼</span>
      </button>
      {isOpen && (
        <ul className="dropdown-content">
          <li>
            <Link to="/" onClick={() => setIsOpen(false)}>
              Dashboard
            </Link>
          </li>
          {/* Character List Link - This needs campaignId from context/store ideally */}
          {/* For now, let's assume campaignId might be available via a hook or prop later */}
          {/* This is a placeholder for where it would go. Actual implementation needs campaignId. */}
          {/* To make it somewhat functional without context here, we can navigate to a generic path
               or make it visible only on certain pages using location.pathname checks,
               but a global state for selectedCampaignId is the best approach.
               For this task, I will add a basic link.
               A better implementation would involve a campaign context.
            */}
          <li>
            {/* This link will need to be dynamic based on the current campaign.
                If we are on a campaign page, we can extract campaignId from URL.
                Otherwise, this link might be disabled or navigate to a selection page.
                For now, it's a simple link.
            */}
            <Link
              to={location.pathname.includes('/campaign/') ? `${location.pathname.split('/').slice(0,3).join('/')}/characters` : "/campaigns"}
              onClick={() => setIsOpen(false)}
              title={location.pathname.includes('/campaign/') ? "View Characters for Current Campaign" : "Select a Campaign to View Characters"}
            >
              Characters
            </Link>
          </li>
          <li>
            <Link to="/user-settings" onClick={() => setIsOpen(false)}>
              My Settings
            </Link>
          </li>
          <li>
            {/* Placeholder for Subscription/Billing - links to '#' for now */}
            <Link to="#" onClick={() => setIsOpen(false)} style={{ opacity: 0.6, pointerEvents: 'none' }} title="Coming Soon!">
              My Subscription
            </Link>
          </li>

          {/* Separator before Data Management */}
          <li className="dropdown-separator"><hr /></li>

          <li>
            <Link to="/data-management" onClick={() => setIsOpen(false)}>
              Data Management
            </Link>
          </li>

          {user.is_superuser && (
            // User Management is only for superusers
            <li>
              <Link to="/users" onClick={() => setIsOpen(false)}>
                User Management
              </Link>
            </li>
          )}

          {/* Separator before Logout */}
          <li className="dropdown-separator"><hr /></li>
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
