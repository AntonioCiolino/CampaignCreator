import React, { ChangeEvent, useRef, useState } from 'react';
import Button from './Button'; // Assuming Button component is in the same directory
import './FileInput.css';   // Styles for this component

export interface FileInputProps {
  /** Unique ID for the input and label association */
  id: string;
  /** Label text to display above or beside the file input area */
  label?: string;
  /** Comma-separated string of accepted file types (e.g., ".json,.zip") */
  accept?: string;
  /** Callback function when a file is selected or cleared */
  onFileSelected: (file: File | null) => void;
  /** Text for the button that triggers file selection */
  buttonText?: string;
  /** Optional additional CSS class for the main wrapper div */
  className?: string;
  /** Is the file input disabled? */
  disabled?: boolean;
  /** Placeholder for the filename display area when no file is selected */
  noFileSelectedText?: string;
}

/**
 * A styled file input component that uses a button to trigger the native file chooser
 * and displays the name of the selected file.
 */
const FileInput: React.FC<FileInputProps> = ({
  id,
  label,
  accept,
  onFileSelected,
  buttonText = 'Choose File',
  className = '',
  disabled = false,
  noFileSelectedText = 'No file selected',
}) => {
  const [selectedFileName, setSelectedFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files ? event.target.files[0] : null;
    setSelectedFileName(file ? file.name : '');
    onFileSelected(file);
    // Reset the input value so that selecting the same file again still triggers onChange
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const wrapperClasses = `file-input-wrapper ${disabled ? 'disabled' : ''} ${className}`.trim();

  return (
    <div className={wrapperClasses}>
      {label && (
        <label htmlFor={`${id}-button`} className="file-input-label"> {/* Label points to button for better UX */}
          {label}
        </label>
      )}
      <input
        type="file"
        id={id}
        ref={fileInputRef}
        accept={accept}
        onChange={handleFileChange}
        disabled={disabled}
        className="file-input-hidden" // Visually hide the default input
        aria-hidden="true" // Hide from accessibility tree as we have a button
      />
      <Button
        onClick={handleButtonClick}
        variant="secondary" // Or make variant a prop
        disabled={disabled}
        className="file-input-custom-trigger"
        type="button" // Ensure it's not a submit button if inside a form
        aria-label={label ? `${label}: ${buttonText}` : buttonText}
      >
        {buttonText}
      </Button>
      <span className="file-input-filename" aria-live="polite">
        {selectedFileName || noFileSelectedText}
      </span>
    </div>
  );
};

export default FileInput;
