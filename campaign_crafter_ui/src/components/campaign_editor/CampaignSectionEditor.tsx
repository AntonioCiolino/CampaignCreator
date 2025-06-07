import React from 'react';
import {
  Button,
  // Grid, // Removed Grid
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
import DragIndicatorIcon from '@mui/icons-material/DragIndicator'; 
import { CampaignSection, CampaignSectionUpdatePayload } from '../../services/campaignService'; // Corrected import
import CampaignSectionView from '../CampaignSectionView';
import { 
  DragDropContext, 
  Droppable, 
  Draggable, 
  DropResult, 
  DroppableProvided, // For typing
  DroppableStateSnapshot, // For typing
  DraggableProvided, // For typing
  DraggableStateSnapshot // For typing
} from 'react-beautiful-dnd';

interface CampaignSectionEditorProps {
  sections: CampaignSection[];
  setSections: React.Dispatch<React.SetStateAction<CampaignSection[]>>;
  handleAddNewSection: () => void;
  handleDeleteSection: (sectionId: number) => void; // Changed sectionId to number
  // These direct handlers might be replaced if onSave handles all updates
  handleUpdateSectionContent: (sectionId: number, newContent: string) => void; // Changed sectionId to number
  handleUpdateSectionTitle: (sectionId: number, newTitle: string) => void; // Changed sectionId to number
  handleUpdateSectionType: (sectionId: number, newType: string) => void; // Added for type updates
  onUpdateSectionOrder: (orderedSectionIds: number[]) => Promise<void>;
  forceCollapseAllSections?: boolean; // Added new prop
  isAddSectionDisabled?: boolean; // Prop to disable the "Add New Section" button
  campaignId: string | number; // Added campaignId prop
}

const CampaignSectionEditor: React.FC<CampaignSectionEditorProps> = ({
  sections,
  setSections,
  handleAddNewSection,
  handleDeleteSection,
  handleUpdateSectionContent, // Keep this prop
  handleUpdateSectionTitle,   // Keep this prop for now, though CampaignSectionView might not edit title
  handleUpdateSectionType,  // Destructure new prop
  onUpdateSectionOrder,
  forceCollapseAllSections, // Destructure the new prop
  isAddSectionDisabled = false, // Destructure and default to false
  campaignId, // Destructure campaignId
}) => {
  const onDragEnd = (result: DropResult) => { // Removed ResponderProvided as it's not typically used in onDragEnd
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

    setSections(items); // Optimistic update

    const orderedSectionIds = items.map(item => typeof item.id === 'string' ? parseInt(item.id, 10) : item.id);
    
    onUpdateSectionOrder(orderedSectionIds).catch(() => {
      // Error handling (reverting) is done in CampaignEditorPage's handleUpdateSectionOrder
    });
  };

  // This function will be passed as the onSave prop to CampaignSectionView
  const handleSectionViewSave = async (sectionId: number, updatedData: CampaignSectionUpdatePayload) => {
    // CampaignSectionView's onSave currently only sends content
    if (updatedData.content !== undefined) {
      await handleUpdateSectionContent(sectionId, updatedData.content);
    }
    if (updatedData.title !== undefined) { // Assuming CampaignSectionView might also update title via its own mechanism
      await handleUpdateSectionTitle(sectionId, updatedData.title);
    }
    if (updatedData.type !== undefined) { // Handle type update
      await handleUpdateSectionType(sectionId, updatedData.type);
    }
  };

  const handleSectionUpdated = (updatedSection: CampaignSection) => {
    setSections((prevSections: CampaignSection[]) => // Add type for prevSections
      prevSections.map((s: CampaignSection) => // Add type for s
        s.id === updatedSection.id ? updatedSection : s
      )
    );
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
            disabled={isAddSectionDisabled}
            title={isAddSectionDisabled ? "Please define and save a campaign concept in the 'Details' tab first." : "Add a new section to the campaign"}
          >
            Add New Section
          </Button>
        </Box>
        <DragDropContext onDragEnd={onDragEnd}>
          <Droppable droppableId="campaignSections">
            {(provided: DroppableProvided, snapshot: DroppableStateSnapshot) => (
              <List
                {...provided.droppableProps}
                ref={provided.innerRef}
                sx={{
                  background: snapshot.isDraggingOver ? 'lightblue' : 'inherit',
                  padding: snapshot.isDraggingOver ? '8px' : '0',
                  transition: 'background-color 0.2s ease, padding 0.2s ease',
                  minHeight: '50px', // Ensure droppable area has some height
                }}
              >
                {sections.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ padding: '16px', textAlign: 'center' }}>
                    No sections yet. Click 'Add New Section' to begin.
                  </Typography>
                ) : (
                  sections.map((section, index) => (
                    <Draggable key={section.id.toString()} draggableId={section.id.toString()} index={index}>
                      {(providedDraggable: DraggableProvided, snapshotDraggable: DraggableStateSnapshot) => (
                        <Paper
                          ref={providedDraggable.innerRef}
                          {...providedDraggable.draggableProps}
                          elevation={snapshotDraggable.isDragging ? 4 : 2}
                          sx={{
                            mb: 2,
                            display: 'flex',
                            alignItems: 'center',
                            border: snapshotDraggable.isDragging ? '2px dashed #ccc' : '2px solid transparent',
                            background: snapshotDraggable.isDragging ? '#f0f0f0' : 'white',
                          }}
                        >
                          <Box {...providedDraggable.dragHandleProps} sx={{ pl: 1, pr: 1, cursor: 'grab', display: 'flex', alignItems: 'center' }}>
                            <DragIndicatorIcon />
                          </Box>
                          <Box sx={{ width: '100%', p: 1 }}>
                            <CampaignSectionView
                              section={section}
                              campaignId={campaignId} // Pass campaignId
                              onSectionUpdated={handleSectionUpdated} // Pass the new handler
                              onSave={(sectionIdFromView, data) => handleSectionViewSave(sectionIdFromView, data)}
                              isSaving={false} // TODO: Manage individual section saving state
                              saveError={null} // TODO: Manage individual section error state
                              onDelete={() => handleDeleteSection(typeof section.id === 'string' ? parseInt(section.id, 10) : section.id)}
                              forceCollapse={forceCollapseAllSections} // Pass the prop here
                              // Pass the type update handler to CampaignSectionView
                              onSectionTypeUpdate={(sectionId, newType) => {
                                // Update local state first for responsiveness
                                setSections(prevSections =>
                                  prevSections.map(s =>
                                    s.id === sectionId ? { ...s, type: newType } : s
                                  )
                                );
                                // Then call the actual update handler passed from parent
                                handleUpdateSectionType(sectionId, newType);
                              }}
                            />
                          </Box>
                          <IconButton
                            edge="end"
                            aria-label="delete"
                            onClick={() => handleDeleteSection(typeof section.id === 'string' ? parseInt(section.id, 10) : section.id)}
                            color="error"
                            sx={{ ml: 1, mr: 1 }}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Paper>
                      )}
                    </Draggable>
                  ))
                )}
                {provided.placeholder}
              </List>
            )}
          </Droppable>
        </DragDropContext>
      </CardContent>
    </Card>
  );
};

export default CampaignSectionEditor;
