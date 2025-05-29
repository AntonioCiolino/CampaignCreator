import React, { ChangeEvent, HTMLInputTypeAttribute } from 'react';
import './Input.css'; // Import the CSS file

export interface InputProps {
  /** The ID of the input element */
  id?: string;
  /** The name of the input element */
  name?: string;
  /** The type of the input element (e.g., 'text', 'email', 'password', 'number') */
  type?: HTMLInputTypeAttribute;
  /** Current value of the input */
  value: string | number;
  /** Change event handler */
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  /** Placeholder text for the input */
  placeholder?: string;
  /** Is the input disabled? */
  disabled?: boolean;
  /** Optional additional CSS class to apply to the input element itself */
  className?: string;
  /** Optional label text to display above the input */
  label?: string;
  /** Optional error message to display below the input */
  error?: string | null;
  /** Optional CSS class for the wrapper div */
  wrapperClassName?: string;
  /** Standard input props can be passed directly, e.g. 'aria-describedby' */
  [x: string]: any; // Allows passing other HTML attributes like aria-label, etc.
}

/**
 * A reusable Input component that leverages global form styling
 * and provides a consistent structure for labels and error messages.
 */
const Input: React.FC<InputProps> = ({
  id,
  name,
  type = 'text',
  value,
  onChange,
  placeholder,
  disabled = false,
  className = '',
  label,
  error,
  wrapperClassName = '',
  ...props // Spread other native input props
}) => {
  const inputId = id || name; // Use name as fallback for id if id is not provided for label linking

  const baseInputClasses = 'form-input input-component'; // from App.css and Input.css
  const errorClass = error ? 'input-error' : ''; // from Input.css
  const finalInputClasses = [baseInputClasses, errorClass, className].filter(Boolean).join(' ');

  const wrapperClasses = ['input-wrapper', wrapperClassName].filter(Boolean).join(' ');

  return (
    <div className={wrapperClasses}>
      {label && (
        <label htmlFor={inputId} className="input-label">
          {label}
        </label>
      )}
      <input
        id={inputId}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        className={finalInputClasses}
        aria-invalid={!!error} // Indicate error state for accessibility
        {...(error && { 'aria-describedby': `${inputId}-error` })} // Link error message for screen readers
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="input-component-error-message" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;
