import React, { useState, ChangeEvent, FormEvent } from 'react';
import { PydanticCharacter } from '../types/characterTypes';
import './CharacterStatsEditor.css'; // CSS for styling

interface CharacterStatsEditorProps {
  stats: Record<string, string>;
  onStatsChange: (newStats: Record<string, string>) => void;
}

const CharacterStatsEditor: React.FC<CharacterStatsEditorProps> = ({ stats, onStatsChange }) => {
  const [newStatKey, setNewStatKey] = useState<string>('');
  const [newStatValue, setNewStatValue] = useState<string>('');
  const [editKey, setEditKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  const handleAddStat = (e: FormEvent) => {
    e.preventDefault();
    if (newStatKey.trim() && !stats.hasOwnProperty(newStatKey.trim())) {
      onStatsChange({ ...stats, [newStatKey.trim()]: newStatValue.trim() });
      setNewStatKey('');
      setNewStatValue('');
    } else if (stats.hasOwnProperty(newStatKey.trim())) {
      alert(`Stat key "${newStatKey.trim()}" already exists. Please use a unique key or edit the existing one.`);
    }
  };

  const handleRemoveStat = (keyToRemove: string) => {
    const { [keyToRemove]: _, ...remainingStats } = stats;
    onStatsChange(remainingStats);
    if (editKey === keyToRemove) {
      setEditKey(null); // Stop editing if the removed key was being edited
    }
  };

  const handleEditStat = (key: string, value: string) => {
    setEditKey(key);
    setEditValue(value);
  };

  const handleSaveEdit = (originalKey: string) => {
    if (editKey && editKey.trim()) { // Ensure new key is not empty
      const updatedStats = { ...stats };
      // If the key itself was changed, delete the old one and add the new one
      if (originalKey !== editKey.trim() && stats.hasOwnProperty(editKey.trim())) {
         alert(`Cannot rename stat to "${editKey.trim()}" as it already exists. Choose a different name.`);
         return;
      }
      if (originalKey !== editKey.trim()) {
        delete updatedStats[originalKey];
      }
      updatedStats[editKey.trim()] = editValue.trim();
      onStatsChange(updatedStats);
      setEditKey(null);
      setEditValue('');
    }
  };

  const handleCancelEdit = () => {
    setEditKey(null);
    setEditValue('');
  };

  return (
    <div className="character-stats-editor">
      <h4>Character Statistics</h4>
      {Object.keys(stats).length === 0 && <p className="no-stats-message">No statistics defined yet.</p>}

      <ul className="stats-list">
        {Object.entries(stats).map(([key, value]) => (
          <li key={key} className="stat-item">
            {editKey === key ? (
              <div className="stat-edit-form">
                <input
                  type="text"
                  value={editKey} // Allow editing the key itself
                  onChange={(e) => setEditKey(e.target.value)}
                  placeholder="Stat Name (e.g., Strength)"
                  className="stat-input key-input"
                />
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  placeholder="Value (e.g., 18)"
                  className="stat-input value-input"
                />
                <div className="stat-edit-actions">
                  <button onClick={() => handleSaveEdit(key)} className="stat-button save">Save</button>
                  <button onClick={handleCancelEdit} className="stat-button cancel">Cancel</button>
                </div>
              </div>
            ) : (
              <div className="stat-display">
                <span className="stat-key">{key}:</span>
                <span className="stat-value">{value}</span>
                <div className="stat-item-actions">
                  <button onClick={() => handleEditStat(key, value)} className="stat-button edit">Edit</button>
                  <button onClick={() => handleRemoveStat(key)} className="stat-button remove">Remove</button>
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>

      <form onSubmit={handleAddStat} className="add-stat-form">
        <div className="form-row">
          <input
            type="text"
            value={newStatKey}
            onChange={(e) => setNewStatKey(e.target.value)}
            placeholder="New Stat Name (e.g., Dexterity)"
            className="stat-input key-input"
          />
          <input
            type="text"
            value={newStatValue}
            onChange={(e) => setNewStatValue(e.target.value)}
            placeholder="Value (e.g., 16)"
            className="stat-input value-input"
          />
        </div>
        <button type="submit" className="stat-button add" disabled={!newStatKey.trim()}>
          Add Stat
        </button>
      </form>
    </div>
  );
};

export default CharacterStatsEditor;
