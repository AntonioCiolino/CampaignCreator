import React, { useState, useEffect, useCallback } from 'react';
// Feature Imports
import { Feature, FeatureCreate, FeatureUpdate } from '../types/featureTypes';
import * as featureService from '../services/featureService';
import FeatureForm from '../components/datamanagement/FeatureForm';
// Rolltable Imports
import { RollTable, RollTableCreate, RollTableUpdate } from '../types/rollTableTypes';
import * as rollTableService from '../services/rollTableService';
import RollTableForm from '../components/datamanagement/RollTableForm';

import './DataManagementPage.css';

const DataManagementPage: React.FC = () => {
  // --- Feature States ---
  const [features, setFeatures] = useState<Feature[]>([]);
  const [isLoadingFeatures, setIsLoadingFeatures] = useState<boolean>(false);
  const [errorFeatures, setErrorFeatures] = useState<string | null>(null);
  const [showFeatureForm, setShowFeatureForm] = useState<boolean>(false);
  const [editingFeature, setEditingFeature] = useState<Feature | null>(null);

  // --- Rolltable States ---
  const [rollTables, setRollTables] = useState<RollTable[]>([]);
  const [isLoadingRollTables, setIsLoadingRollTables] = useState<boolean>(false);
  const [errorRollTables, setErrorRollTables] = useState<string | null>(null);
  const [showRollTableForm, setShowRollTableForm] = useState<boolean>(false);
  const [editingRollTable, setEditingRollTable] = useState<RollTable | null>(null);

  // --- Feature Logic ---
  const fetchFeatures = useCallback(async () => {
    setIsLoadingFeatures(true);
    setErrorFeatures(null);
    try {
      const data = await featureService.getFeatures();
      setFeatures(data);
    } catch (err) {
      console.error("Error fetching features:", err);
      setErrorFeatures(err instanceof Error ? err.message : 'Failed to fetch features.');
    } finally {
      setIsLoadingFeatures(false);
    }
  }, []);

  useEffect(() => {
    fetchFeatures();
  }, [fetchFeatures]);

  const handleCreateNewFeatureClick = () => {
    setEditingFeature(null);
    setShowFeatureForm(true);
  };

  const handleEditFeatureClick = (feature: Feature) => {
    setEditingFeature(feature);
    setShowFeatureForm(true);
  };

  const handleDeleteFeatureClick = async (featureId: number) => {
    if (window.confirm('Are you sure you want to delete this feature?')) {
      setIsLoadingFeatures(true);
      try {
        await featureService.deleteFeature(featureId);
        setFeatures(prevFeatures => prevFeatures.filter(f => f.id !== featureId));
      } catch (err) {
        console.error("Error deleting feature:", err);
        setErrorFeatures(err instanceof Error ? err.message : 'Failed to delete feature.');
      } finally {
        setIsLoadingFeatures(false);
      }
    }
  };

  const handleFeatureFormSubmit = async (data: FeatureCreate | FeatureUpdate) => {
    setIsLoadingFeatures(true);
    setErrorFeatures(null);
    try {
      if (editingFeature) {
        await featureService.updateFeature(editingFeature.id, data);
      } else {
        await featureService.createFeature(data as FeatureCreate);
      }
      await fetchFeatures();
      setShowFeatureForm(false);
      setEditingFeature(null);
    } catch (err) {
      console.error("Error submitting feature form:", err);
      const errMessage = err instanceof Error ? err.message : 'Failed to save feature.';
      if (typeof err === 'object' && err !== null && 'response' in err && typeof err.response === 'object' && err.response !== null && 'status' in err.response && err.response.status === 400) {
        setErrorFeatures(`Error: ${errMessage}. A feature with this name might already exist.`);
     } else {
        setErrorFeatures(errMessage);
     }
    } finally {
      setIsLoadingFeatures(false);
    }
  };

  const handleFeatureFormCancel = () => {
    setShowFeatureForm(false);
    setEditingFeature(null);
    setErrorFeatures(null);
  };

  // --- Rolltable Logic ---
  const fetchRollTables = useCallback(async () => {
    setIsLoadingRollTables(true);
    setErrorRollTables(null);
    try {
      const data = await rollTableService.getRollTables();
      setRollTables(data);
    } catch (err) {
      console.error("Error fetching rolltables:", err);
      setErrorRollTables(err instanceof Error ? err.message : 'Failed to fetch rolltables.');
    } finally {
      setIsLoadingRollTables(false);
    }
  }, []);

  useEffect(() => {
    fetchRollTables();
  }, [fetchRollTables]);

  const handleCreateNewRollTableClick = () => {
    setEditingRollTable(null);
    setShowRollTableForm(true);
  };

  const handleEditRollTableClick = (rollTable: RollTable) => {
    setEditingRollTable(rollTable);
    setShowRollTableForm(true);
  };

  const handleDeleteRollTableClick = async (rollTableId: number) => {
    if (window.confirm('Are you sure you want to delete this rolltable? This will also delete all its items.')) {
      setIsLoadingRollTables(true);
      try {
        await rollTableService.deleteRollTable(rollTableId);
        setRollTables(prevRollTables => prevRollTables.filter(rt => rt.id !== rollTableId));
      } catch (err) {
        console.error("Error deleting rolltable:", err);
        setErrorRollTables(err instanceof Error ? err.message : 'Failed to delete rolltable.');
      } finally {
        setIsLoadingRollTables(false);
      }
    }
  };

  const handleRollTableFormSubmit = async (data: RollTableCreate | RollTableUpdate) => {
    setIsLoadingRollTables(true);
    setErrorRollTables(null);
    try {
      if (editingRollTable) {
        await rollTableService.updateRollTable(editingRollTable.id, data);
      } else {
        await rollTableService.createRollTable(data as RollTableCreate);
      }
      await fetchRollTables();
      setShowRollTableForm(false);
      setEditingRollTable(null);
    } catch (err) {
      console.error("Error submitting rolltable form:", err);
      const errMessage = err instanceof Error ? err.message : 'Failed to save rolltable.';
      if (typeof err === 'object' && err !== null && 'response' in err && typeof err.response === 'object' && err.response !== null && 'status' in err.response && err.response.status === 400) {
        setErrorRollTables(`Error: ${errMessage}. A rolltable with this name might already exist or item data is invalid.`);
     } else {
        setErrorRollTables(errMessage);
     }
    } finally {
      setIsLoadingRollTables(false);
    }
  };

  const handleRollTableFormCancel = () => {
    setShowRollTableForm(false);
    setEditingRollTable(null);
    setErrorRollTables(null);
  };


  return (
    <div className="data-management-page">
      <h1>Data Management</h1>
      <p>Manage Features and Rolltables from this section.</p>

      {/* --- Features Section --- */}
      <div className="management-section feature-management-section">
        <h2>Features Management</h2>
        {errorFeatures && <p className="error-message">Error: {errorFeatures}</p>}
        
        {!showFeatureForm && (
          <button onClick={handleCreateNewFeatureClick} className="action-button create-new-button">
            Create New Feature
          </button>
        )}

        {isLoadingFeatures && <p className="loading-message">Loading features...</p>}

        {showFeatureForm && (
          <FeatureForm
            onSubmit={handleFeatureFormSubmit}
            onCancel={handleFeatureFormCancel}
            initialFeature={editingFeature || undefined}
          />
        )}

        {!showFeatureForm && !isLoadingFeatures && features.length === 0 && !errorFeatures && (
          <p>No features found. Create one to get started!</p>
        )}

        {!showFeatureForm && features.length > 0 && (
          <table className="data-table features-table">
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
                    <button onClick={() => handleEditFeatureClick(feature)} className="action-button edit-button">Edit</button>
                    <button onClick={() => handleDeleteFeatureClick(feature.id)} className="action-button delete-button">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* --- Rolltables Section --- */}
      <div className="management-section rolltable-management-section">
        <h2>Rolltables Management</h2>
        {errorRollTables && <p className="error-message">Error: {errorRollTables}</p>}

        {!showRollTableForm && (
          <button onClick={handleCreateNewRollTableClick} className="action-button create-new-button">
            Create New Rolltable
          </button>
        )}

        {isLoadingRollTables && <p className="loading-message">Loading rolltables...</p>}
        
        {showRollTableForm && (
          <RollTableForm
            onSubmit={handleRollTableFormSubmit}
            onCancel={handleRollTableFormCancel}
            initialRollTable={editingRollTable || undefined}
          />
        )}

        {!showRollTableForm && !isLoadingRollTables && rollTables.length === 0 && !errorRollTables && (
          <p>No rolltables found. Create one to get started!</p>
        )}

        {!showRollTableForm && rollTables.length > 0 && (
          <table className="data-table rolltables-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Item Count</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rollTables.map((rollTable) => (
                <tr key={rollTable.id}>
                  <td>{rollTable.name}</td>
                  <td>{rollTable.description || '-'}</td>
                  <td>{rollTable.items.length}</td>
                  <td className="actions-cell">
                    <button onClick={() => handleEditRollTableClick(rollTable)} className="action-button edit-button">Edit</button>
                    <button onClick={() => handleDeleteRollTableClick(rollTable.id)} className="action-button delete-button">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default DataManagementPage;
