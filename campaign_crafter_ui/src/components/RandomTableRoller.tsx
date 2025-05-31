import React, { useState, useEffect, useCallback } from 'react';
import { getAllRandomTableNames, getRandomItemFromTable, RandomItemResponse } from '../services/randomTableService';
import Button from './common/Button'; // Assuming Button component exists and is styled
import './RandomTableRoller.css'; // For styling

interface RandomTableRollerProps {
  onInsertItem: (itemText: string) => void;
  // Optional: Pass a campaign or section ID if needed to disable if no campaign/section is active
  // disabled?: boolean;
}

const RandomTableRoller: React.FC<RandomTableRollerProps> = ({ onInsertItem }) => {
  const [randomTableNames, setRandomTableNames] = useState<string[]>([]);
  const [selectedRandomTable, setSelectedRandomTable] = useState<string>('');
  const [fetchedRandomItem, setFetchedRandomItem] = useState<RandomItemResponse | null>(null);
  const [isLoadingTables, setIsLoadingTables] = useState<boolean>(false);
  const [isLoadingItem, setIsLoadingItem] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTableNames = async () => {
      setIsLoadingTables(true);
      setError(null);
      try {
        const names = await getAllRandomTableNames();
        setRandomTableNames(names);
        if (names.length > 0) {
          // setSelectedRandomTable(names[0]); // Optionally pre-select first table
        }
      } catch (err) {
        console.error("Failed to load random table names:", err);
        setError(err instanceof Error ? err.message : "Failed to load random tables.");
      } finally {
        setIsLoadingTables(false);
      }
    };
    loadTableNames();
  }, []);

  const handleRollOnTable = async () => {
    if (!selectedRandomTable) {
      setError("Please select a table first.");
      return;
    }
    setIsLoadingItem(true);
    setError(null);
    setFetchedRandomItem(null);
    try {
      const itemResponse = await getRandomItemFromTable(selectedRandomTable);
      setFetchedRandomItem(itemResponse);
    } catch (err) {
      console.error(`Failed to get item from ${selectedRandomTable}:`, err);
      // The service already formats the error message including 404s
      setError(err instanceof Error ? err.message : `Failed to get item from table.`);
    } finally {
      setIsLoadingItem(false);
    }
  };

  const handleInsertClick = () => {
    if (fetchedRandomItem && fetchedRandomItem.item) {
      onInsertItem(fetchedRandomItem.item);
    } else {
      // This case should ideally not be reachable if button is disabled correctly
      setError("No item to insert. Please roll on a table first.");
    }
  };

  return (
    <div className="rtr-wrapper">
      <h4 className="rtr-title">Random Table Roller</h4>
      {isLoadingTables && <p>Loading tables...</p>}
      {error && <p className="rtr-error-message">{error}</p>}

      {!isLoadingTables && randomTableNames.length === 0 && !error && (
        <p>No random tables available.</p>
      )}

      {!isLoadingTables && randomTableNames.length > 0 && (
        <div className="rtr-controls">
          <select
            value={selectedRandomTable}
            onChange={e => {
              setSelectedRandomTable(e.target.value);
              setFetchedRandomItem(null); // Clear previous item when table changes
              setError(null); // Clear previous errors
            }}
            className="rtr-select"
            aria-label="Select random table"
          >
            <option value="">-- Select a Table --</option>
            {randomTableNames.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <Button
            onClick={handleRollOnTable}
            disabled={!selectedRandomTable || isLoadingItem}
            variant="secondary"
            className="rtr-button-roll"
          >
            {isLoadingItem ? 'Rolling...' : 'Roll on Table'}
          </Button>
        </div>
      )}

      {fetchedRandomItem && fetchedRandomItem.item && (
        <div className="rtr-result">
          <p className="rtr-result-text">
            <strong>Result:</strong> {fetchedRandomItem.item}
            <em> (from: {fetchedRandomItem.table_name})</em>
          </p>
          <Button
            onClick={handleInsertClick}
            variant="primary"
            className="rtr-button-insert"
          >
            Insert Item
          </Button>
        </div>
      )}
    </div>
  );
};

export default RandomTableRoller;
