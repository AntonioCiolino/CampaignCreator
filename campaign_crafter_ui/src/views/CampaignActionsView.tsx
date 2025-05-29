import React, { useState } from 'react';
import HomebreweryPostModal from '../components/modals/HomebreweryPostModal'; // Assuming path is correct

const pageStyle: React.CSSProperties = {
  padding: '20px',
  fontFamily: 'Arial, sans-serif',
  maxWidth: '800px',
  margin: '0 auto',
};

const headerStyle: React.CSSProperties = {
  borderBottom: '2px solid #eee',
  paddingBottom: '10px',
  marginBottom: '20px',
};

const buttonStyle: React.CSSProperties = {
  padding: '12px 20px',
  backgroundColor: '#5cb85c', // A distinct color for this action
  color: 'white',
  border: 'none',
  borderRadius: '5px',
  cursor: 'pointer',
  fontSize: '1em',
  fontWeight: '500',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  transition: 'background-color 0.2s ease',
};


// This is a placeholder view. In a real application, campaignId and campaignTitle
// would likely come from URL parameters (e.g., React Router) or a global state/context.
const CampaignActionsView: React.FC = () => {
  // Simulate having a campaign loaded.
  // TODO: Replace these with actual campaign data from props, context, or router.
  const [currentCampaignId] = useState<string | number>('123'); // Example Campaign ID
  const [currentCampaignTitle] = useState<string>('My Awesome Campaign Adventure'); // Example Title

  const [isHomebreweryModalOpen, setIsHomebreweryModalOpen] = useState<boolean>(false);

  const handleOpenHomebreweryModal = () => {
    if (!currentCampaignId) {
        alert("No campaign selected or loaded to prepare for Homebrewery.");
        return;
    }
    setIsHomebreweryModalOpen(true);
  };

  const handleCloseHomebreweryModal = () => {
    setIsHomebreweryModalOpen(false);
  };

  return (
    <div style={pageStyle}>
      <header style={headerStyle}>
        <h1>Campaign Actions</h1>
        {currentCampaignId && currentCampaignTitle && (
          <p>
            <strong>Campaign:</strong> {currentCampaignTitle} (ID: {currentCampaignId})
          </p>
        )}
         {!currentCampaignId && <p>No campaign loaded. Please select a campaign first.</p>}
      </header>

      <section>
        <h2>Export & Sharing</h2>
        <p>Prepare your campaign content for posting on Homebrewery.</p>
        <button 
            onClick={handleOpenHomebreweryModal} 
            style={buttonStyle}
            onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#4cae4c')}
            onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#5cb85c')}
            disabled={!currentCampaignId} // Disable if no campaign ID
        >
          Prepare for Homebrewery
        </button>
      </section>

      {isHomebreweryModalOpen && currentCampaignId && (
        <HomebreweryPostModal
          isOpen={isHomebreweryModalOpen}
          onClose={handleCloseHomebreweryModal}
          campaignId={currentCampaignId}
          campaignTitle={currentCampaignTitle}
        />
      )}

      {/* 
        In a real application, you would integrate this into your main router,
        for example, in App.tsx or a dedicated routing configuration file:

        import CampaignActionsView from './views/CampaignActionsView';
        
        <Routes>
          // other routes
          <Route path="/campaigns/:campaignId/actions" element={<CampaignActionsView />} /> 
          // Or a general tools page that then takes a campaign context
        </Routes>
        
        And provide NavLinks or buttons to navigate to this view for a specific campaign.
        The campaignId and title would then be fetched based on the URL param or context.
      */}
    </div>
  );
};

export default CampaignActionsView;
