import React from 'react';
// Link is not directly used here anymore if Card handles navigation via href
// import { Link } from 'react-router-dom'; 
import { Campaign } from '../types/campaignTypes'; // Corrected import path
import Card from './common/Card'; // Import the new Card component
import Button from './common/Button'; // Import Button
import './CampaignCard.css'; // CSS for specific content styling within the card

interface CampaignCardProps {
  campaign: Campaign;
  onDelete?: (campaignId: number, campaignTitle: string) => void;
}

const CampaignCard: React.FC<CampaignCardProps> = ({ campaign, onDelete }) => {
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
                  if (campaign.badge_image_url) { // Explicit check for TS
                    window.open(campaign.badge_image_url, '_blank', 'noopener,noreferrer');
                  }
                }}
                onKeyDown={(e) => { // Add keyboard accessibility
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.stopPropagation();
                    if (campaign.badge_image_url) { // Explicit check for TS
                      window.open(campaign.badge_image_url, '_blank', 'noopener,noreferrer');
                    }
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
          {onDelete && (
            <div className="campaign-card-actions">
              {/* Placeholder for other actions like Edit */}
              <Button
                  variant="danger" // Or "outline-danger"
                  size="sm" // Make it a small button
                  onClick={(e) => {
                      e.preventDefault(); // Prevent default anchor tag navigation
                      e.stopPropagation(); // Stop event bubbling in React tree
                      // Check onDelete again inside to satisfy TypeScript strict null checks,
                      // though the outer check onDelete && (...) should suffice.
                      if (onDelete) {
                        onDelete(campaign.id, campaign.title);
                      }
                  }}
                  aria-label={`Delete campaign ${campaign.title}`}
              >
                  Delete
              </Button>
            </div>
          )}
        </div>
      </Card>
    </li>
  );
};

export default CampaignCard;
