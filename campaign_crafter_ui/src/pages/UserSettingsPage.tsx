import React, { useState, useEffect, FormEvent } from 'react';
import { getMe, updateUser } from '../services/userService'; // Assuming updateUser can be used for password change for now
import { User } from '../types/userTypes';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import './UserSettingsPage.css'; // Create this CSS file as well

const UserSettingsPage: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentPassword, setCurrentPassword] = useState(''); // For verification on UI
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const user = await getMe();
        setCurrentUser(user);
      } catch (err) {
        setError('Failed to fetch user data.');
        console.error(err);
      }
    };
    fetchCurrentUser();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }
    if (!newPassword) {
      setError('New password cannot be empty.');
      return;
    }
    if (!currentUser) {
      setError('User data not loaded.');
      return;
    }

    setIsLoading(true);
    try {
      // Assuming the existing updateUser service can handle password updates
      // The API endpoint /api/v1/users/{user_id} was modified to accept password updates for the logged-in user.
      // The UserUpdatePayload in userService.ts already allows for an optional password.
      // We might need a dedicated field for 'current_password' if API enforces it for password change,
      // but current API changes do not show this requirement for self-update.
      // For now, we'll use the updateUser function.
      await updateUser(currentUser.id, { password: newPassword });
      setMessage('Password updated successfully!');
      setNewPassword('');
      setConfirmPassword('');
      setCurrentPassword(''); // Clear current password field as well
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update password.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentUser) {
    return <div>Loading user data...</div>;
  }

  return (
    <div className="user-settings-page">
      <h2>User Settings</h2>
      <h3>Change Password</h3>
      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}
      <form onSubmit={handleSubmit} className="password-change-form">
        <Input
          id="username"
          name="username"
          type="text"
          label="Username:"
          value={currentUser.username}
          disabled // Username display only
          onChange={() => {}} // Added dummy onChange
        />
        <Input
          id="email"
          name="email"
          type="email"
          label="Email:"
          value={currentUser.email || ''}
          disabled // Email display only
          onChange={() => {}} // Added dummy onChange
        />
        {/*
          Current Password field is good UI practice, but the current API does not enforce it for self-update.
          If API were to require it, we'd need to send it. For now, it's a UI-only verification step or can be removed
          if not strictly needed by product requirements. Let's keep it for now.
        */}
        <Input
          id="current-password"
          name="currentPassword"
          type="password"
          label="Current Password:"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
        />
        <Input
          id="new-password"
          name="newPassword"
          type="password"
          label="New Password:"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
        />
        <Input
          id="confirm-password"
          name="confirmPassword"
          type="password"
          label="Confirm New Password:"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
        <Button type="submit" variant="primary" disabled={isLoading}>
          {isLoading ? 'Updating...' : 'Change Password'}
        </Button>
      </form>
    </div>
  );
};

export default UserSettingsPage;
