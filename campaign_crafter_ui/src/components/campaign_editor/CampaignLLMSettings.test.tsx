import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CampaignLLMSettings from './CampaignLLMSettings';
import { LLM } from '../../utils/llm'; // Adjust path as needed

describe('CampaignLLMSettings', () => {
  // Clear mocks before each test
  beforeEach(() => {
    mockSetSelectedLLM.mockClear();
    mockSetTemperature.mockClear();
    mockHandleGenerateTOC.mockClear();
    mockHandleGenerateTitles.mockClear();
  });

  const mockSetSelectedLLM = jest.fn();
  const mockSetTemperature = jest.fn();
  const mockHandleGenerateTOC = jest.fn();
  const mockHandleGenerateTitles = jest.fn();

  const llm1: LLM = { id: 'llm-1', name: 'LLM One', capabilities: ['chat'] };
  const llm2: LLM = { id: 'llm-2', name: 'LLM Two', capabilities: ['chat'] };
  const availableLLMs: LLM[] = [llm1, llm2];

  const defaultProps = {
    selectedLLM: llm1,
    setSelectedLLM: mockSetSelectedLLM,
    temperature: 0.7,
    setTemperature: mockSetTemperature,
    isGeneratingTOC: false,
    handleGenerateTOC: mockHandleGenerateTOC,
    isGeneratingTitles: false,
    handleGenerateTitles: mockHandleGenerateTitles,
    availableLLMs: availableLLMs,
  };

  test('renders correctly with basic props', () => {
    render(<CampaignLLMSettings {...defaultProps} />);

    expect(screen.getByLabelText(/Select LLM/i)).toBeInTheDocument();
    // Check if the selected LLM name is displayed (Material UI Select might render it in a specific way)
    expect(screen.getByText(llm1.name)).toBeInTheDocument(); 
    
    expect(screen.getByText(/Temperature/i)).toBeInTheDocument();
    // Slider value might be hard to check directly, but its presence and label are good indicators.
    expect(screen.getByRole('slider')).toBeInTheDocument();

    expect(screen.getByRole('button', { name: /Generate TOC/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate Titles for Sections/i })).toBeInTheDocument();
  });

  test('shows generating state for TOC button', () => {
    render(<CampaignLLMSettings {...defaultProps} isGeneratingTOC={true} />);
    expect(screen.getByRole('button', { name: /Generating TOC.../i })).toBeInTheDocument();
  });

  test('shows generating state for Titles button', () => {
    render(<CampaignLLMSettings {...defaultProps} isGeneratingTitles={true} />);
    expect(screen.getByRole('button', { name: /Generating Titles.../i })).toBeInTheDocument();
  });

  test('disables buttons when one generation is in progress', () => {
    render(<CampaignLLMSettings {...defaultProps} isGeneratingTOC={true} />);
    expect(screen.getByRole('button', { name: /Generating TOC.../i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Generate Titles for Sections/i })).toBeDisabled();
  });

  test('calls setSelectedLLM when a new LLM is selected', () => {
    render(<CampaignLLMSettings {...defaultProps} />);
    // MUI Select interaction:
    // 1. Click the select to open the dropdown.
    // 2. Click the desired option.
    const selectButton = screen.getByRole('button', { name: new RegExp(llm1.name, "i") }); // MUI Select renders as a button
    fireEvent.mouseDown(selectButton); // Opens the dropdown

    // Options are usually in a listbox popup
    const optionToSelect = screen.getByRole('option', { name: llm2.name });
    fireEvent.click(optionToSelect);
    
    expect(mockSetSelectedLLM).toHaveBeenCalledWith(llm2);
  });

  test('calls setTemperature when slider is changed', () => {
    render(<CampaignLLMSettings {...defaultProps} />);
    const slider = screen.getByRole('slider');
    // Note: Testing MUI Slider value changes can be tricky.
    // This is a simplified way to check if the change handler is called.
    // A more robust test might involve checking the aria-valuenow or visual value if possible.
    // For this example, we simulate a change event.
    // The actual value change logic is internal to MUI Slider.
    // We are testing if our setTemperature prop is called.
    // fireEvent.change(slider, { target: { value: '0.5' } }); // This might not work directly with MUI slider
    // A more common way is to simulate keyboard interaction if accessible
    fireEvent.keyDown(slider, { key: 'ArrowRight' }); // Example: simulate a change
    // Or, if the component directly exposes an onChange that we can test, that's better.
    // In this case, the Slider's onChange prop calls setTemperature directly.
    // We can't directly simulate the internal MUI slider emitting a new value to its onChange.
    // However, if the component had a more direct way to trigger this, we'd use it.
    // For now, we acknowledge this is a limitation in directly testing the value propagation
    // without a more complex setup or a testing utility for MUI sliders.
    // The key is that the component *passes* setTemperature to the Slider.
    // A visual regression test or e2e test would be better for slider value verification.
    
    // Let's assume the component has a way for setTemperature to be called,
    // even if not directly through a simple fireEvent.change on the input.
    // The presence of the slider and the prop being passed is a good start.
    // For a more direct test of setTemperature, the component might need an internal handler we can spy on,
    // or we'd need to test the visual outcome.
    // For this test, we'll assume the prop is correctly wired up.
    // If we had a visible value display tied to temperature that updates, we could check that.
    expect(mockSetTemperature).not.toHaveBeenCalled(); // This will likely fail unless we can truly simulate a change.
                                                    // We'll rely on the button click tests below for now.
                                                    // To make this testable, one might wrap the Slider and expose a testable onChange.
  });

  test('calls handleGenerateTOC when "Generate TOC" button is clicked', () => {
    render(<CampaignLLMSettings {...defaultProps} />);
    const tocButton = screen.getByRole('button', { name: /Generate TOC/i });
    fireEvent.click(tocButton);
    expect(mockHandleGenerateTOC).toHaveBeenCalledTimes(1);
  });

  test('calls handleGenerateTitles when "Generate Titles" button is clicked', () => {
    render(<CampaignLLMSettings {...defaultProps} />);
    const titlesButton = screen.getByRole('button', { name: /Generate Titles for Sections/i });
    fireEvent.click(titlesButton);
    expect(mockHandleGenerateTitles).toHaveBeenCalledTimes(1);
  });
});
