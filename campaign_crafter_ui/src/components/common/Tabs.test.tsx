import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Tabs, { TabItem } from './Tabs';

// Mock CSS import
jest.mock('./Tabs.css', () => ({}));

describe('Tabs Component', () => {
  const mockTab1Content = <div data-testid="content-tab1">Content for Tab 1</div>;
  const mockTab2Content = <div data-testid="content-tab2">Content for Tab 2</div>;
  const mockTab3Content = <div data-testid="content-tab3">Content for Tab 3</div>;

  const tabsData: TabItem[] = [
    { name: 'Tab 1', content: mockTab1Content },
    { name: 'Tab 2', content: mockTab2Content },
    { name: 'Tab 3', content: mockTab3Content },
  ];

  test('renders all tab names', () => {
    render(<Tabs tabs={tabsData} />);
    expect(screen.getByText('Tab 1')).toBeInTheDocument();
    expect(screen.getByText('Tab 2')).toBeInTheDocument();
    expect(screen.getByText('Tab 3')).toBeInTheDocument();
  });

  test('displays content of the first tab by default', () => {
    render(<Tabs tabs={tabsData} />);
    expect(screen.getByTestId('content-tab1')).toBeVisible();
    expect(screen.queryByTestId('content-tab2')).not.toBeVisible();
  });

  test('displays content of the specified initialTabName', () => {
    render(<Tabs tabs={tabsData} initialTabName="Tab 2" />);
    expect(screen.getByTestId('content-tab2')).toBeVisible();
    expect(screen.queryByTestId('content-tab1')).not.toBeVisible();
  });

  test('switches tab and displays content on click', () => {
    render(<Tabs tabs={tabsData} />);
    
    // Initially Tab 1 content is visible
    expect(screen.getByTestId('content-tab1')).toBeVisible();
    expect(screen.queryByTestId('content-tab2')).not.toBeVisible();

    // Click on Tab 2
    fireEvent.click(screen.getByText('Tab 2'));
    
    // Now Tab 2 content should be visible
    expect(screen.getByTestId('content-tab2')).toBeVisible();
    expect(screen.queryByTestId('content-tab1')).not.toBeVisible();
  });

  test('switches tab and displays content on Enter key press', () => {
    render(<Tabs tabs={tabsData} />);
    
    expect(screen.getByTestId('content-tab1')).toBeVisible();
    const tab2Button = screen.getByText('Tab 2');
    fireEvent.keyPress(tab2Button, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    expect(screen.getByTestId('content-tab2')).toBeVisible();
    expect(screen.queryByTestId('content-tab1')).not.toBeVisible();
  });
  
  test('switches tab and displays content on Space key press', () => {
    render(<Tabs tabs={tabsData} />);
    
    expect(screen.getByTestId('content-tab1')).toBeVisible();
    const tab3Button = screen.getByText('Tab 3');
    fireEvent.keyPress(tab3Button, { key: ' ', code: 'Space', charCode: 32 });
    
    expect(screen.getByTestId('content-tab3')).toBeVisible();
    expect(screen.queryByTestId('content-tab1')).not.toBeVisible();
  });

  test('marks the active tab with "active" class', () => {
    render(<Tabs tabs={tabsData} initialTabName="Tab 2" />);
    const tab1Button = screen.getByText('Tab 1');
    const tab2Button = screen.getByText('Tab 2');

    expect(tab2Button).toHaveClass('active');
    expect(tab1Button).not.toHaveClass('active');

    fireEvent.click(tab1Button);
    expect(tab1Button).toHaveClass('active');
    expect(tab2Button).not.toHaveClass('active');
  });

  test('renders "No tabs to display" when tabs array is empty', () => {
    render(<Tabs tabs={[]} />);
    expect(screen.getByText('No tabs to display.')).toBeInTheDocument();
  });
});
