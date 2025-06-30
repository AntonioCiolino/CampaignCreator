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
  const [erroredSources, setErroredSources] = useState<Set<string>>(new Set());

  const videoRefs = [useRef<HTMLVideoElement>(null), useRef<HTMLVideoElement>(null)];
  const transitionTimerRef = useRef<NodeJS.Timeout | null>(null); // Single timer for all transitions

  // Initialize players
  useEffect(() => {
    if (VIDEO_SOURCES.length === 0) {
      console.log('[LoginPage Init] No video sources, skipping initialization.');
      return;
    }
    console.log('[LoginPage Init] Initializing video players...');

    const initialErrored = new Set<string>(); // Start with no errored sources for init

    const firstVid = findNextPlayableSource(0, initialErrored);
    if (!firstVid.src) {
      console.error('[LoginPage Init] No playable video found for Player 0. Stopping initialization.');
      setPlayers(prev => prev.map(p => ({ ...p, isVisible: false, src: '' }))); // Make all invisible
      return;
    }
    console.log(`[LoginPage Init] Player 0 (active) gets src: ${firstVid.src} (index ${firstVid.index})`);

    let p1Src = '';
    let p1Key = Date.now() + 1;
    let nextCSI = firstVid.index; // Default for single video or if no other playable

    if (VIDEO_SOURCES.length > 1) {
      const secondVidStartIndex = (firstVid.index + 1) % VIDEO_SOURCES.length;
      const secondVid = findNextPlayableSource(secondVidStartIndex, initialErrored);

      if (secondVid.src && secondVid.index !== firstVid.index) {
        p1Src = secondVid.src;
        p1Key = Date.now() + 1;
        nextCSI = secondVid.index; // currentSourceIndex points to the one Player 1 (hidden) has
        console.log(`[LoginPage Init] Player 1 (hidden) preloads src: ${p1Src} (index ${secondVid.index})`);
      } else if (secondVid.src && secondVid.index === firstVid.index) {
        // Only one playable video found, Player 1 won't preload a different one.
        // It can keep its empty src or mirror player 0 but stay hidden.
        // nextCSI remains firstVid.index for loop.
        console.log('[LoginPage Init] Only one distinct playable video found. Player 1 not preloading different video.');
      } else {
         // All other videos (if any) are errored.
         console.log('[LoginPage Init] No second distinct playable video found for Player 1 preload.');
      }
    } else {
        console.log('[LoginPage Init] Single video source in VIDEO_SOURCES.');
    }

    setPlayers([
      { src: firstVid.src, key: Date.now(), isVisible: true, id: 0 },
      { src: p1Src, key: p1Key, isVisible: false, id: 1 },
    ]);
    setActivePlayerIndex(0);
    setCurrentSourceIndex(nextCSI);
    console.log(`[LoginPage Init] ActivePlayerIndex: 0. Initial currentSourceIndex (for next visible/Player 1's content): ${nextCSI}`);

    return () => {
      if (transitionTimerRef.current) clearTimeout(transitionTimerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // findNextPlayableSource is stable if defined outside or memoized, not adding as dep.


  const findNextPlayableSource = (startIndex: number, currentErroredSources: Set<string>): { src: string | null; index: number } => {
    if (VIDEO_SOURCES.length === 0) return { src: null, index: -1 };

    for (let i = 0; i < VIDEO_SOURCES.length; i++) {
      const potentialIndex = (startIndex + i) % VIDEO_SOURCES.length;
      const potentialSrc = VIDEO_SOURCES[potentialIndex];
      if (!currentErroredSources.has(potentialSrc)) {
        return { src: potentialSrc, index: potentialIndex };
      }
    }
    return { src: null, index: -1 }; // All sources have errored
  };

  const triggerNextVideo = (triggeringPlayerId: number, isError: boolean = false) => {
    let localErroredSources = erroredSources;
    if (isError) {
      const erroredSrc = players[triggeringPlayerId]?.src;
      if (erroredSrc && erroredSrc !== '') { // Avoid adding empty initial src
        localErroredSources = new Set(erroredSources).add(erroredSrc);
        setErroredSources(localErroredSources); // Update state
        console.error(`[triggerNextVideo] Error on player: ${triggeringPlayerId}, src: ${erroredSrc}. Added to erroredSources.`);
      } else {
        console.error(`[triggerNextVideo] Error on player: ${triggeringPlayerId} with empty/invalid src. Not adding to erroredSources.`);
      }
    } else {
      console.log(`[triggerNextVideo] Ended player: ${triggeringPlayerId}. Active: ${activePlayerIndex}.`);
    }

    if (triggeringPlayerId !== activePlayerIndex || VIDEO_SOURCES.length === 0) {
      return;
    }

    if (transitionTimerRef.current) clearTimeout(transitionTimerRef.current);

    // --- Single Video Logic ---
    if (VIDEO_SOURCES.length === 1) {
      if (localErroredSources.has(VIDEO_SOURCES[0])) {
        console.log('[triggerNextVideo] Single video source has errored. Stopping.');
        setPlayers(prev => prev.map(p => ({ ...p, isVisible: false, src: '' })));
        return;
      }
      console.log('[triggerNextVideo] Single video: restarting with fade.');
      setPlayers(prev => prev.map(p => (p.id === activePlayerIndex ? { ...p, isVisible: false } : p)));
      transitionTimerRef.current = setTimeout(() => {
        setPlayers(prev => prev.map(p => (p.id === activePlayerIndex ? { ...p, key: Date.now(), isVisible: true } : p)));
      }, FADE_DURATION_MS);
      return;
    }

    // --- Multiple Videos Logic ---
    const playerToFadeOutIndex = activePlayerIndex;
    const playerToFadeInIndex = (activePlayerIndex + 1) % 2;

    // Find the next video for the player that's about to fade in.
    // currentSourceIndex should point to the src that playerToFadeInIndex *was preloaded with*.
    const fadeInAttempt = findNextPlayableSource(currentSourceIndex, localErroredSources);

    if (!fadeInAttempt.src) {
      console.error("[triggerNextVideo] All video sources have errored or no playable source found for fade-in. Stopping playback.");
      setPlayers(prev => prev.map(p => ({ ...p, isVisible: false, src: '' })));
      return;
    }

    console.log(`[triggerNextVideo] Cross-fading. Out: P${playerToFadeOutIndex}, In: P${playerToFadeInIndex}. Fading in src: ${fadeInAttempt.src} (index ${fadeInAttempt.index})`);

    setPlayers(prev => {
      const newPlayers = [...prev];
      newPlayers[playerToFadeOutIndex] = { ...newPlayers[playerToFadeOutIndex], isVisible: false };
      newPlayers[playerToFadeInIndex] = {
        ...newPlayers[playerToFadeInIndex],
        src: fadeInAttempt.src!,
        key: Date.now(),
        isVisible: true
      };
      return newPlayers;
    });

    setActivePlayerIndex(playerToFadeInIndex);
    // currentSourceIndex should now point to the video for the *next* preload (for playerToFadeOutIndex)
    let nextIndexForPreload = (fadeInAttempt.index + 1) % VIDEO_SOURCES.length;

    transitionTimerRef.current = setTimeout(() => {
      // Now find the source for the player that just faded out (playerToFadeOutIndex)
      const preloadAttempt = findNextPlayableSource(nextIndexForPreload, localErroredSources);

      if (preloadAttempt.src) {
        console.log(`[triggerNextVideo] Timeout: Preloading P${playerToFadeOutIndex} (hidden) with ${preloadAttempt.src} (index ${preloadAttempt.index})`);
        setPlayers(prev => {
          const newPlayers = [...prev];
          newPlayers[playerToFadeOutIndex] = {
            ...newPlayers[playerToFadeOutIndex],
            src: preloadAttempt.src!,
            key: Date.now() + 1,
            isVisible: false
          };
          return newPlayers;
        });
        // The next video to actually play will be preloadAttempt.src, so update currentSourceIndex
        setCurrentSourceIndex(preloadAttempt.index);
        console.log(`[triggerNextVideo] Timeout: currentSourceIndex updated to: ${preloadAttempt.index} (for next fade-in)`);
      } else {
        console.error("[triggerNextVideo] Timeout: All further videos for preload have errored. Hidden player won't be preloaded.");
        // Keep currentSourceIndex as is, or set to a state indicating no more valid sources for preload
        // This means the next onEnded/onError might also hit the "all videos failed" state.
      }
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
