import React, { useState, useEffect, FormEvent } from 'react';
// Use AppUser from userTypes for userToEdit prop
import { AppUser } from '../../types/userTypes';
// Payloads can still come from userService as they are specific to service calls
import { UserCreatePayload, UserUpdatePayload } from '../services/userService';
import Input from './common/Input';
import Checkbox from './common/Checkbox';
import Button from './common/Button';
import './UserForm.css';

interface UserFormProps {
  userToEdit?: AppUser | null; // Use AppUser
  onSubmit: (data: UserCreatePayload | UserUpdatePayload, isEditing: boolean) => Promise<void>;
  onCancel: () => void;
  formError?: string | null;
}

const UserForm: React.FC<UserFormProps> = ({ userToEdit, onSubmit, onCancel, formError }) => {
  const isEditing = Boolean(userToEdit);

  const [username, setUsername] = useState(''); // Added username
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [disabled, setDisabled] = useState(false); // Changed from isActive, default false (not disabled)
  const [isSuperuser, setIsSuperuser] = useState(false);

  const [internalError, setInternalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);


  useEffect(() => {
    if (userToEdit) {
      setUsername(userToEdit.username);
      setEmail(userToEdit.email || ''); // Email is optional
      setFullName(userToEdit.full_name || '');
      setDisabled(userToEdit.disabled); // Use disabled
      setIsSuperuser(userToEdit.is_superuser);
      setPassword('');
      setConfirmPassword('');
    } else {
      setUsername('');
      setEmail('');
      setFullName('');
      setDisabled(false); // Default for new user
      setIsSuperuser(false);
      setPassword('');
      setConfirmPassword('');
    }
  }, [userToEdit]);

  const validateForm = (): boolean => {
    setInternalError(null);
    if (!username.trim()) { // Validate username
      setInternalError('Username is required.');
      return false;
    }
    // Email is optional in backend, so only validate format if provided
    if (email.trim() && !/\S+@\S+\.\S+/.test(email)) {
      setInternalError('Email is invalid.');
      return false;
    }
    if (!isEditing && !password) {
      setInternalError('Password is required for new users.');
      return false;
    }
    if (password && password !== confirmPassword) {
      setInternalError('Passwords do not match.');
      return false;
    }
    return true;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!validateForm()) {
      return;
    }
    setIsSubmitting(true);

    // UserCreatePayload: username, password, email?, full_name?, is_superuser?
    // UserUpdatePayload: username?, email?, password?, full_name?, disabled?, is_superuser?

    let payload: UserCreatePayload | UserUpdatePayload;

    if (isEditing) {
      const updateData: UserUpdatePayload = {
        username: username, // username is part of UserBase, so can be updated
        email: email || undefined, // Send undefined if empty to not clear it if not intended
        full_name: fullName || undefined,
        disabled: disabled,
        is_superuser: isSuperuser,
      };
      if (password) { // Only include password if it's being changed
        updateData.password = password;
      }
      payload = updateData;
    } else {
      payload = {
        username: username,
        password: password, // Password is required for UserCreatePayload
        email: email || undefined,
        full_name: fullName || undefined,
        is_superuser: isSuperuser,
        // 'disabled' is not part of UserCreatePayload, defaults to false on backend
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
        id="user-username" // Added username field
        name="username"
        type="text"
        label="Username:"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
        disabled={isEditing} // Username might not be editable
      />
      <Input
        id="user-email"
        name="email"
        type="email"
        label="Email (optional):"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        // Removed required as email is optional
      />
      <Input
        id="user-fullName"
        name="fullName"
        type="text"
        label="Full Name (optional):"
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
        autoComplete="new-password" // Keep autocomplete for password managers
        required={!isEditing} // Required only for new users
      />
      <Input
        id="user-confirmPassword"
        name="confirmPassword"
        type="password"
        label={isEditing && !password ? "Confirm New Password (if changing)" : "Confirm Password:"}
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        autoComplete="new-password"
        // Required if password is being set/changed
        required={(!isEditing && password !== '') || (isEditing && password !== '')}
        disabled={!password} // Disable if password field is empty
      />
      <Checkbox
        id="user-disabled" // Changed from isActive to disabled
        name="disabled"
        label="Disabled" // Label reflects the state
        checked={disabled} // Checked if user is disabled
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDisabled(e.target.checked)}
      />
      <Checkbox
        id="user-isSuperuser"
        name="isSuperuser"
        label="Superuser"
        checked={isSuperuser}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setIsSuperuser(e.target.checked)}
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
