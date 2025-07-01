import React, { useState, useEffect, useCallback } from 'react';
import { prepareCampaignForHomebrewery } from '../../services/campaignService';
import { PrepareHomebreweryPostResponse } from '../../types/campaignTypes'; // Corrected import path
import Modal from '../common/Modal'; // Import the new Modal component
import Button from '../common/Button'; // Import the new Button component
import './HomebreweryPostModal.css'; // Import specific styles for this modal's content

interface HomebreweryPostModalProps {
  isOpen: boolean;
  onClose: () => void;
  campaignId: string | number | null;
  campaignTitle?: string;
}

const HomebreweryPostModal: React.FC<HomebreweryPostModalProps> = ({ isOpen, onClose, campaignId, campaignTitle }) => {
  const [preparedData, setPreparedData] = useState<PrepareHomebreweryPostResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState<string>('');

  const fetchData = useCallback(async () => {
    if (!campaignId) {
      setError("No campaign ID provided. Cannot fetch Homebrewery data.");
      setPreparedData(null);
      return;
    }
    setIsLoading(true);
    setError(null);
    setCopySuccess('');
    try {
      const data = await prepareCampaignForHomebrewery(campaignId);
      setPreparedData(data);
    } catch (err) {
      console.error("Failed to prepare campaign for Homebrewery:", err);
      setError(err instanceof Error ? err.message : "An unknown error occurred while fetching data.");
      setPreparedData(null);
    } finally {
      setIsLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    if (isOpen && campaignId) {
      fetchData();
    } else if (!isOpen) {
      setPreparedData(null);
      setIsLoading(false);
      setError(null);
      setCopySuccess('');
    }
  }, [isOpen, campaignId, fetchData]);

  const handleCopyMarkdown = async () => {
    if (preparedData?.markdown_content) {
      try {
        await navigator.clipboard.writeText(preparedData.markdown_content);
        setCopySuccess('Markdown copied to clipboard!');
        setTimeout(() => setCopySuccess(''), 2500); 
      } catch (err) {
        console.error('Failed to copy markdown:', err);
        setCopySuccess('Failed to copy. Please copy manually.');
        setTimeout(() => setCopySuccess(''), 3000);
      }
    }
  };

  const modalTitle = `Prepare for Homebrewery: ${campaignTitle || (campaignId ? `Campaign ID ${campaignId}` : 'Campaign')}`;

  const renderContent = () => {
    if (isLoading) {
      return <p>Loading Homebrewery data...</p>;
    }
    if (error) {
      // Using global error class from App.css, can be more specific if needed
      return <p className="error-message" style={{border: '1px solid var(--danger-color)', padding: '10px', borderRadius: 'var(--border-radius)'}}>Error: {error}</p>;
    }
    if (preparedData) {
      return (
        <div className="hb-modal-body-content"> {/* Wrapper for consistent spacing */}
          <p><strong>Follow these steps to post your campaign to Homebrewery:</strong></p>
          <ol className="hb-modal-instructions">
            <li>Click the "Copy Markdown" button below. This will copy the full Homebrewery-formatted content of your campaign.</li>
            <li>Click the "Open Homebrewery (New Brew)" button. This will open Homebrewery's editor in a new browser tab.</li>
            <li>In the Homebrewery editor, paste the copied Markdown (usually Ctrl+V or Cmd+V).</li>
            <li>Give your brew a title and save it on Homebrewery!</li>
          </ol>

          <p>
            <strong>Suggested Filename (for local backup or reference):</strong>
          </p>
          <p className="hb-modal-filename">
            {preparedData.filename_suggestion}
          </p>
          
          {preparedData.notes && <p className="hb-modal-notes">Notes from backend: {preparedData.notes}</p>}

          <div>
            <label htmlFor="hb-markdown-content" className="hb-modal-textarea-label">
              Homebrewery Markdown Content:
            </label>
            <textarea
              id="hb-markdown-content"
              readOnly
              value={preparedData.markdown_content}
              className="hb-modal-textarea" // Use class from HomebreweryPostModal.css
            />
          </div>
          {copySuccess && <span className="hb-modal-copy-success">{copySuccess}</span>}
        </div>
      );
    }
    return null; // Should not happen if not loading and no error and no data
  };

  const renderFooter = () => {
    if (isLoading || error || !preparedData) {
        return <Button variant="secondary" onClick={onClose}>Close</Button>;
    }
    return (
      <div className="hb-modal-actions"> {/* For flex layout of buttons */}
        <Button 
          variant="primary" 
          onClick={handleCopyMarkdown} 
          disabled={!preparedData?.markdown_content}
        >
          Copy Markdown
        </Button>
        <Button
          variant="success"
          href={preparedData?.homebrewery_new_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Open Homebrewery (New Brew)
        </Button>
        <div style={{ marginLeft: 'auto' }}> {/* Push close to the right */}
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    );
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={modalTitle}
      footerContent={renderFooter()}
      size="lg" // Use a larger modal size
    >
      {renderContent()}
    </Modal>
  );
};

export default HomebreweryPostModal;
