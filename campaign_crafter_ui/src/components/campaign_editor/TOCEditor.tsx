import React, { useState, useEffect } from 'react';
import { TOCEntry } from '../../services/campaignService';
import { TextField, Button, IconButton, List, ListItem, Box, Typography, Select, MenuItem, FormControl, InputLabel, SelectChangeEvent, Paper } from '@mui/material'; // Added Paper
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator'; // Added DragIndicatorIcon
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
  DroppableProvided, // For typing Droppable
  DraggableProvided,  // For typing Draggable
  DraggableStateSnapshot // For styling based on drag state
} from 'react-beautiful-dnd';

// Define available types for the dropdown
const AVAILABLE_SECTION_TYPES = ["generic", "character", "location", "chapter", "item", "quest", "note", "world_detail", "monster"];

interface TOCEditorProps {
  toc: TOCEntry[];
  onTOCChange: (newTOC: TOCEntry[]) => void;
  // availableTypes?: string[]; // Using hardcoded AVAILABLE_SECTION_TYPES for now
}

const TOCEditor: React.FC<TOCEditorProps> = ({ toc, onTOCChange }) => {
  const [editableTOC, setEditableTOC] = useState<TOCEntry[]>([]);

  useEffect(() => {
    // Initialize editableTOC when the toc prop changes
    // Create a deep copy to avoid modifying the original prop directly
    setEditableTOC(toc.map(entry => ({ ...entry })));
  }, [toc]);

  const handleInputChange = (index: number, field: keyof TOCEntry, value: string) => {
    const newTOC = editableTOC.map((entry, i) =>
      i === index ? { ...entry, [field]: value } : entry
    );
    setEditableTOC(newTOC);
    onTOCChange(newTOC); // Propagate changes immediately
  };

  const handleTypeChange = (index: number, event: SelectChangeEvent<string>) => {
    const newType = event.target.value;
    const newTOC = editableTOC.map((entry, i) =>
      i === index ? { ...entry, type: newType } : entry
    );
    setEditableTOC(newTOC);
    onTOCChange(newTOC);
  };

  const handleAddEntry = () => {
    const newEntry: TOCEntry = { title: 'New Section', type: 'generic' };
    const newTOC = [...editableTOC, newEntry];
    setEditableTOC(newTOC);
    onTOCChange(newTOC);
  };

  const handleDeleteEntry = (index: number) => {
    const newTOC = editableTOC.filter((_, i) => i !== index);
    setEditableTOC(newTOC);
    onTOCChange(newTOC);
  };

  const onDragEnd = (result: DropResult) => {
    const { source, destination } = result;
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const items = Array.from(editableTOC);
    const [reorderedItem] = items.splice(source.index, 1);
    items.splice(destination.index, 0, reorderedItem);

    setEditableTOC(items);
    onTOCChange(items);
  };

  if (!editableTOC) {
    return <Typography>Loading TOC...</Typography>;
  }

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Box sx={{ padding: 2, border: '1px solid #ccc', borderRadius: '4px' }}>
        <Typography variant="h6" gutterBottom>
          Edit Table of Contents
        </Typography>
        <Droppable droppableId="tocEntries">
          {(provided: DroppableProvided) => (
            <List {...provided.droppableProps} ref={provided.innerRef}>
              {editableTOC.map((entry, index) => (
                <Draggable key={`${entry.title}-${index}`} draggableId={`${entry.title}-${index}`} index={index}>
                  {(providedDraggable: DraggableProvided, snapshotDraggable: DraggableStateSnapshot) => (
                    <ListItem
                      ref={providedDraggable.innerRef}
                      {...providedDraggable.draggableProps}
                      disablePadding
                      sx={{ marginBottom: 1 }} // Adjusted margin to ListItem
                    >
                      <Paper
                        elevation={snapshotDraggable.isDragging ? 4 : 1}
                        sx={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          padding: 1.5, // Increased padding a bit
                          border: snapshotDraggable.isDragging ? '2px dashed #ccc' : '1px solid #eee',
                          borderRadius: '4px',
                          backgroundColor: snapshotDraggable.isDragging ? 'action.hover' : 'background.paper',
                        }}
                      >
                        <Box {...providedDraggable.dragHandleProps} sx={{ cursor: 'grab', marginRight: 1.5, display: 'flex', alignItems: 'center' }}>
                          <DragIndicatorIcon />
                        </Box>
                        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                          <TextField
                            label="Title"
                            variant="outlined"
                            size="small"
                            value={entry.title}
                            onChange={(e) => handleInputChange(index, 'title', e.target.value)}
                            sx={{ marginBottom: 1.5 }}
                          />
                          <FormControl size="small" sx={{ minWidth: 150 }}>
                            <InputLabel id={`type-label-${index}`}>Type</InputLabel>
                            <Select
                              labelId={`type-label-${index}`}
                              value={entry.type}
                              label="Type"
                              onChange={(e) => handleTypeChange(index, e)}
                            >
                              {AVAILABLE_SECTION_TYPES.map((typeOption) => (
                                <MenuItem key={typeOption} value={typeOption}>
                                  {typeOption.charAt(0).toUpperCase() + typeOption.slice(1)}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Box>
                        <IconButton onClick={() => handleDeleteEntry(index)} aria-label="delete" color="error" sx={{ marginLeft: 1.5 }}>
                          <DeleteIcon />
                        </IconButton>
                      </Paper>
                    </ListItem>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </List>
          )}
        </Droppable>
        <Button
          variant="contained"
        startIcon={<AddCircleOutlineIcon />}
        onClick={handleAddEntry}
        sx={{ marginTop: 2 }}
      >
        Add TOC Entry
      </Button>
    </Box>
  );
};

export default TOCEditor;
