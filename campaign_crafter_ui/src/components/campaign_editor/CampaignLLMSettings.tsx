import React from 'react';
import {
  Button,
  Grid,
  Typography,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Box,
  SelectChangeEvent, // Import SelectChangeEvent
} from '@mui/material';
import { LLMModel as LLM } from '../../services/llmService'; // Corrected import path and type

interface CampaignLLMSettingsProps {
  selectedLLM: LLM;
  setSelectedLLM: (llm: LLM) => void;
  temperature: number;
  setTemperature: (temp: number) => void;
  isGeneratingTitles: boolean;
  handleGenerateTitles: () => void;
  availableLLMs: LLM[]; // Assuming this prop will be passed from the parent
}

const CampaignLLMSettings: React.FC<CampaignLLMSettingsProps> = ({
  selectedLLM,
  setSelectedLLM,
  temperature,
  setTemperature,
  isGeneratingTitles,
  handleGenerateTitles,
  availableLLMs,
}) => {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          LLM Settings & Actions
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel id="llm-select-label">Select LLM</InputLabel>
              <Select
                labelId="llm-select-label"
                value={selectedLLM.id}
                label="Select LLM"
                onChange={(e: SelectChangeEvent<string>) => { // Typed event parameter
                  const modelId = e.target.value;
                  const foundLLM = availableLLMs.find(llm => llm.id === modelId);
                  if (foundLLM) {
                    setSelectedLLM(foundLLM);
                  }
                }}
              >
                {availableLLMs.map((llm) => (
                  <MenuItem key={llm.id} value={llm.id}>
                    {llm.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography gutterBottom>Temperature</Typography>
            <Slider
              value={temperature}
              onChange={(_: Event, newValue: number | number[]) => { // Typed parameters
                if (typeof newValue === 'number') {
                  setTemperature(newValue);
                }
              }}
              aria-labelledby="temperature-slider"
              valueLabelDisplay="auto"
              step={0.1}
              marks
              min={0}
              max={1}
              sx={{ mb: 1 }} // Added margin bottom for spacing before buttons
            />
          </Grid>
          {/* Removed TOC Button Grid Item */}
          <Grid item xs={12} sm={6}> {/* Adjusted sm to 6 if only one button left, or keep 12 for full width */}
            <Button
              variant="contained"
              color="secondary"
              onClick={handleGenerateTitles}
              disabled={isGeneratingTitles}
              fullWidth
            >
              {isGeneratingTitles ? 'Generating Titles...' : 'Suggest Campaign Titles'} {/* Changed text slightly for clarity */}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default CampaignLLMSettings;
