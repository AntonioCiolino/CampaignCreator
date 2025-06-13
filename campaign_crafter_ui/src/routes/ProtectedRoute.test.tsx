import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Outlet } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import { useAuth } from '../contexts/AuthContext';
import { User } from '../types/userTypes'; // For user mock

// Mock the useAuth hook
jest.mock('../contexts/AuthContext');
const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// Mock child component to render if protected route allows access
const MockChildComponent: React.FC = () => <div>Protected Content</div>;
const MockLoginPage: React.FC = () => <div>Login Page</div>; // For redirect target
const MockHomePage: React.FC = () => <div>Home Page</div>; // For redirect target

describe('ProtectedRoute', () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  test('renders child component for authenticated user with no specific roles required', () => {
    mockedUseAuth.mockReturnValue({
      user: { id: 1, username: 'testuser', disabled: false, is_superuser: false, email: 'test@example.com' } as User,
      token: 'fake-token',
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(false),
      setUser: jest.fn(), // Add this
    });

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute />}>
            <Route index element={<MockChildComponent />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  test('redirects to login for unauthenticated user', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(false),
      setUser: jest.fn(), // Add this
    });

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute />}>
            <Route index element={<MockChildComponent />} />
          </Route>
          <Route path="/login" element={<MockLoginPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  test('redirects to home for authenticated user lacking required superuser role', () => {
    mockedUseAuth.mockReturnValue({
      user: { id: 1, username: 'testuser', disabled: false, is_superuser: false, email: 'test@example.com' } as User,
      token: 'fake-token',
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(false), // Explicitly regular user
      setUser: jest.fn(), // Add this
    });

    render(
      <MemoryRouter initialEntries={['/superuser-route']}>
        <Routes>
          <Route path="/superuser-route" element={<ProtectedRoute allowedRoles={['superuser']} />}>
            <Route index element={<MockChildComponent />} />
          </Route>
          <Route path="/" element={<MockHomePage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Home Page')).toBeInTheDocument(); // Redirects to home as per ProtectedRoute logic
  });

  test('renders child component for authenticated superuser with superuser role required', () => {
    mockedUseAuth.mockReturnValue({
      user: { id: 1, username: 'super', disabled: false, is_superuser: true, email: 'super@example.com' } as User,
      token: 'fake-token',
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(true), // Explicitly superuser
      setUser: jest.fn(), // Add this
    });

    render(
      <MemoryRouter initialEntries={['/superuser-route']}>
        <Routes>
          <Route path="/superuser-route" element={<ProtectedRoute allowedRoles={['superuser']} />}>
            <Route index element={<MockChildComponent />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  test('renders child component for authenticated regular user with "user" role required', () => {
    mockedUseAuth.mockReturnValue({
      user: { id: 1, username: 'testuser', disabled: false, is_superuser: false, email: 'test@example.com' } as User,
      token: 'fake-token',
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(false),
      setUser: jest.fn(), // Add this
    });

    render(
      <MemoryRouter initialEntries={['/user-route']}>
        <Routes>
          <Route path="/user-route" element={<ProtectedRoute allowedRoles={['user']} />}>
            <Route index element={<MockChildComponent />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  test('shows loading message when isLoading is true', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: true,
      login: jest.fn(),
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(false),
      setUser: jest.fn(), // Add this
    });

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute />}>
            <Route index element={<MockChildComponent />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Loading authentication status...')).toBeInTheDocument();
  });
});
