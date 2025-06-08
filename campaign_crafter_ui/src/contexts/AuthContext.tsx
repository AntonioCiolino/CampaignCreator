import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '../services/apiClient';
import { User } from '../types/userTypes';
import { loginUser as apiLoginUser, getMe as apiGetMe } from '../services/userService'; // Ensure getMe is exported from userService

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username_or_email: string, password: string) => Promise<void>;
  logout: () => void;
  isSuperuser: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true); // Start loading
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        setToken(storedToken);
        // Axios initializes defaults.headers and defaults.headers.common
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        try {
          const userData = await apiGetMe();
          setUser(userData);
        } catch (error) {
          console.error("Failed to fetch user on init:", error);
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
          if (apiClient.defaults.headers && apiClient.defaults.headers.common) {
            delete apiClient.defaults.headers.common['Authorization'];
          }
        }
      }
      setIsLoading(false); // End loading
    };
    initializeAuth();
  }, []);

  const login = async (username_or_email: string, password: string) => {
    const tokenData = await apiLoginUser(username_or_email, password);
    localStorage.setItem('token', tokenData.access_token);
    setToken(tokenData.access_token);
    // Axios initializes defaults.headers and defaults.headers.common
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
    const userData = await apiGetMe();
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setToken(null);
    if (apiClient.defaults.headers && apiClient.defaults.headers.common) {
        delete apiClient.defaults.headers.common['Authorization'];
    }
    // Navigation to login page will be handled by ProtectedRoutes or calling components
  };

  const isSuperuser = () => {
    return user?.is_superuser === true;
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, isSuperuser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
