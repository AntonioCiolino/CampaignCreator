import React, { useState, useEffect, useCallback, FormEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as characterService from '../services/characterService';
import { PydanticCharacter, CharacterCreatePayload, CharacterUpdatePayload, CharacterImage } from '../types/characterTypes';
import CharacterStatsEditor from '../components/CharacterStatsEditor';
import CharacterImageGallery from '../components/CharacterImageGallery';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Button from '../components/common/Button';
import Input from '../components/common/Input'; // Assuming a common Input component
import Textarea from '../components/common/Textarea'; // Assuming a common Textarea component
import Checkbox from '../components/common/Checkbox'; // Assuming a common Checkbox component
import Tabs, { TabItem } from '../components/common/Tabs'; // Assuming a common Tabs component
import './CharacterEditorPage.css'; // CSS for styling

const CharacterEditorPage: React.FC = () => {
  const { campaignId, characterId } = useParams<{ campaignId: string; characterId?: string }>();
  const navigate = useNavigate();
  const isNewCharacter = characterId === 'new' || characterId === undefined;

  const [character, setCharacter] = useState<PydanticCharacter | null>(null);
  const [formData, setFormData] = useState<Partial<CharacterCreatePayload | CharacterUpdatePayload>>({
    name: '',
    icon_url: '',
    stats: {},
    notes: '',
    chatbot_enabled: false,
    images: [],
  });
  const [isLoading, setIsLoading] = useState<boolean>(!isNewCharacter);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('Details');

  const fetchCharacterData = useCallback(async () => {
    if (!isNewCharacter && characterId && campaignId) {
      setIsLoading(true);
      setError(null);
      try {
        const fetchedCharacter = await characterService.getCharacterById(characterId);
        setCharacter(fetchedCharacter);
        setFormData({
          name: fetchedCharacter.name,
          icon_url: fetchedCharacter.icon_url || '',
          stats: fetchedCharacter.stats || {},
          notes: fetchedCharacter.notes || '',
          chatbot_enabled: fetchedCharacter.chatbot_enabled || false,
          images: fetchedCharacter.images || [],
        });
      } catch (err) {
        console.error('Failed to fetch character:', err);
        setError('Failed to load character data. Please try again.');
      } finally {
        setIsLoading(false);
      }
    } else if (isNewCharacter) {
      // Initialize form for new character
      setFormData({
        name: '',
        icon_url: '',
        stats: {},
        notes: '',
        chatbot_enabled: false,
        images: [],
      });
      setIsLoading(false);
    }
  }, [characterId, campaignId, isNewCharacter]);

  useEffect(() => {
    fetchCharacterData();
  }, [fetchCharacterData]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: checked }));
  };

  const handleStatsChange = (newStats: Record<string, string>) => {
    setFormData(prev => ({ ...prev, stats: newStats }));
  };

  const handleImagesChange = (newImages: CharacterImage[]) => {
    setFormData(prev => ({ ...prev, images: newImages }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!campaignId) {
      setError("Campaign ID is missing. Cannot save character.");
      return;
    }
    if (!formData.name?.trim()) {
      setError("Character name cannot be empty.");
      setActiveTab("Details"); // Switch to details tab if name is missing
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      let savedCharacter;
      if (isNewCharacter) {
        const payload: CharacterCreatePayload = {
          name: formData.name!, // Name is checked not to be empty
          icon_url: formData.icon_url || null,
          stats: formData.stats || {},
          notes: formData.notes || null,
          chatbot_enabled: formData.chatbot_enabled || false,
          images: formData.images || [],
        };
        savedCharacter = await characterService.createCharacter(campaignId, payload);
        navigate(`/campaign/${campaignId}/character/${savedCharacter.id}`); // Navigate to edit page of new char
      } else if (characterId) {
        const payload: CharacterUpdatePayload = {
          name: formData.name,
          icon_url: formData.icon_url || null,
          stats: formData.stats,
          notes: formData.notes || null,
          chatbot_enabled: formData.chatbot_enabled,
          images: formData.images,
        };
        savedCharacter = await characterService.updateCharacter(characterId, payload);
        setCharacter(savedCharacter); // Update local state
      }
      // Optionally show a success message
      alert('Character saved successfully!');
    } catch (err) {
      console.error('Failed to save character:', err);
      setError('Failed to save character. Please check the details and try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleExportCharacter = async () => {
    if (characterId && !isNewCharacter) {
      try {
        const data = await characterService.exportCharacterData(characterId);
        const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(data)}`;
        const link = document.createElement("a");
        link.href = jsonString;
        link.download = `${formData.name || 'character'}_export.json`;
        link.click();
        document.body.removeChild(link); // Clean up
      } catch (err) {
        console.error("Failed to export character data:", err);
        setError("Failed to export character data.");
      }
    } else {
      alert("Please save the character before exporting.");
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  const detailsTabContent = (
    <div className="form-section">
      <Input
        label="Character Name"
        id="name"
        name="name"
        value={formData.name || ''}
        onChange={handleInputChange}
        placeholder="E.g., Elara Meadowlight"
        required
      />
      <Input
        label="Icon URL"
        id="icon_url"
        name="icon_url"
        type="url"
        value={formData.icon_url || ''}
        onChange={handleInputChange}
        placeholder="Link to character's icon or portrait"
      />
      {formData.icon_url && (
        <div className="icon-preview-container">
          <img src={formData.icon_url} alt="Icon Preview" className="icon-preview" />
        </div>
      )}
      <CharacterStatsEditor
        stats={formData.stats || {}}
        onStatsChange={handleStatsChange}
      />
    </div>
  );

  const notesTabContent = (
    <div className="form-section">
      <Textarea
        label="Notes"
        id="notes"
        name="notes"
        value={formData.notes || ''}
        onChange={handleInputChange}
        rows={10}
        placeholder="Background story, personality traits, important connections, plot hooks, etc."
      />
    </div>
  );

  const imagesTabContent = (
    <div className="form-section">
      <CharacterImageGallery
        images={formData.images || []}
        onImagesChange={handleImagesChange}
        campaignId={campaignId}
        characterName={formData.name}
      />
    </div>
  );

  const chatbotTabContent = (
    <div className="form-section">
      <Checkbox
        label="Enable Chatbot Feature"
        id="chatbot_enabled"
        name="chatbot_enabled"
        checked={formData.chatbot_enabled || false}
        onChange={handleCheckboxChange}
        text="Allow interaction with this character via an AI-powered chat interface (future feature)."
      />
      {formData.chatbot_enabled && (
        <div className="chatbot-placeholder">
          <p>Chatbot configuration and interface will be available here in a future update.</p>
          <p>For now, enabling this flag will mark the character as chatbot-compatible.</p>
        </div>
      )}
    </div>
  );


  const tabItems: TabItem[] = [
    { name: 'Details', content: detailsTabContent },
    { name: 'Images', content: imagesTabContent },
    { name: 'Notes', content: notesTabContent },
    { name: 'Chatbot', content: chatbotTabContent },
  ];

  return (
    <div className="character-editor-page">
      <header className="editor-header">
        <h2>{isNewCharacter ? 'Create New Character' : `Edit ${character?.name || 'Character'}`}</h2>
        <div className="header-actions">
          {!isNewCharacter && characterId && (
             <Button onClick={handleExportCharacter} variant="outline-secondary" size="sm" disabled={isSaving}>
               Export Character
             </Button>
          )}
          <Button
            onClick={() => navigate(campaignId ? `/campaign/${campaignId}/characters` : '/')}
            variant="secondary"
            size="sm"
            disabled={isSaving}
          >
            Back to List
          </Button>
        </div>
      </header>

      {error && <p className="error-message page-error">{error}</p>}

      <form onSubmit={handleSubmit} className="editor-form">
        <Tabs tabs={tabItems} activeTabName={activeTab} onTabChange={setActiveTab} />

        <div className="form-actions">
          <Button type="submit" variant="primary" disabled={isSaving || isLoading}>
            {isSaving ? 'Saving...' : (isNewCharacter ? 'Create Character' : 'Save Changes')}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default CharacterEditorPage;
