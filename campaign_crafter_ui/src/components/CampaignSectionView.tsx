import React, { useState, useEffect } from 'react';
import { CampaignSection } from '../services/campaignService';
import ReactMarkdown from 'react-markdown';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css'; // Import Quill's snow theme CSS
import Button from './common/Button'; // Added Button import
import RandomTableRoller from './RandomTableRoller';
import ImageGenerationModal from './modals/ImageGenerationModal/ImageGenerationModal'; // Import the new modal
import './CampaignSectionView.css';
import { CampaignSectionUpdatePayload } from '../services/campaignService';

interface CampaignSectionViewProps {
  section: CampaignSection;
  onSave: (sectionId: number, updatedData: CampaignSectionUpdatePayload) => Promise<void>;
  isSaving: boolean; // Prop to indicate if this specific section is being saved
  saveError: string | null; // Prop to display save error for this section
  onDelete: (sectionId: number) => void; // Added onDelete prop
  forceCollapse?: boolean; // Optional prop to force collapse state
}

const CampaignSectionView: React.FC<CampaignSectionViewProps> = ({ section, onSave, isSaving, saveError: externalSaveError, onDelete, forceCollapse }) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(true); 
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedContent, setEditedContent] = useState<string>(section.content);
  const [quillInstance, setQuillInstance] = useState<any>(null); // Enabled to store Quill instance
  const [localSaveError, setLocalSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [isImageGenerationModalOpen, setIsImageGenerationModalOpen] = useState<boolean>(false);


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

  const handleImageInsert = () => {
    if (!quillInstance) {
      console.error("Quill instance not available");
      return;
    }
    const url = prompt('Enter image URL:');
    if (url) {
      const range = quillInstance.getSelection(true); // Get selection or default to current cursor position
      // If there's a selection, it will be replaced by the image. 
      // If no selection, it inserts at the cursor.
      quillInstance.insertEmbed(range.index, 'image', url, ReactQuill.sources.USER);
    }
  };

  const quillModules = {
    toolbar: {
      container: [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike', 'blockquote'],
        [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}],
        ['link', 'image'], // Enabled 'image'
        ['clean']
      ],
      handlers: {
        image: handleImageInsert, // Assign custom image handler
      }
    },
  };

  const quillFormats = [
    'header',
    'bold', 'italic', 'underline', 'strike', 'blockquote',
    'list', 'bullet', 'indent',
    'link', 'image' // Added 'image'
  ];

  // Function to get the Quill instance
  const setQuillRef = (el: ReactQuill | null) => {
    if (el) {
      setQuillInstance(el.getEditor());
    }
  };

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
                ref={setQuillRef} // Set the ref to get Quill instance
              />
              {/* Random Table Roller Integration */}
              <RandomTableRoller onInsertItem={handleInsertRandomItem} />
              
              <div className="editor-actions">
                <Button onClick={handleSave} className="editor-button" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save Content'}
                </Button>
                <Button onClick={() => setIsImageGenerationModalOpen(true)} className="editor-button">
                  Generate Image
                </Button>
                <Button onClick={handleCancel} className="editor-button" variant="secondary" disabled={isSaving}>
                  Cancel
                </Button>
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
      <ImageGenerationModal
        isOpen={isImageGenerationModalOpen}
        onClose={() => setIsImageGenerationModalOpen(false)}
        // onImageGenerated={(imageUrl) => {
        //   // Optionally insert the image URL into the editor or handle as needed
        //   console.log("Generated image URL:", imageUrl);
        //   // Example: Insert into Quill (would require quillInstance)
        //   // if (quillInstance) {
        //   //   const range = quillInstance.getSelection(true) || { index: editedContent.length, length: 0 };
        //   //   quillInstance.insertEmbed(range.index, 'image', imageUrl, 'user');
        //   //   // Or, to insert as markdown if your editor handles it:
        //   //   // quillInstance.insertText(range.index, `\n![Generated Image](${imageUrl})\n`, 'user');
        //   //   setEditedContent(quillInstance.root.innerHTML); // Or however you get content from Quill
        //   // } else {
        //   // Fallback: append to text state if no Quill instance
        //     setEditedContent(prev => `${prev}\n![Generated Image](${imageUrl})\n`);
        //   // }
        //   setIsImageGenerationModalOpen(false); // Close modal after generation
        // }}
        // This modal is for AI image generation, the toolbar button is for URL insertion.
        // If AI generated image URL needs to be inserted into editor, the onImageSuccessfullyGenerated
        // prop for ImageGenerationModal (if it's added) could use a similar logic to handleImageInsert.
        onImageSuccessfullyGenerated={(imageUrl) => { // Example if you want to connect it
          if (quillInstance) {
            const range = quillInstance.getSelection(true) || { index: editedContent.length, length: 0 };
            quillInstance.insertEmbed(range.index, 'image', imageUrl, ReactQuill.sources.USER);
          } else {
            setEditedContent(prev => `${prev}\n![Generated Image](${imageUrl})\n`);
          }
          setIsImageGenerationModalOpen(false);
        }}
      />
    </div>
  );
};

export default CampaignSectionView;
