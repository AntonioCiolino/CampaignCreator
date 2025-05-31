import React, { useState, useEffect } from 'react'; // Added useState here, though it was already present.
import { CampaignSection } from '../services/campaignService';
import ReactMarkdown from 'react-markdown';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css'; // Import Quill's snow theme CSS
import Button from './common/Button'; // Added Button import
import RandomTableRoller from './RandomTableRoller'; // Import RandomTableRoller
import './CampaignSectionView.css';
import { CampaignSectionUpdatePayload } from '../services/campaignService'; // Import the payload type

interface CampaignSectionViewProps {
  section: CampaignSection;
  onSave: (sectionId: number, updatedData: CampaignSectionUpdatePayload) => Promise<void>;
  isSaving: boolean; // Prop to indicate if this specific section is being saved
  saveError: string | null; // Prop to display save error for this section
  onDelete: (sectionId: number) => void; // Added onDelete prop
  forceCollapse?: boolean; // Optional prop to force collapse state
}

const CampaignSectionView: React.FC<CampaignSectionViewProps> = ({ section, onSave, isSaving, saveError: externalSaveError, onDelete, forceCollapse }) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(true); // Add isCollapsed state
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedContent, setEditedContent] = useState<string>(section.content);
  const [quillInstance, setQuillInstance] = useState<any>(null); // To store Quill instance if needed
  const [localSaveError, setLocalSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);


  // Ensure editedContent is updated if the section prop changes externally
  // (e.g. if parent component re-fetches and passes a new section object, or after a save)
  useEffect(() => {
    setEditedContent(section.content);
    // If the external save error for this section is cleared, clear local error too
    if (externalSaveError === null) {
        setLocalSaveError(null);
    }
  }, [section.content, externalSaveError]);

  useEffect(() => {
    if (forceCollapse !== undefined) {
      setIsCollapsed(forceCollapse);
    }
  }, [forceCollapse]);
  
  const handleEdit = () => {
    setIsCollapsed(false); // Expand section on edit
    setEditedContent(section.content); 
    setIsEditing(true);
    setLocalSaveError(null); // Clear local errors when starting to edit
    setSaveSuccess(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedContent(section.content); 
    setLocalSaveError(null);
    setSaveSuccess(false);
  };

  const handleInsertRandomItem = (itemText: string) => {
    // For now, append to the current content.
    // A more advanced implementation would insert at the cursor in ReactQuill.
    // This might require getting a ref to the Quill instance.
    setEditedContent(prevContent => {
      // Add a space if prevContent is not empty and doesn't end with a space
      const prefix = prevContent && !prevContent.endsWith(' ') && !prevContent.endsWith('\n') ? " " : "";
      return prevContent + prefix + itemText;
    });
    // If you have the Quill instance, you could do:
    // if (quillInstance) {
    //   const range = quillInstance.getSelection(true);
    //   quillInstance.insertText(range.index, itemText, 'user');
    // }
  };

  const handleSave = async () => {
    setLocalSaveError(null);
    setSaveSuccess(false);
    try {
      // For now, only content is editable in this component.
      // Title/order would be handled elsewhere or if this component is expanded.
      await onSave(section.id, { content: editedContent });
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000); // Display success for 3s
    } catch (error) {
      console.error("Failed to save section content:", error);
      // The error might already be set by the parent via `externalSaveError`
      // if the parent re-throws. We can also set a local one.
      setLocalSaveError('Failed to save. Please try again.');
      // No need to re-throw if parent is already handling and passing `saveError` prop
    }
  };

  const quillModules = {
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike', 'blockquote'],
      [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}],
      ['link', /*'image'*/], // Image uploads would require more setup
      ['clean']
    ],
  };

  const quillFormats = [
    'header',
    'bold', 'italic', 'underline', 'strike', 'blockquote',
    'list', 'bullet', 'indent',
    'link', /*'image'*/
  ];

  return (
    <div className="campaign-section-view">
      {section.title && (
        <div className="section-title-header" onClick={() => setIsCollapsed(!isCollapsed)}>
          <h3 className="section-title">
            {isCollapsed ? '▶' : '▼'} {section.title}
          </h3>
        </div>
      )}

      {!isCollapsed && (
        <>
          {isEditing ? (
            <div className="section-editor">
              <ReactQuill
                theme="snow"
                value={editedContent}
                onChange={setEditedContent}
                modules={quillModules}
                formats={quillFormats}
                className="quill-editor"
                // Consider getting a ref to the Quill instance if more advanced control is needed
                // ref={(el) => { if (el) setQuillInstance(el.getEditor()); }}
              />
              {/* Random Table Roller Integration */}
              <RandomTableRoller onInsertItem={handleInsertRandomItem} />

              <div className="editor-actions">
                <button onClick={handleSave} className="editor-button save-button" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save Content'}
                </button>
                <button onClick={handleCancel} className="editor-button cancel-button" disabled={isSaving}>
                  Cancel
                </button>
                {localSaveError && <p className="error-message editor-feedback">{localSaveError}</p>}
                {externalSaveError && !localSaveError && <p className="error-message editor-feedback">{externalSaveError}</p>}
                {saveSuccess && <p className="success-message editor-feedback">Content saved!</p>}
              </div>
            </div>
          ) : (
            <>
              <div className="section-content">
                <ReactMarkdown>{section.content}</ReactMarkdown>
              </div>
              <div className="view-actions">
                <button onClick={handleEdit} className="editor-button edit-button">
                  Edit Section Content
                </button>
                <Button
                  onClick={() => onDelete(section.id)}
                  variant="danger"
                  size="sm"
                  className="editor-button delete-button" // Keep existing classes if they add value
                  style={{ marginLeft: '10px' }}
                >
                  Delete Section
                </Button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default CampaignSectionView;
