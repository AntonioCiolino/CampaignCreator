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
} from '@mui/material';
import { LLM } from '../../utils/llm'; // Assuming LLM type is defined here

interface CampaignLLMSettingsProps {
  selectedLLM: LLM;
  setSelectedLLM: (llm: LLM) => void;
  temperature: number;
  setTemperature: (temp: number) => void;
  isGeneratingTOC: boolean;
  handleGenerateTOC: () => void;
  isGeneratingTitles: boolean;
  handleGenerateTitles: () => void;
  availableLLMs: LLM[]; // Assuming this prop will be passed from the parent
}

const CampaignLLMSettings: React.FC<CampaignLLMSettingsProps> = ({
  selectedLLM,
  setSelectedLLM,
  temperature,
  setTemperature,
  isGeneratingTOC,
  handleGenerateTOC,
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
                onChange={(e) => {
                  const foundLLM = availableLLMs.find(llm => llm.id === e.target.value);
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
              onChange={(_, newValue) => setTemperature(newValue as number)}
              aria-labelledby="temperature-slider"
              valueLabelDisplay="auto"
              step={0.1}
              marks
              min={0}
              max={1}
              sx={{ mb: 1 }} // Added margin bottom for spacing before buttons
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Button
              variant="contained"
              color="secondary"
              onClick={handleGenerateTOC}
              disabled={isGeneratingTOC || isGeneratingTitles}
              fullWidth
            >
              {isGeneratingTOC ? 'Generating TOC...' : 'Generate TOC'}
            </Button>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Button
              variant="contained"
              color="secondary"
              onClick={handleGenerateTitles}
              disabled={isGeneratingTitles || isGeneratingTOC}
              fullWidth
            >
              {isGeneratingTitles ? 'Generating Titles...' : 'Generate Titles for Sections'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default CampaignLLMSettings;
