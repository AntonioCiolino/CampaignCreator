import React from 'react';
// Link is not directly used here anymore if Card handles navigation via href
// import { Link } from 'react-router-dom'; 
import { Campaign } from '../services/campaignService';
import Card from './common/Card'; // Import the new Card component
import './CampaignCard.css'; // CSS for specific content styling within the card

interface CampaignCardProps {
  campaign: Campaign;
}

const CampaignCard: React.FC<CampaignCardProps> = ({ campaign }) => {
  const conceptSnippet = campaign.concept ? `${campaign.concept.substring(0, 100)}...` : 'No concept yet.';
  const promptSnippet = campaign.initial_user_prompt ? `${campaign.initial_user_prompt.substring(0, 100)}...` : 'No initial prompt.';

  return (
    <li className="campaign-card"> {/* This class can remain for list item specific styling like margin */}
      <Card 
        href={`/campaign/${campaign.id}`} 
        interactive // Enable hover effects from generic Card
        className="campaign-card-link-wrapper" // Optional: if Card needs an additional class from here
      >
        <div className="campaign-card-content"> {/* This class from CampaignCard.css styles the inner content */}
          <div className="campaign-card-header">
            {campaign.badge_image_url ? (
              <span // Changed from <a> to <span>
                className="campaign-card-badge-link" // Keep for styling (cursor: pointer)
                onClick={(e) => {
                  e.stopPropagation(); // Prevent card click
                  window.open(campaign.badge_image_url, '_blank', 'noopener,noreferrer');
                }}
                onKeyDown={(e) => { // Add keyboard accessibility
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.stopPropagation();
                    window.open(campaign.badge_image_url, '_blank', 'noopener,noreferrer');
                  }
                }}
                role="link" // ARIA role
                tabIndex={0} // Make it focusable
                aria-label={`View badge for ${campaign.title}`}
              >
                <img 
                  src={campaign.badge_image_url} 
                  alt={`${campaign.title} Badge`} 
                  className="campaign-card-badge-image"
                />
              </span>
            ) : (
              <div className="campaign-card-badge-placeholder">
                {/* Optional: <span className="default-badge-icon">📷</span> */}
              </div>
            )}
            <h3 className="campaign-card-title">{campaign.title}</h3>
          </div>
          {campaign.concept ? 
            <p className="campaign-snippet">{conceptSnippet}</p> :
            <p className="campaign-snippet">{promptSnippet}</p>
          }
        </div>
      </Card>
    </li>
  );
};

export default CampaignCard;
