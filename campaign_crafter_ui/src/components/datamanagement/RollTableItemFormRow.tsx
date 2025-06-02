// src/components/datamanagement/RollTableItemFormRow.tsx
import React from 'react';
import { RollTableItemCreate } from '../../types/rollTableTypes'; // Assuming RollTableItemCreate is suitable for form item data
import './RollTableItemFormRow.css';

interface RollTableItemFormRowProps {
  item: Partial<RollTableItemCreate>; // Use Partial for potentially incomplete new items
  onChange: (updatedItem: RollTableItemCreate) => void;
  onRemove: () => void;
  index: number; // For unique keys and labels if needed, though not strictly used in this basic version's labels
}

const RollTableItemFormRow: React.FC<RollTableItemFormRowProps> = ({ item, onChange, onRemove, index }) => {
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    const updatedItem = {
      ...item,
      [name]: name === 'min_roll' || name === 'max_roll' ? parseInt(value, 10) || 0 : value,
    } as RollTableItemCreate; // Cast to full type, assuming validation happens elsewhere or on submit
    onChange(updatedItem);
  };

  return (
    <div className="roll-table-item-form-row">
      <div className="item-input-group">
        <label htmlFor={`min-roll-${index}`}>Min Roll</label>
        <input
          id={`min-roll-${index}`}
          name="min_roll"
          type="number"
          value={item.min_roll ?? ''}
          onChange={handleInputChange}
          placeholder="Min"
        />
      </div>
      <div className="item-input-group">
        <label htmlFor={`max-roll-${index}`}>Max Roll</label>
        <input
          id={`max-roll-${index}`}
          name="max_roll"
          type="number"
          value={item.max_roll ?? ''}
          onChange={handleInputChange}
          placeholder="Max"
        />
      </div>
      <div className="item-input-group item-description-input">
        <label htmlFor={`description-${index}`}>Description</label>
        <input
          id={`description-${index}`}
          name="description"
          type="text"
          value={item.description ?? ''}
          onChange={handleInputChange}
          placeholder="Item Description"
        />
      </div>
      <button type="button" onClick={onRemove} className="remove-item-button">
        Remove
      </button>
    </div>
  );
};

export default RollTableItemFormRow;
