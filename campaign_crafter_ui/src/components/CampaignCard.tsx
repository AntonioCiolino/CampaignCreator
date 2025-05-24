import React from 'react';
import { Link } from 'react-router-dom';
import { Campaign } from '../services/campaignService'; // Assuming Campaign type is exported from here
import './CampaignCard.css'; // CSS for the card

interface CampaignCardProps {
  campaign: Campaign;
}

const CampaignCard: React.FC<CampaignCardProps> = ({ campaign }) => {
  const conceptSnippet = campaign.concept ? `${campaign.concept.substring(0, 100)}...` : 'No concept yet.';
  const promptSnippet = campaign.initial_user_prompt ? `${campaign.initial_user_prompt.substring(0, 100)}...` : 'No initial prompt.';

  return (
    <li className="campaign-card">
      <Link to={`/campaign/${campaign.id}`} className="campaign-card-link">
        <div className="campaign-card-content">
          <h3>{campaign.title}</h3>
          {campaign.concept ? 
            <p className="campaign-snippet">{conceptSnippet}</p> :
            <p className="campaign-snippet">{promptSnippet}</p>
          }
        </div>
      </Link>
    </li>
  );
};

export default CampaignCard;
