import React from 'react';
import { Routes, Route } from 'react-router-dom'; // BrowserRouter removed, it's in App.tsx
import DashboardPage from '../pages/DashboardPage';
import CampaignEditorPage from '../pages/CampaignEditorPage';
import UserManagementPage from '../pages/UserManagementPage';
import DataManagementPage from '../pages/DataManagementPage';
import UserSettingsPage from '../pages/UserSettingsPage'; // Added import
import NotFoundPage from '../pages/NotFoundPage';
import LoginPage from '../pages/LoginPage';
import ProtectedRoute from './ProtectedRoute';
// import CampaignCreatePage from '../pages/CampaignCreatePage'; // Placeholder

const AppRoutes: React.FC = () => {
  return (
    // BrowserRouter is in App.tsx, so not needed here
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected Routes - Any authenticated user */}
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<DashboardPage />} />
        {/* Assuming existing path /campaign/:campaignId is for editing */}
        <Route path="/campaign/:campaignId" element={<CampaignEditorPage />} />
        {/* Add other routes that require any authenticated user, e.g., CampaignCreatePage */}
        {/* <Route path="/campaign/new" element={<CampaignCreatePage />} /> */}
      </Route>

      {/* Protected Routes - Explicitly 'user' role (any authenticated user) */}
      {/* This is somewhat redundant if <ProtectedRoute /> already defaults to any authenticated user,
          but can be used if more specific 'user' vs other non-admin roles were to emerge.
          For now, it achieves the same as the block above.
      */}
      <Route element={<ProtectedRoute allowedRoles={['user']} />}>
        <Route path="/data-management" element={<DataManagementPage />} />
        <Route path="/user-settings" element={<UserSettingsPage />} /> {/* New Route */}
      </Route>

      {/* Protected Routes - Superuser only */}
      <Route element={<ProtectedRoute allowedRoles={['superuser']} />}>
        <Route path="/users" element={<UserManagementPage />} />
      </Route>

      {/* Fallback for not found pages */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default AppRoutes;
