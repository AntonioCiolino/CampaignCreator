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
          <h3>{campaign.title}</h3>
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
