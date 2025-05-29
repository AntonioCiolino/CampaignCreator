import React, { useState, ChangeEvent } from 'react';
import FileInput from '../components/common/FileInput';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import { importJsonFile, importZipFile, ImportSummaryResponse, ImportErrorDetail } from '../services/importService';
import './ImportDataPage.css';

type ActiveTab = 'json' | 'zip';

const ImportDataPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('json');
  
  const [selectedJsonFile, setSelectedJsonFile] = useState<File | null>(null);
  const [targetCampaignIdJson, setTargetCampaignIdJson] = useState<string>('');

  const [selectedZipFile, setSelectedZipFile] = useState<File | null>(null);
  const [targetCampaignIdZip, setTargetCampaignIdZip] = useState<string>('');
  const [processFolders, setProcessFolders] = useState<boolean>(false);

  const [importSummary, setImportSummary] = useState<ImportSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleJsonFileSelect = (file: File | null) => {
    setSelectedJsonFile(file);
    setImportSummary(null); // Clear previous summary
    setError(null);
  };

  const handleZipFileSelect = (file: File | null) => {
    setSelectedZipFile(file);
    setImportSummary(null); // Clear previous summary
    setError(null);
  };

  const handleJsonImport = async () => {
    if (!selectedJsonFile) {
      setError("Please select a JSON file to import.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setImportSummary(null);
    try {
      const summary = await importJsonFile(selectedJsonFile, targetCampaignIdJson || undefined);
      setImportSummary(summary);
      if(summary.errors && summary.errors.length > 0) setError("Import completed with errors. See summary for details.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred during JSON import.");
      setImportSummary(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleZipImport = async () => {
    if (!selectedZipFile) {
      setError("Please select a Zip file to import.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setImportSummary(null);
    try {
      const summary = await importZipFile(selectedZipFile, targetCampaignIdZip || undefined, processFolders);
      setImportSummary(summary);
      if(summary.errors && summary.errors.length > 0) setError("Import completed with errors. See summary for details.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred during Zip import.");
      setImportSummary(null);
    } finally {
      setIsLoading(false);
    }
  };

  const renderImportSummary = () => {
    if (!importSummary) return null;
    return (
      <Card className="import-summary-card" headerContent={<h4 className="import-summary-title">Import Summary</h4>}>
        <p>{importSummary.message}</p>
        {importSummary.imported_campaigns_count > 0 && (
          <p>New Campaigns Created: {importSummary.imported_campaigns_count} (IDs: {importSummary.created_campaign_ids.join(', ')})</p>
        )}
        {importSummary.imported_sections_count > 0 && (
          <p>Sections Imported/Added: {importSummary.imported_sections_count}</p>
        )}
        {importSummary.updated_campaign_ids.length > 0 && (
            <p>Campaigns Updated: (IDs: {importSummary.updated_campaign_ids.join(', ')})</p>
        )}

        {importSummary.errors && importSummary.errors.length > 0 && (
          <>
            <h5 className="import-summary-errors-title">Errors Encountered:</h5>
            <ul className="import-summary-error-list">
              {importSummary.errors.map((err, index) => (
                <li key={index}>
                  {err.file_name && <strong>File:</strong>} {err.file_name}
                  {err.item_identifier && <> ({err.item_identifier})</>}
                  <br />
                  <strong>Error:</strong> {err.error}
                </li>
              ))}
            </ul>
          </>
        )}
      </Card>
    );
  };

  return (
    <div className="import-page-wrapper container">
      <h2 className="import-page-title">Import Campaign Data</h2>

      <div className="import-tabs">
        <button 
          className={`import-tab-button ${activeTab === 'json' ? 'active' : ''}`}
          onClick={() => setActiveTab('json')}
        >
          Import JSON File
        </button>
        <button 
          className={`import-tab-button ${activeTab === 'zip' ? 'active' : ''}`}
          onClick={() => setActiveTab('zip')}
        >
          Import Zip Archive
        </button>
      </div>

      {activeTab === 'json' && (
        <section className="import-section">
          <h3>JSON Import Options</h3>
          <FileInput
            id="jsonFile"
            label="Select JSON File (.json):"
            accept=".json"
            onFileSelected={handleJsonFileSelect}
            buttonText="Choose JSON File"
          />
          <Input
            id="targetCampaignIdJson"
            label="Target Campaign ID (Optional):"
            placeholder="Enter ID of existing campaign to add sections to"
            value={targetCampaignIdJson}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setTargetCampaignIdJson(e.target.value)}
            wrapperClassName="import-form-group"
          />
          <div className="import-actions">
            <Button onClick={handleJsonImport} disabled={isLoading || !selectedJsonFile} variant="primary">
              {isLoading ? 'Importing...' : 'Start JSON Import'}
            </Button>
          </div>
        </section>
      )}

      {activeTab === 'zip' && (
        <section className="import-section">
          <h3>Zip Archive Import Options</h3>
          <FileInput
            id="zipFile"
            label="Select Zip File (.zip):"
            accept=".zip,.tar.gz,.tgz" // Accept common archive formats
            onFileSelected={handleZipFileSelect}
            buttonText="Choose Zip File"
          />
          <Input
            id="targetCampaignIdZip"
            label="Target Campaign ID (Optional):"
            placeholder="Enter ID of existing campaign to add content to"
            value={targetCampaignIdZip}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setTargetCampaignIdZip(e.target.value)}
            wrapperClassName="import-form-group"
          />
          <div className="import-form-group">
            <input
              type="checkbox"
              id="processFolders"
              checked={processFolders}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setProcessFolders(e.target.checked)}
              className="import-checkbox"
            />
            <label htmlFor="processFolders">
              Process Folders as Structure (e.g., top-level folders as new campaigns if no Target ID)
            </label>
          </div>
          <div className="import-actions">
            <Button onClick={handleZipImport} disabled={isLoading || !selectedZipFile} variant="primary">
              {isLoading ? 'Importing...' : 'Start Zip Import'}
            </Button>
          </div>
        </section>
      )}

      {error && <p className="general-import-error error-message">{error}</p>}
      {renderImportSummary()}
    </div>
  );
};

export default ImportDataPage;

// To make this view accessible, you would typically add a route in your main App router,
// for example, in src/routes/AppRoutes.tsx:
//
// import ImportDataPage from '../views/ImportDataPage';
//
// <Route path="/tools/import-data" element={<ImportDataPage />} />
//
// And provide a NavLink or button to navigate to "/tools/import-data".
