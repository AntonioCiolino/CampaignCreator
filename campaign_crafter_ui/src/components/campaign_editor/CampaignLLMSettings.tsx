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
  // Box, // Removed Box
  SelectChangeEvent, // Import SelectChangeEvent
} from '@mui/material';
import { LLMModel as LLM } from '../../services/llmService'; // Corrected import path and type

interface CampaignLLMSettingsProps {
  selectedLLM: LLM | null; // Allow null for when no model is selected or available
  setSelectedLLM: (llm: LLM | null) => void; // Allow null
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
        <Grid container spacing={2} alignItems="flex-start"> {/* Changed alignItems for better layout with more info */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth sx={{ mb: 1 }}> {/* Reduced margin bottom */}
              <InputLabel id="llm-select-label">Select LLM</InputLabel>
              <Select
                labelId="llm-select-label"
                value={selectedLLM ? selectedLLM.id : ''} // Handle null case for value
                label="Select LLM"
                onChange={(e: SelectChangeEvent<string>) => { // Typed event parameter
                  const modelId = e.target.value;
                  if (modelId === "") {
                    setSelectedLLM(null);
                  } else {
                    const foundLLM = availableLLMs.find(llm => llm.id === modelId);
                    if (foundLLM) {
                      setSelectedLLM(foundLLM);
                    }
                  }
                }}
              >
                <MenuItem value="">
                  <em>None (Use default or no LLM)</em>
                </MenuItem>
                {availableLLMs.map((llm) => (
                  <MenuItem key={llm.id} value={llm.id}>
                    {llm.name} ({llm.model_type})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {selectedLLM && (
              <div style={{ marginTop: '8px', paddingLeft: '8px' }}> {/* Added some spacing */}
                <Typography variant="body2" color="textSecondary">
                  Model Type: {selectedLLM.model_type}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Temperature Control: {selectedLLM.supports_temperature ? "Supported" : "Not Supported"}
                </Typography>
              </div>
            )}
          </Grid>

          {selectedLLM && selectedLLM.supports_temperature && (
            <Grid item xs={12} sm={6}>
              <Typography gutterBottom>Temperature: {temperature.toFixed(1)}</Typography>
              <Slider
                value={temperature}
                onChange={(_: Event, newValue: number | number[]) => { // Typed parameters
                  if (typeof newValue === 'number') {
                    setTemperature(newValue);
                  }
                }}
                aria-labelledby="temperature-slider"
                valueLabelDisplay="auto" // Changed to auto for better UX, or remove if label above is enough
                step={0.1}
                marks
                min={0}
                max={1.0} // Max 1.0 is safer for most models
                sx={{ mt: 0, mb: 1 }} // Adjusted margin top
              />
            </Grid>
          )}
          {/* The Grid item for "Suggest Campaign Titles" button has been removed. */}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default CampaignLLMSettings;
