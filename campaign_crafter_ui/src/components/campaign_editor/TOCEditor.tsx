import React, { useState, useEffect } from 'react';
import { TOCEntry } from '../../types/campaignTypes'; // Corrected import path
import { TextField, Button, IconButton, List, Box, Typography, Paper, Autocomplete } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
  DroppableProvided,
  DraggableProvided,
  DraggableStateSnapshot
} from 'react-beautiful-dnd';

// Define available types for the dropdown
const AVAILABLE_SECTION_TYPES = ["generic", "character", "npc", "location", "chapter", "item", "quest", "note", "world_detail", "monster"];

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
                    <Paper
                      ref={providedDraggable.innerRef}
                      {...providedDraggable.draggableProps}
                      elevation={snapshotDraggable.isDragging ? 4 : 1}
                      sx={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        padding: 1, // Adjusted padding
                        border: snapshotDraggable.isDragging ? '2px dashed #ccc' : '1px solid #eee',
                        borderRadius: '4px', // Added from previous successful patch
                        marginBottom: 2, // Added from prompt example
                        backgroundColor: snapshotDraggable.isDragging ? 'action.hover' : 'background.paper', // Added from previous
                      }}
                    >
                      <Box {...providedDraggable.dragHandleProps} sx={{ cursor: 'grab', marginRight: 1, display: 'flex', alignItems: 'center' }}>
                        <DragIndicatorIcon />
                      </Box>
                      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                        <TextField
                          label="Title"
                          variant="outlined"
                          size="small"
                          value={entry.title}
                          onChange={(e) => handleInputChange(index, 'title', e.target.value)}
                          sx={{ marginBottom: 1 }}
                        />
                        <Autocomplete
                          freeSolo
                          options={AVAILABLE_SECTION_TYPES}
                          value={entry.type}
                          onChange={(event: any, newValue: string | null) => {
                            const newTOC = editableTOC.map((e, i) =>
                              i === index ? { ...e, type: newValue || '' } : e
                            );
                            setEditableTOC(newTOC);
                            onTOCChange(newTOC);
                          }}
                          onInputChange={(event: any, newInputValue: string) => {
                            const newTOC = editableTOC.map((e, i) =>
                              i === index ? { ...e, type: newInputValue } : e
                            );
                            setEditableTOC(newTOC);
                            onTOCChange(newTOC);
                          }}
                          renderInput={(params) => (
                            <TextField
                              {...params}
                              label="Type"
                              variant="outlined"
                              size="small"
                            />
                          )}
                          sx={{ minWidth: 180 }} // Adjust width as needed
                          size="small"
                        />
                      </Box>
                      <IconButton onClick={() => handleDeleteEntry(index)} edge="end" aria-label="delete" color="error" sx={{ marginLeft: 1 }}>
                        <DeleteIcon />
                      </IconButton>
                    </Paper>
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
    </DragDropContext> // Added the closing tag here
  );
};

export default TOCEditor;
