import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { User } from '../../types/userTypes';
import './UserDropdownMenu.css';

export interface AdditionalNavItem {
  path: string;
  label: string;
  onClick?: () => void; // Optional click handler
  isExternal?: boolean; // For external links if needed in future
  separatorBefore?: boolean; // Add a separator before this item
}

interface UserDropdownMenuProps {
  user: User;
  onLogout: () => void;
  additionalNavItems?: AdditionalNavItem[];
}

const UserDropdownMenu: React.FC<UserDropdownMenuProps> = ({ user, onLogout, additionalNavItems = [] }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // useEffect(() => {
  //   // console.log('User in dropdown:', user); // Keep for debugging if necessary
  // }, [user]);

  const toggleDropdown = () => setIsOpen(!isOpen);

  const handleLinkClick = (itemClick?: () => void) => {
    if (itemClick) {
      itemClick();
    }
    setIsOpen(false);
  };

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
      <button onClick={toggleDropdown} className="dropdown-toggle" aria-expanded={isOpen} aria-haspopup="true">
        {user.avatar_url ? (
          <img src={user.avatar_url} alt={`${user.username}'s avatar`} className="user-avatar-icon" />
        ) : (
          <span className="user-icon-placeholder" aria-hidden="true">👤</span>
        )}
        <span className="user-username">{user.username}</span>
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </button>
      {isOpen && (
        <ul className="dropdown-content" role="menu">
          <li>
            <Link to="/" role="menuitem" onClick={() => handleLinkClick()}>
              Dashboard
            </Link>
          </li>
          <li className="dropdown-separator" role="separator"><hr /></li> {/* Separator 1: After Dashboard */}
          <li>
            <Link to="/campaigns" role="menuitem" onClick={() => handleLinkClick()}>
              My Campaigns
            </Link>
          </li>
          <li>
            <Link to="/characters" role="menuitem" onClick={() => handleLinkClick()}>
              My Characters
            </Link>
          </li>

          {/* Separator 2: After My Characters, always present before the next block (additional or settings) */}
          <li className="dropdown-separator" role="separator"><hr /></li>

          {/* Render Additional Nav Items */}
          {additionalNavItems.map((item, index) => (
            <React.Fragment key={`additional-${index}`}>
              {item.separatorBefore && <li className="dropdown-separator" role="separator"><hr /></li>}
              <li>
                {item.isExternal ? (
                  <a href={item.path} target="_blank" rel="noopener noreferrer" role="menuitem" onClick={() => handleLinkClick(item.onClick)}>
                    {item.label}
                  </a>
                ) : (
                  <Link to={item.path} role="menuitem" onClick={() => handleLinkClick(item.onClick)}>
                    {item.label}
                  </Link>
                )}
              </li>
            </React.Fragment>
          ))}

          {/* Conditional Separator 3: Only if additionalNavItems exist and the last one didn't request a separator.
              This separates additionalNavItems from the My Settings block.
              If no additionalNavItems, Separator 2 already handles the division from My Characters.
          */}
          {additionalNavItems.length > 0 && !additionalNavItems[additionalNavItems.length - 1].separatorBefore && (
             <li className="dropdown-separator" role="separator"><hr /></li>
          )}
          {/* If additionalNavItems is empty, Separator 2 (after My Characters) effectively separates My Characters from My Settings.
              If additionalNavItems exist, the logic above handles separation.
              The existing separator before "Data Management" further groups "My Settings" and "My Subscription".
          */}

          <li>
            <Link to="/user-settings" role="menuitem" onClick={() => handleLinkClick()}>
              My Settings
            </Link>
          </li>
          <li>
            <Link to="#" role="menuitem" onClick={() => handleLinkClick()} style={{ opacity: 0.6, pointerEvents: 'none' }} title="Coming Soon!">
              My Subscription
            </Link>
          </li>

          <li className="dropdown-separator" role="separator"><hr /></li>

          <li>
            <Link to="/data-management" role="menuitem" onClick={() => handleLinkClick()}>
              Data Management
            </Link>
          </li>

          {user.is_superuser && (
            <li>
              <Link to="/users" role="menuitem" onClick={() => handleLinkClick()}>
                User Management
              </Link>
            </li>
          )}

          <li className="dropdown-separator" role="separator"><hr /></li>
          <li>
            <button onClick={() => { onLogout(); setIsOpen(false); }} className="dropdown-logout-button" role="menuitem">
              Logout
            </button>
          </li>
        </ul>
      )}
    </div>
  );
};

export default UserDropdownMenu;
