import React, { useState, useEffect, FormEvent } from 'react';
import { User, UserCreatePayload, UserUpdatePayload } from '../services/userService';
import Input from './common/Input'; // Assuming common Input component
import Checkbox from './common/Checkbox'; // Assuming common Checkbox component
import Button from './common/Button'; // Assuming common Button component
import './UserForm.css'; // We'll create this CSS file

interface UserFormProps {
  userToEdit?: User | null;
  onSubmit: (data: UserCreatePayload | UserUpdatePayload, isEditing: boolean) => Promise<void>;
  onCancel: () => void;
  formError?: string | null; // For displaying errors from the parent (e.g., API errors)
}

const UserForm: React.FC<UserFormProps> = ({ userToEdit, onSubmit, onCancel, formError }) => {
  const isEditing = Boolean(userToEdit);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [isSuperuser, setIsSuperuser] = useState(false);

  const [internalError, setInternalError] = useState<string | null>(null); // For client-side validation errors
  const [isSubmitting, setIsSubmitting] = useState(false);


  useEffect(() => {
    if (userToEdit) {
      setEmail(userToEdit.email);
      setFullName(userToEdit.full_name || '');
      setIsActive(userToEdit.is_active);
      setIsSuperuser(userToEdit.is_superuser);
      // Password fields are kept blank for editing unless user types a new one
      setPassword('');
      setConfirmPassword('');
    } else {
      // Defaults for new user form
      setEmail('');
      setFullName('');
      setIsActive(true);
      setIsSuperuser(false);
      setPassword('');
      setConfirmPassword('');
    }
  }, [userToEdit]);

  const validateForm = (): boolean => {
    setInternalError(null);
    if (!email.trim()) {
      setInternalError('Email is required.');
      return false;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setInternalError('Email is invalid.');
      return false;
    }
    if (!isEditing && !password) { // Password required for new users
      setInternalError('Password is required for new users.');
      return false;
    }
    if (password && password !== confirmPassword) {
      setInternalError('Passwords do not match.');
      return false;
    }
    // Add more validations as needed (e.g., password complexity)
    return true;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!validateForm()) {
      return;
    }
    setIsSubmitting(true);

    const commonData = {
      email,
      full_name: fullName || null, // Ensure null if empty, or backend handles empty string
      is_active: isActive,
      is_superuser: isSuperuser,
    };

    let payload: UserCreatePayload | UserUpdatePayload;

    if (isEditing) {
      payload = {
        ...commonData,
        // Only include password if it's being changed
        ...(password && { password }),
      } as UserUpdatePayload;
    } else {
      payload = {
        ...commonData,
        password, // Password is required for UserCreatePayload
      } as UserCreatePayload;
    }

    try {
      await onSubmit(payload, isEditing);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="user-form">
      {formError && <div className="error-message form-error">{formError}</div>}
      {internalError && <div className="error-message internal-error">{internalError}</div>}

      <Input
        id="user-email"
        name="email"
        type="email"
        label="Email:"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <Input
        id="user-fullName"
        name="fullName"
        type="text"
        label="Full Name:"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
      />
      <Input
        id="user-password"
        name="password"
        type="password"
        label={isEditing ? "New Password (leave blank to keep current):" : "Password:"}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        autoComplete="new-password"
        required={!isEditing}
      />
      <Input
        id="user-confirmPassword"
        name="confirmPassword"
        type="password"
        label="Confirm Password:"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        autoComplete="new-password"
        required={!isEditing || (isEditing && password !== '')}
        disabled={!isEditing && !password} // Disable if new user and no password yet
      />
      <Checkbox
        id="user-isActive"
        name="isActive"
        label="Active"
        checked={isActive}
        onChange={(e) => setIsActive(e.target.checked)}
      />
      <Checkbox
        id="user-isSuperuser"
        name="isSuperuser"
        label="Superuser"
        checked={isSuperuser}
        onChange={(e) => setIsSuperuser(e.target.checked)}
      />
      <div className="form-actions">
        <Button type="submit" variant="primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : (isEditing ? 'Save Changes' : 'Create User')}
        </Button>
        <Button type="button" onClick={onCancel} variant="secondary" disabled={isSubmitting}>
          Cancel
        </Button>
      </div>
    </form>
  );
};

export default UserForm;
