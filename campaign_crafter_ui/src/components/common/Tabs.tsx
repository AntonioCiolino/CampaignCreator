import React, { useState, ReactElement } from 'react';
import './Tabs.css'; // Import the CSS file

export interface TabItem {
  name: string;
  content: ReactElement;
  disabled?: boolean;
}

interface TabsProps {
  tabs: TabItem[];
  initialTabName?: string;
}

const Tabs: React.FC<TabsProps> = ({ tabs, initialTabName }) => {
  const [activeTab, setActiveTab] = useState<string>(() => {
    if (initialTabName && tabs.some(tab => tab.name === initialTabName)) {
      return initialTabName;
    }
    return tabs.length > 0 ? tabs[0].name : '';
  });

  if (tabs.length === 0) {
    return <div className="tabs-container"><p>No tabs to display.</p></div>;
  }

  const handleTabClick = (tabName: string, isDisabled?: boolean) => {
    if (isDisabled) {
      return; // Do not change tab if it's disabled
    }
    setActiveTab(tabName);
  };

  const activeTabContent = tabs.find(tab => tab.name === activeTab)?.content;

  return (
    <div className="tabs-container">
      <ul className="tab-list">
        {tabs.map((tab) => (
          <li
            key={tab.name}
            className={`tab-list-item ${tab.name === activeTab ? 'active' : ''} ${tab.disabled ? 'tab-disabled' : ''}`}
            onClick={() => handleTabClick(tab.name, tab.disabled)}
            role="tab"
            aria-selected={tab.name === activeTab}
            aria-disabled={tab.disabled} // Announce disabled state to assistive technologies
            aria-controls={`tabpanel-${tab.name}`}
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
            id={`tabpanel-${activeTab}`}
            role="tabpanel"
            aria-labelledby={`tab-${activeTab}`}
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
