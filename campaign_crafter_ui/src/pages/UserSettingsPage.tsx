import React, { useState, useEffect, FormEvent } from 'react';
import { getMe, updateUser, updateUserApiKeys, UserApiKeysPayload } from '../services/userService'; // Added updateUserApiKeys, UserApiKeysPayload
import { User } from '../types/userTypes';
import { useAuth } from '../contexts/AuthContext'; // Import useAuth
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import './UserSettingsPage.css';

const UserSettingsPage: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null); // For password change
  const [error, setError] = useState<string | null>(null); // For password change
  const [isLoading, setIsLoading] = useState(false); // For password change

  // New state for API Keys
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [sdApiKey, setSdApiKey] = useState('');
  const [apiKeyMessage, setApiKeyMessage] = useState<string | null>(null);
  const [apiKeyError, setApiKeyError] = useState<string | null>(null);
  const [isApiKeysLoading, setIsApiKeysLoading] = useState(false);
  const { user: authUser, setUser: setAuthUser } = useAuth(); // Get user and setUser from AuthContext

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        // Use user from AuthContext if available, otherwise fetch
        if (authUser) {
          setCurrentUser(authUser);
        } else {
          const user = await getMe();
          setCurrentUser(user);
          if (setAuthUser) setAuthUser(user); // Optionally update AuthContext if fetched manually
        }
      } catch (err) {
        setError('Failed to fetch user data.'); // This error state is for password form, consider separate for initial load
        console.error(err);
      }
    };
    fetchCurrentUser();
  }, [authUser, setAuthUser]); // Depend on authUser to re-fetch/re-set if it changes

  const handlePasswordSubmit = async (event: FormEvent<HTMLFormElement>) => {
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
      console.error(err); // Log the full error for debugging
      let errorMessage = 'Failed to update password.'; // Default message
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail) && detail.length > 0 && typeof detail[0].msg === 'string' && Array.isArray(detail[0].loc)) {
          // If detail is an array of validation errors (FastAPI style), take the first message.
          errorMessage = `Validation Error: ${detail[0].msg} (field: ${detail[0].loc.join(' > ')})`;
        } else if (typeof detail === 'object' && detail !== null && typeof (detail as any).message === 'string') {
          // If detail is an object with a message property
          errorMessage = (detail as any).message;
        } else if (typeof detail === 'object' && detail !== null) {
          // Fallback for other object structures, convert to string
          try {
            errorMessage = JSON.stringify(detail);
          } catch (stringifyError) {
            console.error("Failed to stringify error detail:", stringifyError);
            // Keep default error message if stringification fails
          }
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentUser) {
    return <div>Loading user data... If this persists, try logging out and back in.</div>;
  }

  // API Keys Submit Handler
  const handleApiKeysSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setApiKeyError(null);
    setApiKeyMessage(null);
    setIsApiKeysLoading(true);

    const payload: UserApiKeysPayload = {};
    // Send current input value. If field is empty string, backend interprets as clearing the key.
    payload.openai_api_key = openaiApiKey;
    payload.sd_api_key = sdApiKey;

    try {
      const updatedUser = await updateUserApiKeys(payload);
      setApiKeyMessage('API keys updated successfully!');
      if (setAuthUser) {
           setAuthUser(updatedUser); // Update user in AuthContext
      }
      setCurrentUser(updatedUser); // Update local state for the page
      setOpenaiApiKey(''); // Clear input field after successful submission
      setSdApiKey('');   // Clear input field after successful submission
    } catch (err: any) {
      let errorMessage = 'Failed to update API keys.';
      if (err.response?.data?.detail) {
          const detail = err.response.data.detail;
          if (typeof detail === 'string') {
            errorMessage = detail;
          } else if (Array.isArray(detail) && detail.length > 0 && typeof detail[0].msg === 'string') {
            errorMessage = `Validation Error: ${detail[0].msg}`; // Simplified error for now
          }
      } else if (err.message) {
          errorMessage = err.message;
      }
      setApiKeyError(errorMessage);
    } finally {
      setIsApiKeysLoading(false);
    }
  };

  return (
    <div className="user-settings-page">
      <h2>User Settings</h2>
      <h3>Change Password</h3>
      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}
      <form onSubmit={handlePasswordSubmit} className="password-change-form">
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

      {/* API Keys Form */}
      <h3>API Keys</h3>
      {apiKeyMessage && <div className="message success">{apiKeyMessage}</div>}
      {apiKeyError && <div className="message error">{apiKeyError}</div>}
      <form onSubmit={handleApiKeysSubmit} className="api-keys-form">
        <Input
          id="openai-api-key"
          name="openaiApiKey"
          type="password"
          label="OpenAI API Key:"
          value={openaiApiKey}
          onChange={(e) => setOpenaiApiKey(e.target.value)}
          placeholder={currentUser?.openai_api_key_provided ? "Key is set (leave blank to keep, type to update/clear)" : "Enter OpenAI API Key"}
          helperText={`Status: ${currentUser?.openai_api_key_provided ? 'Provided' : 'Not Provided'}. To clear a key, submit an empty field.`}
        />
        <Input
          id="sd-api-key"
          name="sdApiKey"
          type="password"
          label="Stable Diffusion API Key:"
          value={sdApiKey}
          onChange={(e) => setSdApiKey(e.target.value)}
          placeholder={currentUser?.sd_api_key_provided ? "Key is set (leave blank to keep, type to update/clear)" : "Enter Stable Diffusion API Key"}
          helperText={`Status: ${currentUser?.sd_api_key_provided ? 'Provided' : 'Not Provided'}. To clear a key, submit an empty field.`}
        />
        <Button type="submit" variant="primary" disabled={isApiKeysLoading}>
          {isApiKeysLoading ? 'Saving Keys...' : 'Save API Keys'}
        </Button>
      </form>
    </div>
  );
};

export default UserSettingsPage;
