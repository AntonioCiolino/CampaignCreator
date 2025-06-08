import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
// Import specific functions to mock their implementations
import { loginUser, getMe } from '../services/userService';
import apiClient from '../services/apiClient';

// Mock userService and typecast the specific functions
jest.mock('../services/userService');
const mockedLoginUser = loginUser as jest.MockedFunction<typeof loginUser>;
const mockedGetMe = getMe as jest.MockedFunction<typeof getMe>;

// Mock localStorage
const localStorageMock = (() => {
  let store: { [key: string]: string } = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Test component to consume context
const TestConsumerComponent: React.FC = () => {
  const { user, token, isLoading, login, logout, isSuperuser } = useAuth();
  return (
    <div>
      {isLoading && <p>Loading...</p>}
      {token && <p>Token: {token}</p>}
      {user && <p>User: {user.username}</p>}
      {user && <p>Is Superuser: {isSuperuser().toString()}</p>}
      <button onClick={() => login('testuser', 'password')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    localStorageMock.clear();
    mockedLoginUser.mockClear(); // Use corrected mock name
    mockedGetMe.mockClear();   // Use corrected mock name
    delete apiClient.defaults.headers.common['Authorization'];
  });

  test('initial state when no token in localStorage', async () => {
    render(
      <AuthProvider>
        <TestConsumerComponent />
      </AuthProvider>
    );
    // Wait for isLoading to become false
    await waitFor(() => expect(screen.queryByText('Loading...')).not.toBeInTheDocument());

    expect(screen.queryByText(/Token:/)).toBeNull();
    expect(screen.queryByText(/User:/)).toBeNull();
  });

  test('initializes from localStorage and fetches user', async () => {
    localStorageMock.setItem('token', 'test-token');
    mockedGetMe.mockResolvedValueOnce({ // Use corrected mock name
      id: 1, username: 'localuser', email: 'local@example.com', disabled: false, is_superuser: true,
    });

    render(
      <AuthProvider>
        <TestConsumerComponent />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByText('Token: test-token')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('User: localuser')).toBeInTheDocument());
    expect(screen.getByText('Is Superuser: true')).toBeInTheDocument();
    expect(apiClient.defaults.headers.common['Authorization']).toBe('Bearer test-token');
    expect(mockedGetMe).toHaveBeenCalledTimes(1); // Use corrected mock name
  });

  test('handles failed user fetch on init by clearing token', async () => {
    localStorageMock.setItem('token', 'test-token-fail-fetch');
    mockedGetMe.mockRejectedValueOnce(new Error("Failed to fetch user")); // Use corrected mock name

    render(
      <AuthProvider>
        <TestConsumerComponent />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.queryByText('Loading...')).not.toBeInTheDocument());

    expect(screen.queryByText(/Token:/)).toBeNull();
    expect(screen.queryByText(/User:/)).toBeNull();
    expect(localStorageMock.getItem('token')).toBeNull();
    expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
  });


  test('login function sets user, token, and localStorage', async () => {
    mockedLoginUser.mockResolvedValueOnce({ access_token: 'new-login-token', token_type: 'bearer' }); // Use corrected mock name
    mockedGetMe.mockResolvedValueOnce({ // Use corrected mock name
      id: 2, username: 'loggedinuser', email: 'loggedin@example.com', disabled: false, is_superuser: false,
    });

    render(
      <AuthProvider>
        <TestConsumerComponent />
      </AuthProvider>
    );

    // Wait for initial loading to complete
    await waitFor(() => expect(screen.queryByText('Loading...')).not.toBeInTheDocument());

    act(() => {
      screen.getByRole('button', { name: /login/i }).click();
    });

    await waitFor(() => expect(mockedLoginUser).toHaveBeenCalledWith('testuser', 'password')); // Use corrected mock name
    await waitFor(() => expect(mockedGetMe).toHaveBeenCalledTimes(1)); // Use corrected mock name

    await waitFor(() => expect(screen.getByText('Token: new-login-token')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('User: loggedinuser')).toBeInTheDocument());
    expect(screen.getByText('Is Superuser: false')).toBeInTheDocument();
    expect(localStorageMock.getItem('token')).toBe('new-login-token');
    expect(apiClient.defaults.headers.common['Authorization']).toBe('Bearer new-login-token');
  });

  test('logout function clears user, token, and localStorage', async () => {
    // Setup initial logged-in state
    localStorageMock.setItem('token', 'initial-token-for-logout');
    mockedGetMe.mockResolvedValueOnce({ // Use corrected mock name
      id: 3, username: 'logoutuser', email: 'logout@example.com', disabled: false, is_superuser: false,
    });

    render(
      <AuthProvider>
        <TestConsumerComponent />
      </AuthProvider>
    );

    // Wait for user to be loaded
    await waitFor(() => expect(screen.getByText('User: logoutuser')).toBeInTheDocument());
    expect(apiClient.defaults.headers.common['Authorization']).toBe('Bearer initial-token-for-logout');


    act(() => {
      screen.getByRole('button', { name: /logout/i }).click();
    });

    await waitFor(() => expect(screen.queryByText(/Token:/)).toBeNull());
    expect(screen.queryByText(/User:/)).toBeNull();
    expect(localStorageMock.getItem('token')).toBeNull();
    expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
  });
});
