import React, { useState, useEffect } from 'react';
import { getAllRandomTableNames, getRandomItemFromTable, RandomItemResponse, copySystemTables } from '../services/randomTableService';
import Button from './common/Button';
import './RandomTableRoller.css';
import { useAuth } from '../contexts/AuthContext'; // Assuming a useAuth hook for token

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
  const [isCopying, setIsCopying] = useState<boolean>(false);
  const [copyMessage, setCopyMessage] = useState<string | null>(null);
  const { token } = useAuth(); // Get token from AuthContext

  // Encapsulate loadTableNames to be callable
  const loadTableNames = async () => {
    setIsLoadingTables(true);
    setError(null); // Clear main error
    try {
      const names = await getAllRandomTableNames(); // This will now fetch user-specific + system if token is available via apiService
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

  useEffect(() => {
    loadTableNames();
  }, [token]); // Rerun if token changes, e.g. user logs in.

  const handleCopySystemTables = async () => {
    if (!token) {
      setCopyMessage("You must be logged in to copy tables.");
      return;
    }
    setIsCopying(true);
    setCopyMessage(null);
    setError(null); // Clear main error as this is a separate operation
    try {
      const copied = await copySystemTables(token);
      setCopyMessage(copied.length > 0 ? `Successfully copied ${copied.length} system table(s) to your account.` : "System tables already up-to-date in your account.");
      await loadTableNames(); // Refresh the table list
    } catch (err) {
      console.error("Failed to copy system tables:", err);
      setCopyMessage(err instanceof Error ? err.message : "Failed to copy system tables.");
    } finally {
      setIsCopying(false);
    }
  };

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
      {error && <p className="rtr-error-message">{error}</p>}
      {copyMessage && <p className={copyMessage.includes("Failed") || copyMessage.includes("must be logged in") ? "rtr-error-message" : "rtr-success-message"}>{copyMessage}</p>}

      <div className="rtr-system-table-actions">
        <Button
          onClick={handleCopySystemTables}
          disabled={isCopying || isLoadingTables}
          variant="outline-secondary"
          className="rtr-button-copy-system"
        >
          {isCopying ? 'Copying...' : 'Copy System Tables to My Account'}
        </Button>
      </div>

      {isLoadingTables && <p>Loading tables...</p>}

      {!isLoadingTables && randomTableNames.length === 0 && !error && (
        <p>No random tables available. Try copying system tables.</p>
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
