import React, { useState, useEffect, useRef } from 'react'; // Add useRef
import './LoginPage.css'; // Import CSS
import LoginForm from '../components/auth/LoginForm';
import { useNavigate, useLocation } from 'react-router-dom'; // Add useLocation
import { useAuth } from '../contexts/AuthContext'; // Import useAuth
import { AxiosError } from 'axios';


// Configuration for video background
const FADE_DURATION_MS = 1000; // 1 second fade
const GAP_DURATION_MS = 2000;  // 2 seconds gap between videos
const BASE_VIDEO_OPACITY = 0.2; // Target opacity for visible video

// Placeholder video sources - replace with your actual video paths
// Ensure these files are in your `public/assets/videos/` directory
const VIDEO_SOURCES = [
  `${process.env.PUBLIC_URL}/assets/videos/Dnd5e_realistic_high_202506282155_3836j.mp4`,
  `${process.env.PUBLIC_URL}/assets/videos/loop2.mp4`, // Replace with actual file
  `${process.env.PUBLIC_URL}/assets/videos/loop3.mp4`, // Replace with actual file
];

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation(); // For redirecting after login
  const { login, user, isLoading, token } = useAuth(); // Get user, isLoading, token from AuthContext
  const [error, setError] = useState<string | null>(null);

  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [isVideoFadingOut, setIsVideoFadingOut] = useState(true); // Start faded out, then fade in
  const [videoKey, setVideoKey] = useState(Date.now()); // Used to force video remount
  const fadeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const gapTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleVideoEnded = () => {
    if (VIDEO_SOURCES.length > 1) {
      setIsVideoFadingOut(true);
      if (fadeTimeoutRef.current) clearTimeout(fadeTimeoutRef.current);
      fadeTimeoutRef.current = setTimeout(() => {
        setCurrentVideoIndex((prevIndex) => (prevIndex + 1) % VIDEO_SOURCES.length);
        setVideoKey(Date.now()); // Ensures the new video loads and plays

        // The new video will start playing automatically due to autoPlay and new key.
        // We need to fade it in after a short delay to allow it to load a bit (or use onLoadedData)
        // For simplicity here, we'll fade in after the gap.
        if (gapTimeoutRef.current) clearTimeout(gapTimeoutRef.current);
        gapTimeoutRef.current = setTimeout(() => {
          setIsVideoFadingOut(false); // Trigger fade-in
        }, GAP_DURATION_MS);

      }, FADE_DURATION_MS);
    } else {
      // If only one video, restart it by changing key (acts like a loop with a pause)
      // Or simply add 'loop' attribute to video tag if no gap/fade is desired for single video.
      // For consistency with multi-video logic including gap:
      setIsVideoFadingOut(true);
      if (fadeTimeoutRef.current) clearTimeout(fadeTimeoutRef.current);
      fadeTimeoutRef.current = setTimeout(() => {
        setVideoKey(Date.now()); // Re-trigger load/play
        if (gapTimeoutRef.current) clearTimeout(gapTimeoutRef.current);
        gapTimeoutRef.current = setTimeout(() => {
          setIsVideoFadingOut(false);
        }, GAP_DURATION_MS);
      }, FADE_DURATION_MS);
    }
  };

  useEffect(() => {
    // Initial fade-in for the very first video
    setIsVideoFadingOut(false);

    return () => {
      // Cleanup timeouts when component unmounts
      if (fadeTimeoutRef.current) clearTimeout(fadeTimeoutRef.current);
      if (gapTimeoutRef.current) clearTimeout(gapTimeoutRef.current);
    };
  }, []); // Run only once on mount

  useEffect(() => {
    // If user is already logged in (and not loading), redirect from login page
    if (!isLoading && token && user) {
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [user, token, isLoading, navigate, location.state]);

  const handleLogin = async (username_or_email: string, password: string) => {
    setError(null);
    try {
      await login(username_or_email, password); // Call context login
      // Redirect to the page they were trying to access, or dashboard
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (err) {
      const axiosError = err as AxiosError<any>;
      if (axiosError.response && axiosError.response.data && axiosError.response.data.detail) {
        setError(axiosError.response.data.detail);
      } else if (err instanceof Error) { // More specific error type check
        setError(err.message || 'Login failed. Please try again.');
      }
      else {
        setError('Login failed. Please try again.');
      }
      console.error("Login error:", err);
    }
  };

  // If still loading auth status or already logged in and about to redirect, don't show form yet.
  if (isLoading || (token && user)) {
    return <div>Loading...</div>; // Or a blank screen, or a spinner
  }

  return (
    <div className="login-page-container">
      <video
        key={videoKey}
        autoPlay
        muted
        playsInline
        onEnded={handleVideoEnded}
        className="login-page-video-background"
        style={{ opacity: isVideoFadingOut ? 0 : BASE_VIDEO_OPACITY }}
        src={VIDEO_SOURCES[currentVideoIndex]}
      >
        Your browser does not support the video tag.
      </video>
      <div className="login-card">
        <h2>Login</h2>
        {error && <p className="login-error-message">{error}</p>}
        <LoginForm onSubmit={handleLogin} />
      </div>
    </div>
  );
};

export default LoginPage;
