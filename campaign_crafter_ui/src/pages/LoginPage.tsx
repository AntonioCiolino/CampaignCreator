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
console.log('[LoginPage] Initial VIDEO_SOURCES:', VIDEO_SOURCES);

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
  // currentSourceIndex now consistently points to the video that the *next active player* should play.
  const [currentSourceIndex, setCurrentSourceIndex] = useState(0);

  const videoRefs = [useRef<HTMLVideoElement>(null), useRef<HTMLVideoElement>(null)];
  const transitionTimerRef = useRef<NodeJS.Timeout | null>(null); // Single timer for all transitions

  // Initialize players
  useEffect(() => {
    if (VIDEO_SOURCES.length === 0) return;
    console.log('[LoginPage Init] Initializing. VIDEO_SOURCES available.');

    setPlayers(prev => {
      const newPlayers = [...prev];
      newPlayers[0] = { ...newPlayers[0], src: VIDEO_SOURCES[0], key: Date.now(), isVisible: true };
      console.log(`[LoginPage Init] Player 0 (active) gets src: ${VIDEO_SOURCES[0]}`);

      const preloadSrcIndex = VIDEO_SOURCES.length > 1 ? 1 : 0;
      newPlayers[1] = { ...newPlayers[1], src: VIDEO_SOURCES[preloadSrcIndex], key: Date.now() + 1, isVisible: false };
      if (VIDEO_SOURCES.length > 1) {
        console.log(`[LoginPage Init] Player 1 (hidden) preloads src: ${VIDEO_SOURCES[preloadSrcIndex]}`);
      }
      return newPlayers;
    });

    setActivePlayerIndex(0);
    const initialCurrentSourceIndex = VIDEO_SOURCES.length > 1 ? 1 : 0;
    setCurrentSourceIndex(initialCurrentSourceIndex);
    console.log(`[LoginPage Init] ActivePlayerIndex: 0. Initial currentSourceIndex (for next visible): ${initialCurrentSourceIndex}`);

    return () => {
      if (transitionTimerRef.current) clearTimeout(transitionTimerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  const triggerNextVideo = (triggeringPlayerId: number, isError: boolean = false) => {
    if (isError) {
      console.error(`[triggerNextVideo] Error on player: ${triggeringPlayerId}, src: ${players[triggeringPlayerId]?.src || 'N/A'}. Attempting to advance.`);
    } else {
      console.log(`[triggerNextVideo] Ended player: ${triggeringPlayerId}. Active: ${activePlayerIndex}. Attempting to advance.`);
    }

    if (triggeringPlayerId !== activePlayerIndex || VIDEO_SOURCES.length === 0) {
      // console.log(`[triggerNextVideo] Conditions not met. Triggering: ${triggeringPlayerId}, Active: ${activePlayerIndex}`); // Too verbose
      return;
    }

    if (transitionTimerRef.current) clearTimeout(transitionTimerRef.current);

    if (VIDEO_SOURCES.length === 1) {
      console.log('[triggerNextVideo] Single video: restarting.');
      setPlayers(prev => prev.map(p => (p.id === activePlayerIndex ? { ...p, isVisible: false } : p))); // Fade out
      transitionTimerRef.current = setTimeout(() => {
        setPlayers(prev => prev.map(p => (p.id === activePlayerIndex ? { ...p, key: Date.now(), isVisible: true } : p))); // Fade back in
      }, FADE_DURATION_MS);
      return;
    }

    const playerToFadeOutIndex = activePlayerIndex;
    const playerToFadeInIndex = (activePlayerIndex + 1) % 2;

    console.log(`[triggerNextVideo] Cross-fading. Out: P${playerToFadeOutIndex}, In: P${playerToFadeInIndex}. Next video src: VIDEO_SOURCES[${currentSourceIndex}]`);

    setPlayers(prev => {
      const newPlayers = [...prev];
      newPlayers[playerToFadeOutIndex] = { ...newPlayers[playerToFadeOutIndex], isVisible: false };
      newPlayers[playerToFadeInIndex] = {
        ...newPlayers[playerToFadeInIndex],
        src: VIDEO_SOURCES[currentSourceIndex],
        key: Date.now(),
        isVisible: true
      };
      // console.log('[triggerNextVideo] SetPlayers for cross-fade:', newPlayers.map(p => ({id: p.id, src: p.src, vis: p.isVisible }))); // Too verbose
      return newPlayers;
    });

    setActivePlayerIndex(playerToFadeInIndex);
    const nextSourceIndexForFollowingPreload = (currentSourceIndex + 1) % VIDEO_SOURCES.length;

    transitionTimerRef.current = setTimeout(() => {
      console.log(`[triggerNextVideo] Timeout: Preloading P${playerToFadeOutIndex} (hidden) with VIDEO_SOURCES[${nextSourceIndexForFollowingPreload}]`);
      setPlayers(prev => {
        const newPlayers = [...prev];
        newPlayers[playerToFadeOutIndex] = {
          ...newPlayers[playerToFadeOutIndex],
          src: VIDEO_SOURCES[nextSourceIndexForFollowingPreload],
          key: Date.now() + 1,
          isVisible: false
        };
        // console.log('[triggerNextVideo] SetPlayers for preload:', newPlayers.map(p => ({id: p.id, src: p.src, vis: p.isVisible }))); // Too verbose
        return newPlayers;
      });
      setCurrentSourceIndex(nextSourceIndexForFollowingPreload);
      console.log(`[triggerNextVideo] Timeout: currentSourceIndex is now: ${nextSourceIndexForFollowingPreload}`);
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
          onEnded={() => triggerNextVideo(player.id)}
          onError={(e) => { console.error('Video Error on player:', player.id, 'src:', player.src, e); triggerNextVideo(player.id, true); }}
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
