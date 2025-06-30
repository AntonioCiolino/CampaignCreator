import React, { useState, useEffect, useRef } from 'react'; // Add useRef
import './LoginPage.css'; // Import CSS
import LoginForm from '../components/auth/LoginForm';
import { useNavigate, useLocation } from 'react-router-dom'; // Add useLocation
import { useAuth } from '../contexts/AuthContext'; // Import useAuth
import { AxiosError } from 'axios';


// Configuration for video background
const FADE_DURATION_MS = 1000; // 1 second fade
// const GAP_DURATION_MS = 2000; // No longer used for a visible gap in cross-fade
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

  // State for two video players for cross-fading
  const [players, setPlayers] = useState([
    { src: '', key: Date.now(), isVisible: false, id: 0 },
    { src: '', key: Date.now() + 1, isVisible: false, id: 1 },
  ]);
  const [activePlayerIndex, setActivePlayerIndex] = useState(0); // 0 or 1
  // currentSourceIndex will point to the video in VIDEO_SOURCES that the *inactive* player should load next.
  const [currentSourceIndex, setCurrentSourceIndex] = useState(0);

  const videoRefs = [useRef<HTMLVideoElement>(null), useRef<HTMLVideoElement>(null)];
  const transitionEndTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize players
  useEffect(() => {
    if (VIDEO_SOURCES.length === 0) return;

    setPlayers(prev => {
      const newPlayers = [...prev];
      newPlayers[0] = { ...newPlayers[0], src: VIDEO_SOURCES[0], key: Date.now(), isVisible: true };
      if (VIDEO_SOURCES.length > 1) {
        newPlayers[1] = { ...newPlayers[1], src: VIDEO_SOURCES[1], key: Date.now() + 1, isVisible: false };
        setCurrentSourceIndex(2 % VIDEO_SOURCES.length); // Next video for player 0 after player 1 finishes
      } else {
        // Single video: player 1 won't be used for a different source initially
        newPlayers[1] = { ...newPlayers[1], src: '', key: Date.now() + 1, isVisible: false };
        setCurrentSourceIndex(0); // Points to the same video for reloading
      }
      return newPlayers;
    });
    setActivePlayerIndex(0);

    return () => {
      if (transitionEndTimerRef.current) clearTimeout(transitionEndTimerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  const handleVideoEnded = (endedPlayerIndex: number) => {
    if (endedPlayerIndex !== activePlayerIndex || VIDEO_SOURCES.length === 0) {
      return;
    }

    if (transitionEndTimerRef.current) {
      clearTimeout(transitionEndTimerRef.current);
    }

    if (VIDEO_SOURCES.length === 1) {
      // Single video: just restart it by changing its key after a short delay (simulating a loop with fade)
      setPlayers(prev => prev.map((p, i) => (i === activePlayerIndex ? { ...p, isVisible: false } : p)));
      transitionEndTimerRef.current = setTimeout(() => {
        setPlayers(prev => prev.map((p, i) => (i === activePlayerIndex ? { ...p, key: Date.now(), isVisible: true } : p)));
      }, FADE_DURATION_MS); // Fade out, then immediately fade back in
      return;
    }

    const playerToFadeInIndex = (activePlayerIndex + 1) % 2;
    const playerToFadeOutIndex = activePlayerIndex;

    // The playerToFadeInIndex should already have its src preloaded.
    // Now, trigger the cross-fade.
    setPlayers(prevPlayers => {
      const newPlayers = [...prevPlayers];
      newPlayers[playerToFadeOutIndex] = { ...newPlayers[playerToFadeOutIndex], isVisible: false };
      newPlayers[playerToFadeInIndex] = { ...newPlayers[playerToFadeInIndex], isVisible: true };
      return newPlayers;
    });

    setActivePlayerIndex(playerToFadeInIndex);

    // After the fade duration, update the src of the now hidden player (playerToFadeOutIndex)
    // so it starts preloading the next video in the sequence.
    transitionEndTimerRef.current = setTimeout(() => {
      const nextSrcForHiddenPlayer = VIDEO_SOURCES[currentSourceIndex];
      setPlayers(prevPlayers => {
        const newPlayers = [...prevPlayers];
        newPlayers[playerToFadeOutIndex] = {
          ...newPlayers[playerToFadeOutIndex],
          src: nextSrcForHiddenPlayer,
          key: Date.now(), // New key to ensure it reloads if src is the same
          isVisible: false, // Stays hidden
        };
        return newPlayers;
      });
      // Advance currentSourceIndex for the next cycle
      setCurrentSourceIndex(prevSrcIndex => (prevSrcIndex + 1) % VIDEO_SOURCES.length);
    }, FADE_DURATION_MS);
  };

  // This useEffect handles the login redirect
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
      {players.map((player, index) => (
        <video
          ref={videoRefs[index]}
          key={player.key}
          autoPlay
          muted
          playsInline
          onEnded={() => handleVideoEnded(player.id)}
          className="login-page-video-background"
          style={{
            opacity: player.isVisible ? BASE_VIDEO_OPACITY : 0,
            // zIndex is managed by order of rendering; last one with higher opacity will be on top.
            // Or, ensure activePlayerIndex video has higher zIndex if needed, but opacity should handle it.
          }}
          src={player.src}
        >
          Your browser does not support the video tag.
        </video>
      ))}
      <div className="login-card" style={{ zIndex: 10 }}> {/* Ensure login card is well above videos */}
        <h2>Login</h2>
        {error && <p className="login-error-message">{error}</p>}
        <LoginForm onSubmit={handleLogin} />
      </div>
    </div>
  );
};

export default LoginPage;
