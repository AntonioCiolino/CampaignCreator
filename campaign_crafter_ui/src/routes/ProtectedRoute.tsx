import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  allowedRoles?: ('user' | 'superuser')[]; // 'user' means any authenticated user
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles }) => {
  const { user, isLoading, token } = useAuth();
  const location = useLocation();

  if (isLoading) {
    // Optional: Show a loading spinner or a blank page while auth is being checked
    return <div>Loading authentication status...</div>; // More specific loading message
  }

  if (!token || !user) {
    // Not authenticated, redirect to login page
    // Pass the original location to redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check roles if specified
  if (allowedRoles) {
    const isAllowed = allowedRoles.some(role => {
      if (role === 'superuser') {
        return user.is_superuser;
      }
      if (role === 'user') {
        return true; // Any authenticated user is considered 'user' role
      }
      return false;
    });

    if (!isAllowed) {
      // User does not have the required role, redirect to a 'forbidden' page or home
      // For simplicity, redirecting to home. Consider a dedicated /forbidden page.
      console.warn(`User '${user.username}' with roles (is_superuser: ${user.is_superuser}) attempted to access a route allowed for roles: ${allowedRoles.join(', ')}. Redirecting.`);
      return <Navigate to="/" state={{ from: location }} replace />;
    }
  }

  // User is authenticated and has the required role (if specified)
  return <Outlet />; // Render the child route elements
};

export default ProtectedRoute;
