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
    render(<Tabs tabs={tabsData} activeTabName={tabsData[0].name} onTabChange={jest.fn()} />);
    expect(screen.getByText('Tab 1')).toBeInTheDocument();
    expect(screen.getByText('Tab 2')).toBeInTheDocument();
    expect(screen.getByText('Tab 3')).toBeInTheDocument();
  });

  test('displays content of the first tab by default', () => {
    render(<Tabs tabs={tabsData} activeTabName={tabsData[0].name} onTabChange={jest.fn()} />);
    expect(screen.getByTestId('content-tab1')).toBeVisible();
    expect(screen.queryByTestId('content-tab2')).not.toBeInTheDocument(); // Updated assertion
  });

  test('displays content of the specified activeTabName', () => { // Renamed test
    render(<Tabs tabs={tabsData} activeTabName="Tab 2" onTabChange={jest.fn()} />);
    expect(screen.getByTestId('content-tab2')).toBeVisible();
    expect(screen.queryByTestId('content-tab1')).not.toBeInTheDocument(); // Updated assertion
  });

  test('calls onTabChange with the correct tab name on click', () => {
    const mockOnTabChange = jest.fn();
    render(<Tabs tabs={tabsData} activeTabName={tabsData[0].name} onTabChange={mockOnTabChange} />);
    
    fireEvent.click(screen.getByText('Tab 2'));
    expect(mockOnTabChange).toHaveBeenCalledWith('Tab 2');
  });

  test('calls onTabChange with the correct tab name on Enter key press', () => {
    const mockOnTabChange = jest.fn();
    render(<Tabs tabs={tabsData} activeTabName={tabsData[0].name} onTabChange={mockOnTabChange} />);
    const tab2Button = screen.getByText('Tab 2');
    fireEvent.keyPress(tab2Button, { key: 'Enter', code: 'Enter', charCode: 13 });
    expect(mockOnTabChange).toHaveBeenCalledWith('Tab 2');
  });
  
  test('calls onTabChange with the correct tab name on Space key press', () => {
    const mockOnTabChange = jest.fn();
    render(<Tabs tabs={tabsData} activeTabName={tabsData[0].name} onTabChange={mockOnTabChange} />);
    const tab3Button = screen.getByText('Tab 3');
    fireEvent.keyPress(tab3Button, { key: ' ', code: 'Space', charCode: 32 });
    expect(mockOnTabChange).toHaveBeenCalledWith('Tab 3');
  });

  test('marks the tab corresponding to activeTabName with "active" class', () => {
    const { rerender } = render(<Tabs tabs={tabsData} activeTabName="Tab 2" onTabChange={jest.fn()} />);
    const tab1Button = screen.getByText('Tab 1');
    const tab2Button = screen.getByText('Tab 2');

    expect(tab2Button).toHaveClass('active');
    expect(tab1Button).not.toHaveClass('active');

    // Test rerender with a new activeTabName
    rerender(<Tabs tabs={tabsData} activeTabName="Tab 1" onTabChange={jest.fn()} />);
    expect(tab1Button).toHaveClass('active');
    expect(tab2Button).not.toHaveClass('active');
  });

  test('renders "No tabs to display" when tabs array is empty', () => {
    render(<Tabs tabs={[]} activeTabName="" onTabChange={jest.fn()} />);
    expect(screen.getByText('No tabs to display.')).toBeInTheDocument();
  });
});
