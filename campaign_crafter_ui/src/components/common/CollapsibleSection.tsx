import React, { useState, ReactNode } from 'react';
import './CollapsibleSection.css';

interface CollapsibleSectionProps {
  title: string;
  children: ReactNode;
  initialCollapsed?: boolean;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  children,
  initialCollapsed = true, // Default to true (collapsed)
}) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(initialCollapsed);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className="collapsible-section">
      <div className="collapsible-section-header" onClick={toggleCollapse}>
        <span className="collapsible-section-icon">
          {isCollapsed ? '▶' : '▼'}
        </span>
        <h3 className="collapsible-section-title">{title}</h3>
      </div>
      {!isCollapsed && (
        <div className="collapsible-section-content">
          {children}
        </div>
      )}
    </div>
  );
};

export default CollapsibleSection;
