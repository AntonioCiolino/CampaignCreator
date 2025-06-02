import React from 'react';
import { Routes, Route } from 'react-router-dom';
import DashboardPage from '../pages/DashboardPage';
import CampaignEditorPage from '../pages/CampaignEditorPage';
import UserManagementPage from '../pages/UserManagementPage'; // Added import
import DataManagementPage from '../pages/DataManagementPage'; // Added import
import NotFoundPage from '../pages/NotFoundPage';
// Placeholder for CampaignCreatePage - can be added later
// import CampaignCreatePage from '../pages/CampaignCreatePage';

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      {/* <Route path="/campaign/new" element={<CampaignCreatePage />} /> */}
      <Route path="/campaign/:campaignId" element={<CampaignEditorPage />} />
      <Route path="/users" element={<UserManagementPage />} /> {/* Added route */}
      <Route path="/data-management" element={<DataManagementPage />} /> {/* Added route */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default AppRoutes;
