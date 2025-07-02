// src/components/datamanagement/FeatureForm.tsx
import React, { useState, useEffect } from 'react';
import { Feature, FeatureCreate, FeatureUpdate } from '../../types/featureTypes';
import './FeatureForm.css';

interface FeatureFormProps {
  initialFeature?: Feature;
  onSubmit: (data: FeatureCreate | FeatureUpdate) => void;
  onCancel: () => void;
}

const SECTION_TYPES = ['NPC', 'Character', 'Location', 'Item', 'Quest', 'Monster', 'Chapter', 'Note', 'World Detail', 'Generic'];
const FEATURE_CATEGORIES = ['FullSection', 'Snippet', 'System']; // Define categories

const FeatureForm: React.FC<FeatureFormProps> = ({ initialFeature, onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [template, setTemplate] = useState('');
  const [featureCategory, setFeatureCategory] = useState<string>(FEATURE_CATEGORIES[0]);
  const [requiredContext, setRequiredContext] = useState<string>(''); // Comma-separated string
  const [compatibleTypes, setCompatibleTypes] = useState<string[]>([]); // Array of selected type strings

  useEffect(() => {
    if (initialFeature) {
      setName(initialFeature.name);
      setTemplate(initialFeature.template);
      setFeatureCategory(initialFeature.feature_category || FEATURE_CATEGORIES[0]);
      setRequiredContext(initialFeature.required_context?.join(', ') || '');
      setCompatibleTypes(initialFeature.compatible_types || []);
    } else {
      // Reset form for create new
      setName('');
      setTemplate('');
      setFeatureCategory(FEATURE_CATEGORIES[0]);
      setRequiredContext('');
      setCompatibleTypes([]);
    }
  }, [initialFeature]);

  const handleCompatibleTypesChange = (type: string) => {
    setCompatibleTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    );
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !template.trim()) {
      alert('Name and Template cannot be empty.'); // Basic validation
      return;
    }
    const dataToSubmit: FeatureCreate | FeatureUpdate = {
      name,
      template,
      feature_category: featureCategory,
      required_context: requiredContext.split(',').map(s => s.trim()).filter(s => s),
      compatible_types: compatibleTypes,
    };
    onSubmit(dataToSubmit);
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
        <label htmlFor="feature-category">Category:</label>
        <select
          id="feature-category"
          value={featureCategory}
          onChange={(e) => setFeatureCategory(e.target.value)}
        >
          {FEATURE_CATEGORIES.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="feature-required-context">Required Context (comma-separated):</label>
        <input
          id="feature-required-context"
          type="text"
          value={requiredContext}
          onChange={(e) => setRequiredContext(e.target.value)}
          placeholder="e.g., selected_text, campaign_concept"
        />
      </div>
      <div className="compatible-types-group">
        <label>Compatible Section Types:</label>
        <div className="checkbox-group">
          {SECTION_TYPES.map(type => (
            <label key={type} htmlFor={`type-${type}`} className="checkbox-label">
              <input
                type="checkbox"
                id={`type-${type}`}
                value={type}
                checked={compatibleTypes.includes(type)}
                onChange={() => handleCompatibleTypesChange(type)}
              />
              {type}
            </label>
          ))}
        </div>
      </div>
      <div>
        <label htmlFor="feature-template">Template:</label>
        <textarea
          id="feature-template"
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
          required
          rows={10}
        />
        <div className="template-guidance">
          <p><strong>Available Template Variables (examples):</strong></p>
          <ul>
            <li><code>{'{campaign_title}'}</code> - Title of the campaign.</li>
            <li><code>{'{campaign_concept}'}</code> - Concept of the campaign.</li>
            <li><code>{'{section_title}'}</code> - Title of the current section.</li>
            <li><code>{'{section_type}'}</code> - Type of the current section.</li>
            <li><code>{'{selected_text}'}</code> - (For Snippet features) The user's highlighted text.</li>
            <li><code>{'{user_instructions}'}</code> - (For FullSection features) Content of the editor if provided as instruction.</li>
            <li><code>{'{campaign_characters}'}</code> - Summary of campaign characters.</li>
            <li><code>{'{existing_sections_summary}'}</code> - Summary of other sections.</li>
            <li><em>(Add any custom keys you define in "Required Context" above, e.g., <code>{'{npc_name}'}</code>)</em></li>
          </ul>
        </div>
      </div>
      <div className="form-actions">
        <button type="submit" className="save-button">Save Feature</button>
        <button type="button" onClick={onCancel} className="cancel-button">Cancel</button>
      </div>
    </form>
  );
};

export default FeatureForm;
