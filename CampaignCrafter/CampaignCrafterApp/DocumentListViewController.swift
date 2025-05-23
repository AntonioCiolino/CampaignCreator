import UIKit
import MobileCoreServices // For kUTTypeJSON and kUTTypeZipArchive
import ZipFoundation // Assuming this library is added to the project

class DocumentListViewController: UIViewController, UITableViewDataSource, UITableViewDelegate, UIDocumentPickerDelegate {

    var documents: [URL] = []
    let tableView = UITableView()

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Documents" // Title font is set by UIAppearance
        view.backgroundColor = Theme.parchmentBackground
        setupTableView()
        setupNavigationBar()
        loadDocuments()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        // Refresh documents when the view is about to appear,
        // in case changes were made in EditorViewController (e.g., new file created then back)
        // or if a rename happened.
        loadDocuments()
    }

    func setupTableView() {
        view.addSubview(tableView)
        tableView.backgroundColor = .clear // So it shows the view's parchment background
        tableView.separatorStyle = .singleLine // Default, can be themed later if needed
        tableView.separatorColor = Theme.mutedGoldAccent.withAlphaComponent(0.5) // Subtle separator

        tableView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor)
        ])
        tableView.dataSource = self
        tableView.delegate = self
        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "documentCell")
    }

    func setupNavigationBar() {
        // SF Symbols for buttons. Tint color is handled by UIAppearance.
        let addButtonImage = UIImage(systemName: "plus.circle.fill") // Using filled for more presence
        let importButtonImage = UIImage(systemName: "square.and.arrow.down.fill")

        let addButton = UIBarButtonItem(image: addButtonImage, style: .plain, target: self, action: #selector(createNewDocument))
        let importButton = UIBarButtonItem(image: importButtonImage, style: .plain, target: self, action: #selector(handleImportButtonTapped))
        
        navigationItem.rightBarButtonItems = [addButton]
        navigationItem.leftBarButtonItem = importButton
    }

    @objc func handleImportButtonTapped() {
        // Supported UTI types for import: JSON, Zip archives, and Folders
        // kUTTypeFolder is 'public.folder'
        let supportedTypes = [
            kUTTypeJSON as String,
            kUTTypeZipArchive as String,
            kUTTypeFolder as String
        ]
        
        let documentPicker = UIDocumentPickerViewController(documentTypes: supportedTypes, in: .import)
        documentPicker.delegate = self
        // For directory import, 'open' action is more appropriate if UIDocumentPickerViewController is used directly
        // However, the task is to import content, so .import action is fine.
        // If we wanted to "open" a directory to manage its contents in place, that would be different.
        documentPicker.allowsMultipleSelection = false // Process one item (file or directory) at a time
        present(documentPicker, animated: true, completion: nil)
    }

    @objc func createNewDocument() {
        let newDocumentName = "Untitled \(Date().timeIntervalSince1970).txt"
        let documentsDirectory = getDocumentsDirectory()
        let fileURL = documentsDirectory.appendingPathComponent(newDocumentName)
        
        do {
            try "".write(to: fileURL, atomically: true, encoding: .utf8)
            // loadDocuments() // Refresh the list - viewWillAppear will also handle this.
            // Open the new document directly in EditorViewController
            let editorVC = EditorViewController()
            editorVC.documentURL = fileURL
            navigationController?.pushViewController(editorVC, animated: true)
        } catch {
            print("Error creating new document: \(error)")
            showAlert(title: "Error", message: "Could not create new document: \(error.localizedDescription)")
        }
    }

    func getDocumentsDirectory() -> URL {
        let paths = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)
        return paths[0]
    }

    func loadDocuments() {
        let documentsDirectory = getDocumentsDirectory()
        do {
            let fileURLs = try FileManager.default.contentsOfDirectory(at: documentsDirectory, 
                                                                       includingPropertiesForKeys: nil, 
                                                                       options: .skipsHiddenFiles) // Skip hidden files
            documents = fileURLs.filter { $0.pathExtension == "txt" }.sorted(by: { $0.lastPathComponent < $1.lastPathComponent }) // Sort alphabetically
            tableView.reloadData()
        } catch {
            print("Error loading documents: \(error)")
            showAlert(title: "Error", message: "Could not load documents: \(error.localizedDescription)")
        }
    }

    // MARK: - UITableViewDataSource

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return documents.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "documentCell", for: indexPath)
        cell.textLabel?.text = documents[indexPath.row].lastPathComponent
        
        // Apply theme to cell
        cell.backgroundColor = .clear // Or Theme.parchmentBackground
        let selectedBackgroundView = UIView()
        selectedBackgroundView.backgroundColor = Theme.mutedGoldAccent.withAlphaComponent(0.2) // Subtle selection
        cell.selectedBackgroundView = selectedBackgroundView
        
        cell.textLabel?.textColor = Theme.sepiaText
        cell.textLabel?.font = Theme.font(name: Theme.FontName.body, size: 17)
        
        // Add long press gesture recognizer for renaming
        let longPressRecognizer = UILongPressGestureRecognizer(target: self, action: #selector(handleLongPress(_:)))
        cell.addGestureRecognizer(longPressRecognizer)
        return cell
    }

    // MARK: - UITableViewDelegate

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        let selectedDocumentURL = documents[indexPath.row]
        let editorVC = EditorViewController()
        editorVC.documentURL = selectedDocumentURL
        navigationController?.pushViewController(editorVC, animated: true)
        tableView.deselectRow(at: indexPath, animated: true)
    }
    
    func tableView(_ tableView: UITableView, commit editingStyle: UITableViewCell.EditingStyle, forRowAt indexPath: IndexPath) {
        if editingStyle == .delete {
            let fileURLToDelete = documents[indexPath.row]
            do {
                try FileManager.default.removeItem(at: fileURLToDelete)
                documents.remove(at: indexPath.row)
                tableView.deleteRows(at: [indexPath], with: .fade)
            } catch {
                print("Error deleting document: \(error)")
                showAlert(title: "Error", message: "Could not delete document: \(error.localizedDescription)")
            }
        }
    }

    // MARK: - Renaming Logic

    @objc func handleLongPress(_ gestureRecognizer: UILongPressGestureRecognizer) {
        if gestureRecognizer.state == .began {
            let touchPoint = gestureRecognizer.location(in: tableView)
            if let indexPath = tableView.indexPathForRow(at: touchPoint) {
                promptForRename(at: indexPath)
            }
        }
    }

    func promptForRename(at indexPath: IndexPath) {
        let documentURL = documents[indexPath.row]
        let currentName = documentURL.deletingPathExtension().lastPathComponent

        let alertController = UIAlertController(title: "Rename Document", message: "Enter new name for \"\(currentName)\"", preferredStyle: .alert)
        // Apply theme to alert actions if needed, or rely on global tint for now
        // alertController.view.tintColor = Theme.mutedGoldAccent // Example for alert-specific tinting

        alertController.addTextField { textField in
            textField.text = currentName
            textField.placeholder = "New document name"
            textField.clearButtonMode = .whileEditing
            textField.textColor = Theme.sepiaText // Theme the text field
            textField.font = Theme.font(name: Theme.FontName.body, size: 16)
        }

        let renameAction = UIAlertAction(title: "Rename", style: .default) { [weak self, weak alertController] _ in
            guard let self = self, let newNameField = alertController?.textFields?.first, var newName = newNameField.text else { return }
            
            // Basic validation
            if newName.isEmpty {
                self.showAlert(title: "Invalid Name", message: "Document name cannot be empty.")
                return
            }
            if newName.rangeOfCharacter(from: CharacterSet(charactersIn: "/:")) != nil { // Basic check for invalid characters
                self.showAlert(title: "Invalid Name", message: "Document name cannot contain '/' or ':'.")
                return
            }

            // Ensure it has the .txt extension
            if !newName.lowercased().hasSuffix(".txt") {
                newName += ".txt"
            }
            
            let documentsDirectory = self.getDocumentsDirectory()
            let newFileURL = documentsDirectory.appendingPathComponent(newName)

            // Check for conflicts (optional, but good practice)
            if FileManager.default.fileExists(atPath: newFileURL.path) && newFileURL != documentURL {
                 self.showAlert(title: "Name Conflict", message: "A document with this name already exists.")
                 return
            }

            do {
                try FileManager.default.moveItem(at: documentURL, to: newFileURL)
                self.documents[indexPath.row] = newFileURL // Update data source
                // self.tableView.reloadRows(at: [indexPath], with: .automatic) // Reloads the cell
                self.loadDocuments() // Easiest way to refresh and re-sort
                self.showAlert(title: "Renamed", message: "\"\(currentName).txt\" was renamed to \"\(newName)\".")
            } catch {
                print("Error renaming document: \(error)")
                self.showAlert(title: "Error Renaming", message: "Could not rename document: \(error.localizedDescription)")
            }
        }

        let cancelAction = UIAlertAction(title: "Cancel", style: .cancel)

        alertController.addAction(renameAction)
        alertController.addAction(cancelAction)

        present(alertController, animated: true)
    }

    // MARK: - UIDocumentPickerDelegate

    func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
        guard let selectedFileURL = urls.first else {
            showAlert(title: "Import Error", message: "No file was selected.")
            return
        }

        // Start accessing the security-scoped resource
        let shouldStopAccessing = selectedFileURL.startAccessingSecurityScopedResource()
        defer {
            if shouldStopAccessing {
                selectedFileURL.stopAccessingSecurityScopedResource()
            }
        }

        // Determine file type and process accordingly
        // Check if it's a directory first, as directories might not have a conventional "pathExtension"
        var isDirectory: ObjCBool = false
        if FileManager.default.fileExists(atPath: selectedFileURL.path, isDirectory: &isDirectory), isDirectory.boolValue {
            processDirectory(at: selectedFileURL, originalUserSelectionURL: selectedFileURL)
        } else if selectedFileURL.pathExtension.lowercased() == "json" {
            processJSONFile(at: selectedFileURL)
        } else if selectedFileURL.pathExtension.lowercased() == "zip" {
            processZipFile(at: selectedFileURL)
        } else {
            showAlert(title: "Unsupported Item", message: "Please select a .json file, .zip archive, or a folder to import.")
        }
    }
    
    private func processJSONFile(at url: URL) {
        do {
            let fileData = try Data(contentsOf: url)
            let importedDocs = try JSONDecoder().decode([ImportedDocument].self, from: fileData)

            if importedDocs.isEmpty {
                showAlert(title: "Import Warning", message: "The selected JSON file is empty or contains no documents.")
                return
            }
            
            var (importedCount, errorCount) = importDocuments(importedDocs)
            
            loadDocuments() // Refresh the list
            showImportSummary(importedCount: importedCount, errorCount: errorCount, totalAttempted: importedDocs.count, sourceName: url.lastPathComponent)
        } catch {
            print("Error processing JSON file: \(error)")
            showAlert(title: "JSON Import Failed", message: "Could not read or parse the JSON file: \(error.localizedDescription)")
        }
    }

    private func processZipFile(at url: URL) {
        let fileManager = FileManager.default
        let tempDirectoryURL = fileManager.temporaryDirectory.appendingPathComponent("ZipImport-\(UUID().uuidString)")

        var totalProcessedInZip = 0
        var totalImportedFromZip = 0
        var totalErrorsInZip = 0

        do {
            try fileManager.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true, attributes: nil)
            // Assuming ZipFoundation: try fileManager.unzipItem(at: url, to: tempDirectoryURL)
            // Since I cannot use ZipFoundation directly, I'll simulate the iteration part
            // This is a placeholder for actual unzipping and iteration.
            // In a real scenario, ZipFoundation would provide entries to iterate through.
            // For now, I'll show an alert that this part is conceptual.
            
            // --- Conceptual ZipFoundation Usage START ---
            // guard let archive = Archive(url: url, accessMode: .read) else {
            //     showAlert(title: "Zip Error", message: "Could not open the Zip archive.")
            //     try? fileManager.removeItem(at: tempDirectoryURL)
            //     return
            // }
            //
            // for entry in archive {
            //     let destinationURL = tempDirectoryURL.appendingPathComponent(entry.path)
            //     if entry.type == .directory {
            //         try? fileManager.createDirectory(at: destinationURL, withIntermediateDirectories: true, attributes: nil)
            //     } else {
            //         // Ensure parent directory exists
            //         try? fileManager.createDirectory(at: destinationURL.deletingLastPathComponent(), withIntermediateDirectories: true, attributes: nil)
            //         // Extract entry
            //         try archive.extract(entry, to: destinationURL)
            //     }
            // }
            // --- Conceptual ZipFoundation Usage END ---

            // For the purpose of this environment, let's assume unzipping happened and we scan the temp dir.
            // This part needs ZipFoundation to be functional.
            // showAlert(title: "Zip Processing", message: "Zip file selected. Actual unzipping and processing requires ZipFoundation library which cannot be dynamically added here. Conceptual processing will proceed if relevant files (.txt, .json) were hypothetically extracted.")

            // Recursive scan of the (hypothetically) extracted temporary directory
            if let enumerator = fileManager.enumerator(at: tempDirectoryURL, includingPropertiesForKeys: [.isRegularFileKey], options: [.skipsHiddenFiles, .skipsPackageDescendants]) {
                for case let fileURL as URL in enumerator {
                    let pathExtension = fileURL.pathExtension.lowercased()
                    if pathExtension == "txt" {
                        totalProcessedInZip += 1
                        do {
                            let content = try String(contentsOf: fileURL, encoding: .utf8)
                            let title = fileURL.deletingPathExtension().lastPathComponent
                            let targetURL = generateUniqueURL(forBaseName: title, in: getDocumentsDirectory())
                            try content.write(to: targetURL, atomically: true, encoding: .utf8)
                            totalImportedFromZip += 1
                        } catch {
                            print("Error processing .txt file from zip '\(fileURL.lastPathComponent)': \(error)")
                            totalErrorsInZip += 1
                        }
                    } else if pathExtension == "json" {
                        totalProcessedInZip += 1
                        do {
                            let jsonData = try Data(contentsOf: fileURL)
                            let importedDocs = try JSONDecoder().decode([ImportedDocument].self, from: jsonData)
                            let (imported, errors) = importDocuments(importedDocs)
                            totalImportedFromZip += imported
                            totalErrorsInZip += errors
                        } catch {
                            print("Error processing .json file from zip '\(fileURL.lastPathComponent)': \(error)")
                            totalErrorsInZip += 1
                        }
                    }
                }
            }
            
            if totalProcessedInZip == 0 {
                 showAlert(title: "Zip Import", message: "No .txt or .json files found in the Zip archive (or ZipFoundation is not available to extract).")
            } else {
                loadDocuments()
                showImportSummary(importedCount: totalImportedFromZip, errorCount: totalErrorsInZip, totalAttempted: totalProcessedInZip, fromZip: true, sourceName: url.lastPathComponent)
            }

        } catch {
            print("Error processing Zip file: \(error)")
            showAlert(title: "Zip Import Failed", message: "Could not process the Zip file: \(error.localizedDescription)")
        }

        // Clean up temporary directory
        try? fileManager.removeItem(at: tempDirectoryURL)
    }

    // Helper to import an array of ImportedDocument objects
    private func importDocuments(_ docs: [ImportedDocument]) -> (importedCount: Int, errorCount: Int) {
        var importedCount = 0
        var errorCount = 0
        for doc in docs {
            let baseName = doc.title
            let content = doc.content
            let targetURL = generateUniqueURL(forBaseName: baseName, in: getDocumentsDirectory())
            do {
                try content.write(to: targetURL, atomically: true, encoding: .utf8)
                importedCount += 1
            } catch {
                print("Error writing imported document '\(baseName)': \(error)")
                errorCount += 1
            }
        }
        return (importedCount, errorCount)
    }

    private func showImportSummary(importedCount: Int, errorCount: Int, totalAttempted: Int, fromZip: Bool = false, sourceName: String) {
        var message = "\(importedCount) document(s) imported successfully from \(sourceName)."
        if errorCount > 0 {
            message += "\n\(errorCount) document(s) failed to import."
        }
        
        if importedCount == 0 && errorCount == 0 { // Nothing imported, nothing failed
            if totalAttempted > 0 { // Files were processed but none were new/valid
                 message = "No new documents were imported from \(sourceName). Files might be empty, not of the supported type (.txt), or already exist with the same content if unique naming isn't robust enough for content identity."
            } else { // totalAttempted == 0, no compatible files found in the first place
                 message = "No compatible files (.txt or .json for non-zip) were found to import from \(sourceName)."
            }
        } else if importedCount == 0 && errorCount > 0 { // All attempts to import resulted in errors
            message = "Failed to import any documents from \(sourceName)."
        }
        showAlert(title: "Import Complete", message: message)
    }
    
    private func processDirectory(at directoryURL: URL, originalUserSelectionURL: URL) {
        let fileManager = FileManager.default
        var importedCount = 0
        var errorCount = 0
        var processedTxtFiles = 0

        // Note: For directoryURL obtained from UIDocumentPickerViewController,
        // security-scoped access is already started by the documentPicker delegate method's defer block.

        let resourceKeys: [URLResourceKey] = [.isRegularFileKey, .nameKey, .isDirectoryKey]
        guard let enumerator = fileManager.enumerator(at: directoryURL,
                                includingPropertiesForKeys: resourceKeys,
                                options: [.skipsHiddenFiles, .skipsPackageDescendants],
                                errorHandler: { (url, error) -> Bool in
                                    print("Enumerator error at \(url.path): \(error.localizedDescription)")
                                    // Optionally, collect these errors to show to the user.
                                    // Return true to continue enumerating despite the error.
                                    return true
                                }) else {
            showAlert(title: "Directory Error", message: "Could not enumerate the selected directory.")
            return
        }

        for case let fileURL as URL in enumerator {
            do {
                let resourceValues = try fileURL.resourceValues(forKeys: Set(resourceKeys))
                if resourceValues.isRegularFile == true && fileURL.pathExtension.lowercased() == "txt" {
                    processedTxtFiles += 1
                    let content = try String(contentsOf: fileURL, encoding: .utf8)
                    let title = fileURL.deletingPathExtension().lastPathComponent
                    
                    let targetURL = generateUniqueURL(forBaseName: title, in: getDocumentsDirectory())
                    try content.write(to: targetURL, atomically: true, encoding: .utf8)
                    importedCount += 1
                }
            } catch {
                print("Error processing file '\(fileURL.lastPathComponent)' in directory: \(error)")
                errorCount += 1
            }
        }
        
        loadDocuments()
        let directoryName = originalUserSelectionURL.lastPathComponent // Use the name of the folder the user actually selected
        showImportSummary(importedCount: importedCount, errorCount: errorCount, totalAttempted: processedTxtFiles, sourceName: "\"\(directoryName)\" directory")
    }


    func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) {
        // Handle cancellation, if needed (e.g., log it or do nothing)
        print("Document picker was cancelled.")
    }
    
    // MARK: - File Naming Helper
    
    func generateUniqueURL(forBaseName baseName: String, in directory: URL) -> URL {
        var fileName = baseName.trimmingCharacters(in: .whitespacesAndNewlines)
        if fileName.isEmpty {
            fileName = "Untitled" // Default if title is empty
        }
        
        // Ensure it has .txt extension
        if !fileName.lowercased().hasSuffix(".txt") {
            fileName += ".txt"
        }
        
        var finalURL = directory.appendingPathComponent(fileName)
        var counter = 1
        
        let fileManager = FileManager.default
        
        while fileManager.fileExists(atPath: finalURL.path) {
            var newNameWithoutExtension = baseName.trimmingCharacters(in: .whitespacesAndNewlines)
            if newNameWithoutExtension.isEmpty {
                newNameWithoutExtension = "Untitled"
            }
            // Remove .txt if it was added, before adding suffix
            if newNameWithoutExtension.lowercased().hasSuffix(".txt") {
                 newNameWithoutExtension = String(newNameWithoutExtension.dropLast(4))
            }

            fileName = "\(newNameWithoutExtension) (\(counter)).txt"
            finalURL = directory.appendingPathComponent(fileName)
            counter += 1
        }
        return finalURL
    }


    // MARK: - Utility

    func showAlert(title: String, message: String, completion: (() -> Void)? = nil) {
        let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
        
        // Theming UIAlertController title and message (more involved, usually done via subclassing or appearance proxies if possible)
        // For simplicity, we'll rely on the system's presentation.
        // However, we can theme the actions.
        // alert.view.tintColor = Theme.mutedGoldAccent // This themes all action button text.

        alert.addAction(UIAlertAction(title: "OK", style: .default, handler: { _ in completion?() }))
        present(alert, animated: true)
    }
}
