import React from 'react';
import {
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
  availableLLMs: LLM[]; // Assuming this prop will be passed from the parent
  // Props related to title generation (isGeneratingTitles, handleGenerateTitles) are removed.
  // titlesError might also be removed if it was only for the generate titles button.
}

const CampaignLLMSettings: React.FC<CampaignLLMSettingsProps> = ({
  selectedLLM,
  setSelectedLLM,
  temperature,
  setTemperature,
  availableLLMs,
  // Removed isGeneratingTitles and handleGenerateTitles from destructured props
}) => {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          LLM Settings
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
              sx={{ mb: 1 }}
            />
          </Grid>
          {/* The Grid item for "Suggest Campaign Titles" button has been removed. */}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default CampaignLLMSettings;
