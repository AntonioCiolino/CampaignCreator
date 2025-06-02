// src/components/datamanagement/FeatureForm.tsx
import React, { useState, useEffect } from 'react';
import { Feature, FeatureCreate, FeatureUpdate } from '../../types/featureTypes';
import './FeatureForm.css';

interface FeatureFormProps {
  initialFeature?: Feature;
  onSubmit: (data: FeatureCreate | FeatureUpdate) => void;
  onCancel: () => void;
}

const FeatureForm: React.FC<FeatureFormProps> = ({ initialFeature, onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [template, setTemplate] = useState('');

  useEffect(() => {
    if (initialFeature) {
      setName(initialFeature.name);
      setTemplate(initialFeature.template);
    } else {
      // Reset form if no initialFeature (e.g., for create new)
      setName('');
      setTemplate('');
    }
  }, [initialFeature]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !template.trim()) {
      alert('Name and Template cannot be empty.'); // Basic validation
      return;
    }
    onSubmit({ name, template });
  };

  return (
    <form onSubmit={handleSubmit} className="feature-form">
      <div>
        <label htmlFor="feature-name">Name:</label>
        <input
          id="feature-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="feature-template">Template:</label>
        <textarea
          id="feature-template"
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
          required
        />
      </div>
      <div className="form-actions">
        <button type="submit" className="save-button">Save Feature</button>
        <button type="button" onClick={onCancel} className="cancel-button">Cancel</button>
      </div>
    </form>
  );
};

export default FeatureForm;
