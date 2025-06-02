import React from 'react';
import {
  Button,
  Grid,
  Typography,
  Card,
  CardContent,
  Box,
  IconButton,
  List,
  // ListItem, // Will be replaced by Draggable
  // ListItemText,
  Paper,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator'; // For drag handle
import { CampaignSection } from '../../types'; 
import CampaignSectionView from '../CampaignSectionView';
import { DragDropContext, Droppable, Draggable, DropResult, ResponderProvided } from 'react-beautiful-dnd';

interface CampaignSectionEditorProps {
  sections: CampaignSection[];
  setSections: (sections: CampaignSection[]) => void; // Keep for optimistic updates if parent doesn't handle it all
  handleAddNewSection: () => void;
  handleDeleteSection: (sectionId: string) => void;
  handleUpdateSectionContent: (sectionId: string, newContent: string) => void;
  handleUpdateSectionTitle: (sectionId: string, newTitle: string) => void;
  onUpdateSectionOrder: (orderedSectionIds: number[]) => Promise<void>; // Add this prop
}

const CampaignSectionEditor: React.FC<CampaignSectionEditorProps> = ({
  sections,
  setSections,
  handleAddNewSection,
  handleDeleteSection,
  handleUpdateSectionContent,
  handleUpdateSectionTitle,
  onUpdateSectionOrder,
}) => {
  const onDragEnd = (result: DropResult, provided: ResponderProvided) => {
    const { source, destination } = result;

    // Dropped outside the list
    if (!destination) {
      return;
    }

    // If dropped in the same place
    if (destination.droppableId === source.droppableId && destination.index === source.index) {
      return;
    }

    const items = Array.from(sections);
    const [reorderedItem] = items.splice(source.index, 1);
    items.splice(destination.index, 0, reorderedItem);

    // Update local state for immediate UI feedback (optimistic update)
    setSections(items);

    // Prepare array of IDs in the new order
    const orderedSectionIds = items.map(item => parseInt(item.id, 10)); // Ensure IDs are numbers if they are not already

    // Call the handler passed from parent to update backend
    onUpdateSectionOrder(orderedSectionIds).catch(() => {
      // If backend update fails, revert to original order (or handle error appropriately)
      // For simplicity, current CampaignEditorPage's handleUpdateSectionOrder handles error by reverting.
      // Here, we could also revert if setSections was purely local and not also an optimistic update from parent.
    });
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Campaign Sections</Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddCircleOutlineIcon />}
            onClick={handleAddNewSection}
          >
            Add New Section
          </Button>
        </Box>
        {sections.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No sections yet. Click "Add New Section" to begin.
          </Typography>
        ) : (
          <DragDropContext onDragEnd={onDragEnd}>
            <Droppable droppableId="campaignSections">
              {(provided, snapshot) => (
                <List
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  sx={{
                    background: snapshot.isDraggingOver ? 'lightblue' : 'inherit',
                    padding: snapshot.isDraggingOver ? '8px' : '0', // Visual cue for drop area
                    transition: 'background-color 0.2s ease, padding 0.2s ease',
                  }}
                >
                  {sections.map((section, index) => (
                    <Draggable key={section.id.toString()} draggableId={section.id.toString()} index={index}>
                      {(provided, snapshot) => (
                        <Paper
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          elevation={snapshot.isDragging ? 4 : 2} // Higher elevation when dragging
                          sx={{ 
                            mb: 2, 
                            display: 'flex', 
                            alignItems: 'center',
                            border: snapshot.isDragging ? '2px dashed #ccc' : '2px solid transparent', // Dragging border
                            background: snapshot.isDragging ? '#f0f0f0' : 'white', // Background change when dragging
                          }}
                        >
                          <Box {...provided.dragHandleProps} sx={{ pl: 1, pr: 1, cursor: 'grab', display: 'flex', alignItems: 'center' }}>
                            <DragIndicatorIcon />
                          </Box>
                          <Box sx={{ width: '100%', p: 1 }}> {/* Ensure content takes full width */}
                            <CampaignSectionView
                              section={section}
                              onContentChange={(newContent) => handleUpdateSectionContent(section.id, newContent)}
                              onTitleChange={(newTitle) => handleUpdateSectionTitle(section.id, newTitle)}
                            />
                          </Box>
                          <IconButton
                            edge="end"
                            aria-label="delete"
                            onClick={() => handleDeleteSection(section.id)}
                            color="error"
                            sx={{ ml: 1, mr:1 }} // Margin for spacing
                          >
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
          </DragDropContext>
        )}
      </CardContent>
    </Card>
  );
};

export default CampaignSectionEditor;
