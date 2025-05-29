import React from 'react';
import { Routes, Route } from 'react-router-dom';
import DashboardPage from '../pages/DashboardPage';
import CampaignEditorPage from '../pages/CampaignEditorPage';
import NotFoundPage from '../pages/NotFoundPage';
// Placeholder for CampaignCreatePage - can be added later
// import CampaignCreatePage from '../pages/CampaignCreatePage';

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      {/* <Route path="/campaign/new" element={<CampaignCreatePage />} /> */}
      <Route path="/campaign/:campaignId" element={<CampaignEditorPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default AppRoutes;
