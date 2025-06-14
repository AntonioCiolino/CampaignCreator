import React, { useState, ReactElement } from 'react';
import './Tabs.css'; // Import the CSS file

export interface TabItem {
  name: string;
  content: ReactElement;
  disabled?: boolean;
}

interface TabsProps {
  tabs: TabItem[];
  activeTabName: string; // Changed from initialTabName and removed internal state management for this
  onTabChange: (tabName: string) => void; // New prop to notify parent of tab change
}

const Tabs: React.FC<TabsProps> = ({ tabs, activeTabName, onTabChange }) => {
  // const [activeTab, setActiveTab] = useState<string>(() => { // REMOVE THIS
  //   if (initialTabName && tabs.some(tab => tab.name === initialTabName)) { // REMOVE THIS
  //     return initialTabName; // REMOVE THIS
  //   } // REMOVE THIS
  //   return tabs.length > 0 ? tabs[0].name : ''; // REMOVE THIS
  // }); // REMOVE THIS

  if (tabs.length === 0) {
    return <div className="tabs-container"><p>No tabs to display.</p></div>;
  }

  const handleTabClick = (tabName: string, isDisabled?: boolean) => {
    if (isDisabled) {
      return; // Do not change tab if it's disabled
    }
    // setActiveTab(tabName); // REMOVE THIS
    onTabChange(tabName); // CALL THE PROP
  };

  const activeTabContent = tabs.find(tab => tab.name === activeTabName)?.content;

  return (
    <div className="tabs-container">
      <ul className="tab-list">
        {tabs.map((tab) => (
          <li
            key={tab.name}
            className={`tab-list-item ${tab.name === activeTabName ? 'active' : ''} ${tab.disabled ? 'tab-disabled' : ''}`}
            onClick={() => handleTabClick(tab.name, tab.disabled)}
            role="tab"
            aria-selected={tab.name === activeTabName}
            aria-disabled={tab.disabled} // Announce disabled state to assistive technologies
            aria-controls={`tabpanel-${tab.name}`}
            id={`tab-${tab.name}`} // Added id for aria-labelledby correspondence
            tabIndex={tab.disabled ? -1 : 0} // Make disabled tabs not focusable
            onKeyPress={(e) => { if (!tab.disabled && (e.key === 'Enter' || e.key === ' ')) handleTabClick(tab.name, tab.disabled);}}
          >
            {tab.name}
          </li>
        ))}
      </ul>
      <div className="tab-content">
        {activeTabContent ? (
          <div
            id={`tabpanel-${activeTabName}`} // Corrected to use activeTabName for the panel id
            role="tabpanel"
            aria-labelledby={`tab-${activeTabName}`} // Corrected to activeTabName and removed duplicate
            className="tab-pane"
          >
            {activeTabContent}
          </div>
        ) : (
          <p>Select a tab to see its content.</p>
        )}
      </div>
    </div>
  );
};

export default Tabs;
