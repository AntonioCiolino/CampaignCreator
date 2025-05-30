import React from 'react';
import './Checkbox.css'; // For styling

interface CheckboxProps {
  id?: string;
  name?: string;
  label: string;
  checked: boolean;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  className?: string; // Allow custom classes
}

const Checkbox: React.FC<CheckboxProps> = ({
  id,
  name,
  label,
  checked,
  onChange,
  disabled = false,
  className = '',
}) => {
  return (
    <label htmlFor={id || name} className={`checkbox-label ${className} ${disabled ? 'disabled' : ''}`}>
      <input
        type="checkbox"
        id={id || name}
        name={name}
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className="checkbox-input"
      />
      <span className="checkbox-custom"></span> {/* For custom styling of the checkbox appearance */}
      <span className="checkbox-text">{label}</span>
    </label>
  );
};

export default Checkbox;
