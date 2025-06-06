import React from 'react';
import './DetailedProgressDisplay.css'; // Optional: Create this for styling

interface DetailedProgressDisplayProps {
  percent: number;
  currentTitle: string;
  error?: string | null;
  title?: string; // Optional title for the progress section
}

const DetailedProgressDisplay: React.FC<DetailedProgressDisplayProps> = ({
  percent,
  currentTitle,
  error,
  title = "Processing Sections..." // Default title
}) => {
  return (
    <div className="detailed-progress-display editor-section card-like" style={{ marginTop: '20px', padding: '20px' }}>
      <h4>{title}</h4>
      <progress value={percent} max="100" style={{ width: '100%', marginBottom: '10px' }}></progress>
      <p style={{ marginBottom: '5px' }}>Progress: {percent.toFixed(2)}%</p>
      {currentTitle && <p>Current: {currentTitle}</p>}
      {error && <p className="error-message" style={{ marginTop: '10px' }}>Error: {error}</p>}
    </div>
  );
};

export default DetailedProgressDisplay;
