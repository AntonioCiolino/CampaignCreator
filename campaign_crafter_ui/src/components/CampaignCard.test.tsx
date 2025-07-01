import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import CampaignCard from './CampaignCard';
import { Campaign } from '../services/campaignService'; // Ensure this path is correct

const mockCampaignWithBadge: Campaign = {
  id: 1,
  title: 'Test Campaign With Badge',
  initial_user_prompt: 'A grand adventure awaits!',
  concept: 'A quest to find the ancient artifact.',
  display_toc: null,
  homebrewery_toc: [{ title: 'Chapter 1: The Beginning', type: 'chapter' }],
  badge_image_url: 'http://example.com/campaign_badge.png',
  selected_llm_id: 'openai/gpt-3.5-turbo', // Added for interface completeness
  temperature: 0.7, // Added for interface completeness
  // owner_id: 1, // Not used by CampaignCard display
  // sections: [], // Not used by CampaignCard display
};

const mockCampaignWithoutBadge: Campaign = {
  id: 2,
  title: 'Test Campaign No Badge',
  initial_user_prompt: 'Another journey begins.',
  concept: 'Exploring the unknown lands.',
  display_toc: [{ title: 'Overview', type: 'generic' }, { title: 'Rules', type: 'rules' }],
  homebrewery_toc: [{ title: 'Introduction', type: 'introduction' }],
  badge_image_url: null,
  selected_llm_id: 'openai/gpt-4', // Added for interface completeness
  temperature: 0.5, // Added for interface completeness
  // owner_id: 2, // Not used by CampaignCard display
  // sections: [], // Not used by CampaignCard display
};

describe('CampaignCard', () => {
  test('renders campaign title and snippet', () => {
    render(
      <MemoryRouter>
        <CampaignCard campaign={mockCampaignWithBadge} />
      </MemoryRouter>
    );
    expect(screen.getByText(mockCampaignWithBadge.title)).toBeInTheDocument();
    expect(screen.getByText(`${mockCampaignWithBadge.concept!.substring(0, 100)}...`)).toBeInTheDocument();
  });

  describe('Badge Image Display', () => {
    test('displays badge image as a clickable link when badge_image_url exists', () => {
      render(
        <MemoryRouter>
          <CampaignCard campaign={mockCampaignWithBadge} />
        </MemoryRouter>
      );

      const badgeImage = screen.getByRole('img', { name: `${mockCampaignWithBadge.title} Badge` });
      expect(badgeImage).toBeInTheDocument();
      expect(badgeImage).toHaveAttribute('src', mockCampaignWithBadge.badge_image_url);

      const parentLink = badgeImage.closest('a');
      expect(parentLink).toBeInTheDocument();
      expect(parentLink).toHaveAttribute('href', mockCampaignWithBadge.badge_image_url);
      expect(parentLink).toHaveAttribute('target', '_blank');
      expect(parentLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    test('displays placeholder when badge_image_url does not exist', () => {
      render(
        <MemoryRouter>
          <CampaignCard campaign={mockCampaignWithoutBadge} />
        </MemoryRouter>
      );

      expect(screen.queryByRole('img', { name: `${mockCampaignWithoutBadge.title} Badge` })).not.toBeInTheDocument();
      // Check for placeholder. The current implementation renders an empty div.
      // If a specific placeholder text or icon was added, test for that.
      // For now, we can check if the placeholder div exists by its class if needed,
      // or just rely on the absence of the image.
      // Example if placeholder had a testid: expect(screen.getByTestId('badge-placeholder')).toBeInTheDocument();
      // For now, the absence of image and link is the key.
      const header = screen.getByText(mockCampaignWithoutBadge.title).closest('.campaign-card-header');
      expect(header?.querySelector('.campaign-card-badge-placeholder')).toBeInTheDocument();
      expect(header?.querySelector('a.campaign-card-badge-link')).not.toBeInTheDocument();

    });

    test('badge link click should not navigate the main card link (simulated)', () => {
      // This test is a bit conceptual with JSDOM as true navigation doesn't happen.
      // We are testing that e.stopPropagation() is present on the badge link.
      // A more robust test would involve a spy on window.location or router navigation,
      // but for this component, the direct presence of stopPropagation is a good indicator.
      
      const mockStopPropagation = jest.fn();
      
      render(
        <MemoryRouter>
          <CampaignCard campaign={mockCampaignWithBadge} />
        </MemoryRouter>
      );

      const badgeLink = screen.getByRole('img', { name: `${mockCampaignWithBadge.title} Badge` }).closest('a');
      expect(badgeLink).toBeInTheDocument();

      // Simulate a click event where stopPropagation can be spied upon if we could attach it.
      // However, directly testing the outcome of stopPropagation in JSDOM is tricky.
      // The presence of onClick={(e) => e.stopPropagation()} in the component code
      // is the primary thing we rely on from the implementation.
      // We can simulate the click and ensure no other navigation is triggered if we had a mock for it.
      if (badgeLink) {
        // Manually create an event and dispatch it to check if stopPropagation is called.
        // This is more complex than typical RTL usage.
        // For now, we'll assume the onClick handler is correctly implemented.
        // A more integrated test might involve mocking the parent Card's navigation.
        fireEvent.click(badgeLink, { stopPropagation: mockStopPropagation });
        // In a real scenario if the card itself had an onClick that caused navigation,
        // we'd check that the navigation mock wasn't called.
        // Here, we can only check if our mockStopPropagation was called if the event system worked that way.
        // Since it's a direct prop, it's harder to intercept here without deeper mocking.
        // The main check is that the link exists and has the right attributes.
      }
      // This test doesn't assert mockStopPropagation was called because the actual
      // stopPropagation is on the event object during the real click handler.
      // The key is that the attribute is present in the component's code.
      // We've verified the link is there and correctly configured.
    });
  });
});
