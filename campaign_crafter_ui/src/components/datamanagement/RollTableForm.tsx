// src/components/datamanagement/RollTableForm.tsx
import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid'; // For unique keys for new items
import { RollTable, RollTableCreate, RollTableUpdate, RollTableItemCreate } from '../../types/rollTableTypes';
import RollTableItemFormRow from './RollTableItemFormRow';
import './RollTableForm.css';

// Local type for items in the form, includes a temporary client-side ID for list keys
type FormRollTableItem = Partial<RollTableItemCreate> & { tempId: string };

interface RollTableFormProps {
  initialRollTable?: RollTable;
  onSubmit: (data: RollTableCreate | RollTableUpdate) => void;
  onCancel: () => void;
}

const RollTableForm: React.FC<RollTableFormProps> = ({ initialRollTable, onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [items, setItems] = useState<FormRollTableItem[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (initialRollTable) {
      setName(initialRollTable.name);
      setDescription(initialRollTable.description || '');
      setItems(initialRollTable.items.map(item => ({ ...item, tempId: uuidv4() })));
    } else {
      setName('');
      setDescription('');
      setItems([{ tempId: uuidv4(), min_roll: 1, max_roll: 1, description: '' }]); // Start with one item
    }
  }, [initialRollTable]);

  const handleItemChange = (index: number, updatedSubItem: RollTableItemCreate) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], ...updatedSubItem };
    setItems(newItems);
  };

  const handleAddItem = () => {
    setItems([...items, { tempId: uuidv4(), min_roll: undefined, max_roll: undefined, description: '' }]);
  };

  const handleRemoveItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
  };

  const validateForm = (): boolean => {
    if (!name.trim()) {
      setFormError("Table Name cannot be empty.");
      return false;
    }
    if (items.length === 0) {
      setFormError("Rolltable must have at least one item.");
      return false;
    }
    for (const item of items) {
      if (item.min_roll == null || item.max_roll == null || !item.description?.trim()) {
        setFormError("All item fields (Min Roll, Max Roll, Description) must be filled.");
        return false;
      }
      if (item.min_roll > item.max_roll) {
        setFormError(`Invalid range for item "${item.description}": Min Roll cannot be greater than Max Roll.`);
        return false;
      }
    }
    setFormError(null);
    return true;
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!validateForm()) {
      return;
    }

    const itemsToSubmit: RollTableItemCreate[] = items.map(item => ({
      min_roll: item.min_roll!, // Validation ensures these are present
      max_roll: item.max_roll!,
      description: item.description!,
    }));

    const rollTableData = {
      name,
      description: description.trim() || null, // Send null if empty
      items: itemsToSubmit,
    };
    
    onSubmit(rollTableData);
  };

  return (
    <form onSubmit={handleSubmit} className="roll-table-form">
      <div className="form-field">
        <label htmlFor="rolltable-name">Table Name:</label>
        <input
          id="rolltable-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      <div className="form-field">
        <label htmlFor="rolltable-description">Description (e.g., d100, d20):</label>
        <input
          id="rolltable-description"
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g., d100 or brief explanation"
        />
      </div>

      <div className="items-section">
        <h3>Items</h3>
        {items.map((item, index) => (
          <RollTableItemFormRow
            key={item.tempId} // Use tempId for stable key during edits
            index={index}
            item={item}
            onChange={(updatedSubItem) => handleItemChange(index, updatedSubItem)}
            onRemove={() => handleRemoveItem(index)}
          />
        ))}
        <button type="button" onClick={handleAddItem} className="add-item-button">
          Add Item
        </button>
      </div>
      
      {formError && <p className="validation-error">{formError}</p>}

      <div className="form-actions">
        <button type="submit" className="save-button">Save Rolltable</button>
        <button type="button" onClick={onCancel} className="cancel-button">Cancel</button>
      </div>
    </form>
  );
};

export default RollTableForm;
