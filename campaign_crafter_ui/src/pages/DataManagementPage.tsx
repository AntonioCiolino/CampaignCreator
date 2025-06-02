import React, { useState, useEffect, useCallback } from 'react';
import { Feature, FeatureCreate, FeatureUpdate } from '../types/featureTypes';
import * as featureService from '../services/featureService';
import FeatureForm from '../components/datamanagement/FeatureForm';
import './DataManagementPage.css'; // Ensure this path is correct

const DataManagementPage: React.FC = () => {
  const [features, setFeatures] = useState<Feature[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showFeatureForm, setShowFeatureForm] = useState<boolean>(false);
  const [editingFeature, setEditingFeature] = useState<Feature | null>(null);

  const fetchFeatures = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await featureService.getFeatures();
      setFeatures(data);
    } catch (err) {
      console.error("Error fetching features:", err);
      setError(err instanceof Error ? err.message : 'Failed to fetch features. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFeatures();
  }, [fetchFeatures]);

  const handleCreateNewClick = () => {
    setEditingFeature(null);
    setShowFeatureForm(true);
  };

  const handleEditClick = (feature: Feature) => {
    setEditingFeature(feature);
    setShowFeatureForm(true);
  };

  const handleDeleteClick = async (featureId: number) => {
    if (window.confirm('Are you sure you want to delete this feature?')) {
      setIsLoading(true);
      try {
        await featureService.deleteFeature(featureId);
        // Refresh features list
        setFeatures(prevFeatures => prevFeatures.filter(f => f.id !== featureId)); 
        // Or call fetchFeatures(); but filtering is more optimistic
      } catch (err) {
        console.error("Error deleting feature:", err);
        setError(err instanceof Error ? err.message : 'Failed to delete feature.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleFormSubmit = async (data: FeatureCreate | FeatureUpdate) => {
    setIsLoading(true);
    setError(null);
    try {
      if (editingFeature) {
        await featureService.updateFeature(editingFeature.id, data);
      } else {
        await featureService.createFeature(data as FeatureCreate);
      }
      await fetchFeatures(); // Re-fetch all features to get the latest list
      setShowFeatureForm(false);
      setEditingFeature(null);
    } catch (err) {
      console.error("Error submitting feature form:", err);
      const errMessage = err instanceof Error ? err.message : 'Failed to save feature.';
      // Check for duplicate name error from backend (assuming 400 for this)
      // This is a basic check, specific error codes/messages from API are better
      if (typeof err === 'object' && err !== null && 'response' in err && typeof err.response === 'object' && err.response !== null && 'status' in err.response && err.response.status === 400) {
         setError(`Error: ${errMessage}. A feature with this name might already exist.`);
      } else {
         setError(errMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormCancel = () => {
    setShowFeatureForm(false);
    setEditingFeature(null);
    setError(null); // Clear any form-specific errors
  };

  return (
    <div className="data-management-page">
      <h1>Data Management</h1>
      <p>Manage Features and Rolltables from this section.</p>

      <div className="feature-management-section">
        <h2>Features Management</h2>
        {error && <p className="error-message">Error: {error}</p>}
        
        {!showFeatureForm && (
          <button onClick={handleCreateNewClick} className="action-button create-new-button">
            Create New Feature
          </button>
        )}

        {isLoading && <p>Loading features...</p>}

        {showFeatureForm && (
          <FeatureForm
            onSubmit={handleFormSubmit}
            onCancel={handleFormCancel}
            initialFeature={editingFeature || undefined}
          />
        )}

        {!showFeatureForm && !isLoading && features.length === 0 && !error && (
          <p>No features found. Create one to get started!</p>
        )}

        {!showFeatureForm && features.length > 0 && (
          <table className="features-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Template (excerpt)</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature) => (
                <tr key={feature.id}>
                  <td>{feature.name}</td>
                  <td>{feature.template.substring(0, 100)}{feature.template.length > 100 ? '...' : ''}</td>
                  <td className="actions-cell">
                    <button onClick={() => handleEditClick(feature)} className="action-button edit-button">Edit</button>
                    <button onClick={() => handleDeleteClick(feature.id)} className="action-button delete-button">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {/* Placeholder for Rolltable Management UI */}
    </div>
  );
};

export default DataManagementPage;
