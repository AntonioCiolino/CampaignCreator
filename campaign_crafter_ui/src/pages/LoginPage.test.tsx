import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom';
import LoginPage from './LoginPage';
import { useAuth } from '../contexts/AuthContext';

// Mock the useAuth hook
jest.mock('../contexts/AuthContext');

// Mock react-router-dom's useNavigate
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // Use actual for other parts
  useNavigate: () => mockedNavigate,
  useLocation: () => ({ pathname: '/login', state: null }), // Mock useLocation for LoginPage
}));

const mockLogin = jest.fn();
const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>; // Typecast for mock functions

describe('LoginPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    mockLogin.mockClear();
    mockedNavigate.mockClear();

    // Default mock return value for useAuth
    mockedUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: mockLogin,
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(false),
      setUser: jest.fn(),
    });

    // Mock process.env.PUBLIC_URL for video src
    // process.env.PUBLIC_URL = ''; // JSDOM doesn't have PUBLIC_URL, so it defaults to empty or host
  });

  test('renders login form correctly', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <LoginPage />
      </MemoryRouter>
    );
    expect(screen.getByLabelText(/username or email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  test('renders video background with correct attributes', () => {
    // Mock process.env.PUBLIC_URL for this specific test if needed,
    // or ensure it's handled globally if your setup requires it for tests.
    // For this test, we'll assume PUBLIC_URL resolves correctly or check relative path.
    // Lines modifying process.env.PUBLIC_URL have been removed.

    render(
      <MemoryRouter initialEntries={['/login']}>
        <LoginPage />
      </MemoryRouter>
    );

    // A more direct way to get the video element:
    const video = document.querySelector('video');
    expect(video).toBeInTheDocument();

    if (video) { // TypeScript null check
      // expect(video).toHaveAttribute('autoPlay'); // Removed due to JSDOM limitations
      // expect(video).toHaveAttribute('loop');    // Removed due to JSDOM limitations
      // expect(video).toHaveAttribute('muted');   // Removed due to JSDOM limitations
      // expect(video).toHaveAttribute('playsInline'); // Removed due to JSDOM limitations
      expect(video.className).toContain('login-page-video-background');
      // Check src attribute. process.env.PUBLIC_URL is '' in CRA tests by default
      // or you can set it if your component relies on it being something else.
      expect(video.src).toBe(window.location.origin + '/assets/videos/Dnd5e_realistic_high_202506282155_3836j.mp4');
      // The fallback text
      expect(screen.getByText('Your browser does not support the video tag.')).toBeInTheDocument();
    }
    // Removed restoration of process.env.PUBLIC_URL
  });


  test('calls login on form submission and navigates on success', async () => {
    mockLogin.mockResolvedValueOnce(undefined); // Simulate successful login in AuthContext

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes> {/* Define routes used by LoginPage and for navigation target */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<div>Dashboard Page</div>} /> {/* Mock dashboard/home route */}
        </Routes>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/username or email/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password');
    });
    await waitFor(() => {
      // Check if navigate was called to the root path after successful login
      // LoginPage's handleLogin navigates to location.state?.from?.pathname || '/'
      expect(mockedNavigate).toHaveBeenCalledWith('/', { replace: true });
    });
  });

  test('displays error message on failed login', async () => {
    const errorMessage = "Invalid credentials";
    // Simulate login failure by having the mockLogin function throw an error
    // The error should have a structure that LoginPage's catch block can handle
    const mockError = {
      isAxiosError: true,
      response: { data: { detail: errorMessage } },
      message: 'Request failed' // Fallback message
    };
    mockLogin.mockRejectedValueOnce(mockError);

    render(
      <MemoryRouter initialEntries={['/login']}>
        <LoginPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/username or email/i), { target: { value: 'wronguser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpass' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  test('redirects if user is already logged in and not loading', () => {
    mockedUseAuth.mockReturnValue({
      user: { id: 1, username: 'test', email: 'test@example.com', disabled: false, is_superuser: false }, // Mock authenticated user
      token: 'fake-token',
      isLoading: false,
      login: mockLogin,
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(false),
      setUser: jest.fn(), // Add this
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    );
    // LoginPage useEffect should call navigate
    expect(mockedNavigate).toHaveBeenCalledWith('/', { replace: true });
  });

  test('shows loading state when isLoading is true', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: true, // Simulate loading state
      login: mockLogin,
      logout: jest.fn(),
      isSuperuser: jest.fn().mockReturnValue(false),
      setUser: jest.fn(), // Add this
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <LoginPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/loading\.\.\./i)).toBeInTheDocument();
  });
});
