import React, { useState, useEffect } from 'react';
import { CampaignSection } from '../services/campaignService';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import ReactQuill, { Quill } from 'react-quill';
import type { RangeStatic as QuillRange } from 'quill'; // Import QuillRange
import 'react-quill/dist/quill.snow.css'; // Import Quill's snow theme CSS
import Button from './common/Button'; // Added Button import
import RandomTableRoller from './RandomTableRoller';
import ImageGenerationModal from './modals/ImageGenerationModal/ImageGenerationModal'; // Import the new modal
import './CampaignSectionView.css';
import { CampaignSectionUpdatePayload } from '../services/campaignService';
import { generateTextLLM, LLMTextGenerationParams } from '../services/llmService'; // Added import

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
  const [editedContent, setEditedContent] = useState<string>(section.content || '');
  const [quillInstance, setQuillInstance] = useState<any>(null); // Enabled to store Quill instance
  const [localSaveError, setLocalSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [isImageGenerationModalOpen, setIsImageGenerationModalOpen] = useState<boolean>(false);
  const [isGeneratingContent, setIsGeneratingContent] = useState<boolean>(false);
  const [contentGenerationError, setContentGenerationError] = useState<string | null>(null);


  // Ensure editedContent is updated if the section prop changes externally
  // (e.g. if parent component re-fetches and passes a new section object, or after a save)
  useEffect(() => {
    setEditedContent(section.content || '');
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
    setEditedContent(section.content || '');
    setIsEditing(true);
    setLocalSaveError(null); // Clear local errors when starting to edit
    setSaveSuccess(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedContent(section.content || '');
    setLocalSaveError(null);
    setSaveSuccess(false);
    setContentGenerationError(null); // Clear content generation error on cancel
  };

  const handleGenerateContent = async () => {
    setIsGeneratingContent(true);
    setContentGenerationError(null);
    let initialSelectionRange: QuillRange | null = null; // Use QuillRange

    try {
      let contextText = '';
      if (quillInstance) {
        initialSelectionRange = quillInstance.getSelection();
        if (initialSelectionRange && initialSelectionRange.length > 0) {
          contextText = quillInstance.getText(initialSelectionRange.index, initialSelectionRange.length);
        } else {
          // Get all text if no selection, but trim it to avoid overly long contexts.
          // Or consider a configurable max context length.
          const fullText = quillInstance.getText();
          contextText = fullText.substring(0, 2000); // Limit context length
        }
      } else {
        contextText = editedContent.substring(0, 2000); // Fallback and limit
      }

      const prompt = `Based on the following context, generate additional relevant content. If the context is a question, answer it. If it's a statement, expand on it or provide related information. Context: ${contextText}`;

      const params: LLMTextGenerationParams = {
        prompt: prompt,
        model_id_with_prefix: null, // Use default model
        // Add any other params like max_tokens, temperature if needed
      };

      const response = await generateTextLLM(params);
      const generatedText = response.text; // Changed generated_text to text

      if (quillInstance) {
        // It's good practice to get the selection again right before an operation,
        // as focus might have shifted, though less likely in this specific async flow.
        const currentSelection = initialSelectionRange || quillInstance.getSelection();

        if (currentSelection && currentSelection.length > 0) {
          // Replace selected text
          quillInstance.deleteText(currentSelection.index, currentSelection.length, 'user');
          quillInstance.insertText(currentSelection.index, generatedText, 'user');
          // Move cursor to the end of the inserted text
          quillInstance.setSelection(currentSelection.index + generatedText.length, 0, 'user');
        } else {
          // Append to the end of the editor
          const endPosition = quillInstance.getLength() > 1 ? quillInstance.getLength() -1 : 0; // Quill has a default newline
          quillInstance.insertText(endPosition, (endPosition > 0 ? "\n" : "") + generatedText, 'user');
           // Move cursor to the end of the inserted text
          quillInstance.setSelection(endPosition + (endPosition > 0 ? 1 : 0) + generatedText.length, 0, 'user');
        }
        setEditedContent(quillInstance.root.innerHTML);
      } else {
        // Fallback: Append to editedContent state
        // This won't handle replacing selected text if quillInstance was initially null.
        setEditedContent(prev => prev + "\n" + generatedText);
      }

    } catch (error) {
      console.error("Failed to generate content:", error);
      setContentGenerationError('Failed to generate content. An error occurred.');
    } finally {
      setIsGeneratingContent(false);
    }
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
    toolbar: {
      container: [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike', 'blockquote'],
        [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}],
        ['link', 'image'], // Enabled 'image'
        ['clean']
      ]
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
                <Button onClick={handleSave} className="editor-button" disabled={isSaving || isGeneratingContent}>
                  {isSaving ? 'Saving...' : 'Save Content'}
                </Button>
                <Button onClick={handleGenerateContent} className="editor-button" disabled={isGeneratingContent || isSaving}>
                  {isGeneratingContent ? 'Generating...' : 'Generate Content'}
                </Button>
                <Button onClick={() => setIsImageGenerationModalOpen(true)} className="editor-button" disabled={isGeneratingContent || isSaving}>
                  Generate Image
                </Button>
                <Button onClick={handleCancel} className="editor-button" variant="secondary" disabled={isSaving || isGeneratingContent}>
                  Cancel
                </Button>
                {localSaveError && <p className="error-message editor-feedback">{localSaveError}</p>}
                {externalSaveError && !localSaveError && <p className="error-message editor-feedback">{externalSaveError}</p>}
                {contentGenerationError && <p className="error-message editor-feedback">{contentGenerationError}</p>}
                {saveSuccess && <p className="success-message editor-feedback">Content saved!</p>}
              </div>
            </div>
          ) : (
            <>
              <div className="section-content">
                <ReactMarkdown rehypePlugins={[rehypeRaw]}>{section.content}</ReactMarkdown>
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
            quillInstance.insertEmbed(range.index, 'image', imageUrl, 'user');
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
