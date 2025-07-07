import React, { useState, useEffect, FormEvent, useRef } from 'react';
import { getMe, updateUser, updateUserApiKeys, UserApiKeysPayload, uploadUserAvatar } from '../services/userService'; // Removed getMyFiles
import { User } from '../types/userTypes';
// Removed BlobFileMetadata import as it's no longer used here
import { useAuth } from '../contexts/AuthContext';
import Input from '../components/common/Input';
// LoadingSpinner import is confirmed removed as it's no longer used here.
import Button from '../components/common/Button';
import Tabs, { TabItem } from '../components/common/Tabs';
import ImageGenerationModal from '../components/modals/ImageGenerationModal/ImageGenerationModal';
// Removed renderFileRepresentation import as it's no longer used here
import './UserSettingsPage.css';

const STABLE_DIFFUSION_ENGINE_OPTIONS = [
  { value: "", label: "System Default" },
  { value: "core", label: "Core" },
  { value: "ultra", label: "Ultra (Experimental)" },
  { value: "sd3", label: "SD3 (Experimental)" },
];

const UserSettingsPage: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // State for new fields
  const [description, setDescription] = useState('');
  const [appearance, setAppearance] = useState('');

  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [sdApiKey, setSdApiKey] = useState('');
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [otherLlmApiKey, setOtherLlmApiKey] = useState('');
  const [apiKeyMessage, setApiKeyMessage] = useState<string | null>(null);
  const [apiKeyError, setApiKeyError] = useState<string | null>(null);
  const [isApiKeysLoading, setIsApiKeysLoading] = useState(false);

  const [sdEnginePreference, setSdEnginePreference] = useState('');
  const [sdSettingsMessage, setSdSettingsMessage] = useState<string | null>(null);
  const [sdSettingsError, setSdSettingsError] = useState<string | null>(null);
  const [isSdSettingsLoading, setIsSdSettingsLoading] = useState(false);

  const { user: authUser, setUser: setAuthUser, token } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('Profile');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarUploadError, setAvatarUploadError] = useState<string | null>(null);
  const [isAvatarUploading, setIsAvatarUploading] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showImageGenerationModal, setShowImageGenerationModal] = useState<boolean>(false);

  // State for User Files Tab - REMOVED
  // const [userFiles, setUserFiles] = useState<BlobFileMetadata[]>([]);
  // const [filesLoading, setFilesLoading] = useState<boolean>(false);
  // const [filesError, setFilesError] = useState<string | null>(null);


  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        let userToSet: User | null = null;
        if (authUser) {
          userToSet = authUser;
        } else {
          const user = await getMe();
          userToSet = user;
          if (setAuthUser) setAuthUser(user); // Make sure setAuthUser is called
        }
        setCurrentUser(userToSet);
        if (userToSet) {
          setSdEnginePreference(userToSet.sd_engine_preference || '');
          setDescription(userToSet.description || '');
          setAppearance(userToSet.appearance || '');
          // If avatar_url is present in the fetched user data, set the preview
          if (userToSet.avatar_url && !avatarPreview) { // only set if not already previewing a new file
            setAvatarPreview(userToSet.avatar_url);
          }
        }
      } catch (err) {
        setError('Failed to fetch user data.');
        console.error(err);
      }
    };
    fetchCurrentUser();
  }, [authUser, setAuthUser, avatarPreview]); // Added avatarPreview to prevent resetting preview during upload

  // Effect for fetching user files - ENTIRELY REMOVED as this logic moved to CampaignEditorPage

  // Helper function to format bytes - REMOVED (this was already done in previous step, ensuring it's gone)
  // const formatBytes = (bytes: number, decimals: number = 2): string => {
  //   if (bytes === 0) return '0 Bytes';
  //   const k = 1024;
  //   const dm = decimals < 0 ? 0 : decimals;
  //   const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  //   const i = Math.floor(Math.log(bytes) / Math.log(k));
  //   return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  // };

  const handleProfileSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (!currentUser) {
      setError('User data not loaded.');
      return;
    }

    const updatePayload: Partial<User> = {
        description: description,
        appearance: appearance,
    };

    if (newPassword) {
        if (newPassword !== confirmPassword) {
            setError('New passwords do not match.');
            return;
        }
        updatePayload.password = newPassword;
    }

    setIsLoading(true);
    try {
      // Assuming updateUser service can handle partial updates including password
      await updateUser(currentUser.id, updatePayload);
      setMessage('Profile updated successfully!');
      if (newPassword) {
          setNewPassword('');
          setConfirmPassword('');
          setCurrentPassword(''); // Clear current password field after successful update
      }
      // Refetch user data to update context and local state accurately
      const updatedUser = await getMe();
      if (setAuthUser) setAuthUser(updatedUser);
      setCurrentUser(updatedUser);
      setDescription(updatedUser.description || '');
      setAppearance(updatedUser.appearance || '');

    } catch (err: any) {
      let errorMessage = 'Failed to update profile.';
      if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string' ? err.response.data.detail : JSON.stringify(err.response.data.detail);
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiKeysSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setApiKeyError(null);
    setApiKeyMessage(null);
    setIsApiKeysLoading(true);
    const payload: UserApiKeysPayload = {
      openai_api_key: openaiApiKey,
      sd_api_key: sdApiKey,
      gemini_api_key: geminiApiKey,
      other_llm_api_key: otherLlmApiKey,
    };
    try {
      const updatedUser = await updateUserApiKeys(payload);
      setApiKeyMessage('API keys updated successfully!');
      if (setAuthUser) setAuthUser(updatedUser);
      setCurrentUser(updatedUser);
      setOpenaiApiKey('');
      setSdApiKey('');
      setGeminiApiKey('');
      setOtherLlmApiKey('');
    } catch (err: any) {
      let errorMessage = 'Failed to update API keys.';
      if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string' ? err.response.data.detail : JSON.stringify(err.response.data.detail);
      } else if (err.message) {
        errorMessage = err.message;
      }
      setApiKeyError(errorMessage);
    } finally {
      setIsApiKeysLoading(false);
    }
  };

  const triggerAvatarFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleAvatarFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Basic validation (e.g., file type, size) can be added here
      if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)) {
        setAvatarUploadError('Invalid file type. Please select an image (jpeg, png, gif, webp).');
        setAvatarFile(null);
        setAvatarPreview(null);
        return;
      }
      if (file.size > 2 * 1024 * 1024) { // 2MB limit example
        setAvatarUploadError('File is too large. Maximum 2MB allowed.');
        setAvatarFile(null);
        setAvatarPreview(null);
        return;
      }

      setAvatarFile(file);
      setAvatarUploadError(null);
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setAvatarFile(null);
      setAvatarPreview(null);
    }
  };

  const handleAvatarUpload = async () => {
    if (!avatarFile || !currentUser || !token) {
      setAvatarUploadError('No file selected or user not available.');
      return;
    }
    console.log("Avatar file to upload:", avatarFile); // DEBUG LOG
    setIsAvatarUploading(true);
    setAvatarUploadError(null);
    setMessage(null); // Clear other messages

    const formData = new FormData();
    formData.append('file', avatarFile);

    try {
      const updatedUser = await uploadUserAvatar(formData);
      console.log('Updated user from API:', updatedUser);

      if (setAuthUser) {
        setAuthUser(updatedUser);
      }
      setCurrentUser(updatedUser);

      setMessage('Avatar updated successfully!');
      setAvatarFile(null);
      setAvatarPreview(null);
      // Clear file input value if it's still holding the old file
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: any) {
      let errorMessage = 'Failed to upload avatar.';
      if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string' ? err.response.data.detail : JSON.stringify(err.response.data.detail);
      } else if (err.message) {
        errorMessage = err.message;
      }
      setAvatarUploadError(errorMessage);
    } finally {
      setIsAvatarUploading(false);
    }
  };

  // Function to handle setting avatar from generated URL
  const handleSetGeneratedAvatar = async (imageUrl: string) => {
    if (!currentUser || !token) {
      setAvatarUploadError('User not available. Cannot set avatar.');
      throw new Error('User not available');
    }
    console.log("Attempting to set generated avatar from URL:", imageUrl);
    setIsAvatarUploading(true); // Use the same loading state
    setAvatarUploadError(null);
    setMessage(null);

    try {
      // 1. Fetch the image data from the URL
      console.log(`[UserSettingsPage] handleSetGeneratedAvatar: Attempting to fetch image URL: ${imageUrl}`);
      let fetchResponse;
      try {
        fetchResponse = await fetch(imageUrl);
      } catch (fetchErr: any) {
        console.error(`[UserSettingsPage] handleSetGeneratedAvatar: Raw fetch error for URL ${imageUrl}:`, fetchErr);
        throw new Error(`Network error or CORS issue fetching image: ${fetchErr.message}`);
      }

      console.log(`[UserSettingsPage] handleSetGeneratedAvatar: Fetch response status: ${fetchResponse.status}, OK: ${fetchResponse.ok}`);
      if (!fetchResponse.ok) {
        // Log response body text if not OK, as it might contain error details from Azure/server
        const errorText = await fetchResponse.text().catch(() => "Could not read error response body.");
        console.error(`[UserSettingsPage] handleSetGeneratedAvatar: Fetch failed with status ${fetchResponse.status}. Response text:`, errorText);
        throw new Error(`Failed to fetch generated image: ${fetchResponse.status} ${fetchResponse.statusText}. Server response: ${errorText}`);
      }
      const imageBlob = await fetchResponse.blob();
      console.log(`[UserSettingsPage] handleSetGeneratedAvatar: Image blob fetched successfully. Type: ${imageBlob.type}, Size: ${imageBlob.size}`);

      // 2. Convert blob to File object
      // Try to get a filename from the URL, otherwise use a default
      let filename = "generated_avatar.png"; // Default filename
      try {
        const urlPath = new URL(imageUrl).pathname;
        const parts = urlPath.split('/');
        if (parts.length > 0) {
          const lastPart = parts[parts.length - 1];
          if (lastPart.includes('.')) { // Basic check for extension
            filename = lastPart;
          }
        }
      } catch (e) {
        console.warn("Could not parse filename from URL, using default.", e);
      }

      const imageFile = new File([imageBlob], filename, { type: imageBlob.type });
      console.log("Converted generated image to File:", imageFile);

      // 3. Call uploadUserAvatar (which expects FormData)
      const formData = new FormData();
      formData.append('file', imageFile);

      const updatedUser = await uploadUserAvatar(formData);
      console.log('User updated with generated avatar:', updatedUser);

      if (setAuthUser) {
        setAuthUser(updatedUser);
      }
      setCurrentUser(updatedUser);

      setMessage('Avatar updated successfully with generated image!');
      setAvatarPreview(updatedUser.avatar_url || null); // Update preview with the new URL, ensuring null if undefined
      setShowImageGenerationModal(false); // Close modal on success
    } catch (err: any) {
      let errorMessage = 'Failed to set generated avatar.';
      if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string' ? err.response.data.detail : JSON.stringify(err.response.data.detail);
      } else if (err.message) {
        errorMessage = err.message;
      }
      setAvatarUploadError(errorMessage); // Display error in the main page for now
      console.error('Error setting generated avatar:', err);
      throw err; // Re-throw to be caught by the modal if needed
    } finally {
      setIsAvatarUploading(false);
    }
  };

  const handleStableDiffusionSettingsSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSdSettingsError(null);
    setSdSettingsMessage(null);
    setIsSdSettingsLoading(true);
    if (!currentUser) {
      setSdSettingsError('User data not loaded.');
      setIsSdSettingsLoading(false);
      return;
    }
    try {
      const updatedUser = await updateUser(currentUser.id, {
        sd_engine_preference: sdEnginePreference === "" ? undefined : sdEnginePreference // Send undefined to clear
      });
      setSdSettingsMessage('Stable Diffusion settings updated successfully!');
      if (setAuthUser) setAuthUser(updatedUser);
      setCurrentUser(updatedUser);
      setSdEnginePreference(updatedUser.sd_engine_preference || '');
    } catch (err: any) {
      let errorMessage = 'Failed to update Stable Diffusion settings.';
       if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string' ? err.response.data.detail : JSON.stringify(err.response.data.detail);
      } else if (err.message) {
        errorMessage = err.message;
      }
      setSdSettingsError(errorMessage);
    } finally {
      setIsSdSettingsLoading(false);
    }
  };

  if (!currentUser) {
    return <div className="container"><p>Loading user data... If this persists, try logging out and back in.</p></div>;
  }

  const profileTabContent = (
    <div className="settings-tab-content">
      <h3>Profile Information</h3>
      <div className="settings-form-section read-only-info">
        <Input id="username-display" name="usernameDisplay" type="text" label="Username:" value={currentUser.username} disabled onChange={() => {}} />
        <Input id="email-display" name="emailDisplay" type="email" label="Email:" value={currentUser.email || ''} disabled onChange={() => {}} />
      </div>

      <h3>Update Profile Information</h3>
      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}
      <form onSubmit={handleProfileSubmit} className="profile-update-form settings-form-section">
        <Input
          id="description"
          name="description"
          type="textarea" // Changed to textarea for potentially longer input
          label="Description (optional):"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Tell us a bit about yourself..."
        />
        <Input
          id="appearance"
          name="appearance"
          type="text" // Could also be a select or other input type depending on what "appearance" means
          label="Appearance (optional):"
          value={appearance}
          onChange={(e) => setAppearance(e.target.value)}
          placeholder="E.g., 'Likes dark themes'"
        />

        <h4>Change Password (optional)</h4>
        {/* Current password might be needed if password is being changed, depends on backend logic. Assuming not for now. */}
        {/* <Input id="current-password" name="currentPassword" type="password" label="Current Password (if changing password):" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} /> */}
        <Input id="new-password" name="newPassword" type="password" label="New Password (leave blank to keep current):" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        <Input id="confirm-password" name="confirmPassword" type="password" label="Confirm New Password:" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} disabled={!newPassword} />

        <Button type="submit" variant="primary" disabled={isLoading} style={{marginTop: '1rem'}}>
          {isLoading ? 'Updating Profile...' : 'Save Profile Changes'}
        </Button>
      </form>

      <div className="settings-form-section profile-icon-section">
        <h3>Profile Icon</h3>
        <div className="current-profile-icon">
          {avatarPreview ? (
            <img src={avatarPreview} alt="Avatar preview" className="avatar-image-preview" />
          ) : currentUser?.avatar_url ? (
            <img src={currentUser.avatar_url} alt="Current avatar" className="avatar-image-preview" />
          ) : (
            <span className="user-icon-placeholder-large" aria-label="Current profile icon">👤</span>
          )}
        </div>
        <input
          type="file"
          accept="image/png, image/jpeg, image/gif, image/webp"
          onChange={handleAvatarFileChange}
          ref={fileInputRef}
          style={{ display: 'none' }}
          id="avatar-file-input"
        />
        {!avatarFile && (
          <Button
            variant="secondary"
            onClick={triggerAvatarFileInput}
            className="change-icon-button"
            aria-label="Change profile icon"
          >
            Choose Icon
          </Button>
        )}
        {avatarFile && (
          <div className="avatar-upload-actions">
            <Button
              variant="primary"
              onClick={handleAvatarUpload}
              disabled={isAvatarUploading}
              className="upload-avatar-button"
            >
              {isAvatarUploading ? 'Uploading...' : 'Upload Selected Icon'}
            </Button>
            <Button
              variant="outline-secondary"
              onClick={() => { setAvatarFile(null); setAvatarPreview(null); setAvatarUploadError(null); if(fileInputRef.current) fileInputRef.current.value = ''; }}
              disabled={isAvatarUploading}
              className="cancel-avatar-button"
            >
              Cancel
            </Button>
          </div>
        )}
        {avatarUploadError && <div className="message error" style={{marginTop: '10px'}}>{avatarUploadError}</div>}
        {/* Button for AI Generation (still stubbed) */}
        <Button
            variant="outline-secondary"
            onClick={() => setShowImageGenerationModal(true)} // Open the modal
            style={{marginTop: '10px', display: avatarFile ? 'none' : 'block' }}
            className="generate-icon-button"
            disabled={isAvatarUploading} // Disable if an upload is in progress
        >
            Generate Icon with AI
        </Button>
      </div>
    </div>
  );

  const apiKeysTabContent = (
    <div className="settings-tab-content">
      <h3>API Keys</h3>
      {apiKeyMessage && <div className="message success">{apiKeyMessage}</div>}
      {apiKeyError && <div className="message error">{apiKeyError}</div>}
      <form onSubmit={handleApiKeysSubmit} className="api-keys-form settings-form-section">
        <Input id="openai-api-key" name="openaiApiKey" type="password" label="OpenAI API Key:" value={openaiApiKey} onChange={(e) => setOpenaiApiKey(e.target.value)} placeholder={currentUser?.openai_api_key_provided ? "Key is set (leave blank to keep, type to update/clear)" : "Enter OpenAI API Key"} helperText={`Status: ${currentUser?.openai_api_key_provided ? 'Provided' : 'Not Provided'}. To clear/update, enter new key or leave blank and save.`} />
        <Input id="sd-api-key" name="sdApiKey" type="password" label="Stable Diffusion API Key:" value={sdApiKey} onChange={(e) => setSdApiKey(e.target.value)} placeholder={currentUser?.sd_api_key_provided ? "Key is set (leave blank to keep, type to update/clear)" : "Enter Stable Diffusion API Key"} helperText={`Status: ${currentUser?.sd_api_key_provided ? 'Provided' : 'Not Provided'}. To clear/update, enter new key or leave blank and save.`} />
        <Input id="gemini-api-key" name="geminiApiKey" type="password" label="Gemini API Key:" value={geminiApiKey} onChange={(e) => setGeminiApiKey(e.target.value)} placeholder={currentUser?.gemini_api_key_provided ? "Key is set (leave blank to keep, type to update/clear)" : "Enter Gemini API Key"} helperText={`Status: ${currentUser?.gemini_api_key_provided ? 'Provided' : 'Not Provided'}. To clear/update, enter new key or leave blank and save.`} />
        <Input id="other-llm-api-key" name="otherLlmApiKey" type="password" label="Other LLM API Key:" value={otherLlmApiKey} onChange={(e) => setOtherLlmApiKey(e.target.value)} placeholder={currentUser?.other_llm_api_key_provided ? "Key is set (leave blank to keep, type to update/clear)" : "Enter Other LLM API Key"} helperText={`Status: ${currentUser?.other_llm_api_key_provided ? 'Provided' : 'Not Provided'}. To clear/update, enter new key or leave blank and save.`} />
        <Button type="submit" variant="primary" disabled={isApiKeysLoading}>
          {isApiKeysLoading ? 'Saving Keys...' : 'Save API Keys'}
        </Button>
      </form>
    </div>
  );

  const preferencesTabContent = (
    <div className="settings-tab-content">
      <h3>Preferences</h3>
      <h4>Stable Diffusion Settings</h4>
      {sdSettingsMessage && <div className="message success">{sdSettingsMessage}</div>}
      {sdSettingsError && <div className="message error">{sdSettingsError}</div>}
      <form onSubmit={handleStableDiffusionSettingsSubmit} className="sd-settings-form settings-form-section">
        <div className="form-group">
          <label htmlFor="sd-engine-preference">Preferred Stable Diffusion Engine:</label>
          <select id="sd-engine-preference" name="sdEnginePreference" value={sdEnginePreference} onChange={(e) => setSdEnginePreference(e.target.value)} className="form-control">
            {STABLE_DIFFUSION_ENGINE_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <p className="form-helper-text">Select your preferred engine for Stable Diffusion image generation. "System Default" will use the server's configured default.</p>
        </div>
        <Button type="submit" variant="primary" disabled={isSdSettingsLoading}>
          {isSdSettingsLoading ? 'Saving...' : 'Save Stable Diffusion Settings'}
        </Button>
      </form>
    </div>
  );

  // const filesTabContent = (...) Block fully removed.

  const tabItems: TabItem[] = [
    { name: 'Profile', content: profileTabContent },
    { name: 'API Keys', content: apiKeysTabContent },
    { name: 'Preferences', content: preferencesTabContent },
  ];

  // Ensure activeTab state is initialized with one of these new names
  // If `activeTab` was 'profile', it should now be 'Profile'
  // This might require adjusting the initial state of activeTab if it was based on the old names.
  // For simplicity, assuming Tabs component or its usage handles default active tab gracefully or
  // the initial useState for activeTab is updated accordingly.
  // Let's ensure the initial activeTab is 'Profile' to match the first item.
  // The activeTab state is already initialized with 'profile'. We should update it to 'Profile'.
  // This requires changing the initial useState for activeTab:
  // const [activeTab, setActiveTab] = useState<string>('Profile'); // Changed from 'profile'

  return (
    <>
      <div className="user-settings-page modern-settings-layout container">
        <h2 className="page-title">My Settings</h2>
        <Tabs tabs={tabItems} activeTabName={activeTab === 'profile' ? 'Profile' : activeTab} onTabChange={setActiveTab} />
      </div>
      {showImageGenerationModal && (
        <ImageGenerationModal
          isOpen={showImageGenerationModal}
          onClose={() => {
            setShowImageGenerationModal(false);
            setAvatarUploadError(null); // Clear any previous avatar errors when closing modal
          }}
          // Pass handleSetGeneratedAvatar to the correct prop based on ImageGenerationModal's definition
          onImageSuccessfullyGenerated={handleSetGeneratedAvatar}
          primaryActionText="Set as Avatar" // This text might be used if autoApply is false
          autoApplyDefault={true} // We want to auto-apply for the avatar scenario
        />
      )}
    </>
  );
};

export default UserSettingsPage;
