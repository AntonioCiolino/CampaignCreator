import React, { useState, ReactNode } from 'react';
import './CollapsibleSection.css';

import React, { useState, ReactNode, useEffect } from 'react'; // Added useEffect
import './CollapsibleSection.css';

interface CollapsibleSectionProps {
  title: string;
  children: ReactNode;
  initialCollapsed?: boolean;
  isManuallyCollapsed?: boolean; // New prop for external control
  onToggle?: (isCollapsed: boolean) => void; // Callback for when toggled
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  children,
  initialCollapsed = true,
  isManuallyCollapsed,
  onToggle,
}) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(initialCollapsed);

  // Effect to sync with external control
  useEffect(() => {
    if (isManuallyCollapsed !== undefined && isManuallyCollapsed !== isCollapsed) {
      setIsCollapsed(isManuallyCollapsed);
    }
  }, [isManuallyCollapsed, isCollapsed]);

  const toggleCollapse = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    if (onToggle) {
      onToggle(newState);
    }
  };

  return (
    <div className={`collapsible-section ${isCollapsed ? 'collapsed' : 'expanded'}`}>
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
