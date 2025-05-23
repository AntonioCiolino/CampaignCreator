import UIKit

class EditorViewController: UIViewController {

    var documentURL: URL?
    let textView = UITextView()
    var hasMadeChanges: Bool = false

    // LLM Selection
    enum LLMProvider: String, CaseIterable {
        case openAI = "OpenAI"
        case gemini = "Gemini"
    }
    private var selectedLLMProvider: LLMProvider = .openAI {
        didSet {
            updateLLMService()
            UserDefaults.standard.set(selectedLLMProvider.rawValue, forKey: "selectedLLMProvider")
        }
    }
    private var llmService: LLMService! // Will be initialized based on selection
    private var llmSegmentedControl: UISegmentedControl!
    private var temperatureSlider: UISlider!
    private var temperatureLabel: UILabel!
    private let randomTableService = RandomTableService()
    private var currentTemperature: Double = 0.7 // Default temperature
    private var thematicImageView: UIImageView!

    private var activityIndicator: UIActivityIndicatorView!

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = Theme.parchmentBackground // Theme background
        // Title will be set by the segmented control
        
        loadSelectedLLMProvider() // Load preference first
        updateLLMService() // Initialize llmService
        
        setupTemperatureControls()
        setupThematicImageView() // Setup image view
        setupTextView() // Setup text view, potentially constrained to image view
        setupNavigationBar() // This will now include the segmented control
        setupActivityIndicator() // Setup the activity indicator
        loadDocumentContent()
        
        // Observe text changes to set hasMadeChanges flag
        NotificationCenter.default.addObserver(self, selector: #selector(textDidChange), name: UITextView.textDidChangeNotification, object: textView)
    }

    private func loadSelectedLLMProvider() {
        if let savedProviderRawValue = UserDefaults.standard.string(forKey: "selectedLLMProvider"),
           let provider = LLMProvider(rawValue: savedProviderRawValue) {
            selectedLLMProvider = provider
        } else {
            selectedLLMProvider = .openAI // Default
        }
    }

    private func updateLLMService() {
        switch selectedLLMProvider {
        case .openAI:
            llmService = OpenAIClient()
        case .gemini:
            llmService = GeminiClient()
        }
    }
    
    @objc private func llmProviderChanged(_ sender: UISegmentedControl) {
        selectedLLMProvider = sender.selectedSegmentIndex == 0 ? .openAI : .gemini
        // llmService is updated by the didSet of selectedLLMProvider
    }

    func setupActivityIndicator() {
        activityIndicator = UIActivityIndicatorView(style: .large)
        activityIndicator.color = Theme.mutedGoldAccent // Theme activity indicator
        activityIndicator.hidesWhenStopped = true
        activityIndicator.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(activityIndicator)
        NSLayoutConstraint.activate([
            activityIndicator.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            activityIndicator.centerYAnchor.constraint(equalTo: view.centerYAnchor)
        ])
    }

    func setupTextView() {
        view.addSubview(textView)
        textView.backgroundColor = Theme.editorBackground // Slightly different background for editor area
        textView.textColor = Theme.sepiaText
        textView.font = Theme.font(name: Theme.FontName.editor, size: 16)
        textView.isEditable = true
        textView.layer.borderColor = Theme.mutedGoldAccent.withAlphaComponent(0.5).cgColor // Subtle border
        textView.layer.borderWidth = 1.0
        textView.layer.cornerRadius = 5.0
        textView.textContainerInset = UIEdgeInsets(top: 8, left: 5, bottom: 8, right: 5) // Padding

        textView.translatesAutoresizingMaskIntoConstraints = false
        // Adjust constraints later to accommodate the slider
        NSLayoutConstraint.activate([
            textView.topAnchor.constraint(equalTo: temperatureLabel.bottomAnchor, constant: 8), // Below temperature label
            textView.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 8),
            textView.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -8),
            // textView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -8) // Original
            textView.bottomAnchor.constraint(equalTo: thematicImageView.topAnchor, constant: -8) // Constrain to top of thematicImageView
        ])
    }

    func setupThematicImageView() {
        thematicImageView = UIImageView()
        thematicImageView.isHidden = true // Initially hidden
        thematicImageView.contentMode = .scaleAspectFit
        thematicImageView.backgroundColor = .lightGray // Placeholder
        thematicImageView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(thematicImageView)

        NSLayoutConstraint.activate([
            thematicImageView.widthAnchor.constraint(equalToConstant: 120), // Adjusted size
            thematicImageView.heightAnchor.constraint(equalToConstant: 120), // Adjusted size
            thematicImageView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -10),
            thematicImageView.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -10)
        ])
    }
    
    func setupTemperatureControls() {
        temperatureSlider = UISlider()
        temperatureSlider.minimumValue = 0.0
        temperatureSlider.maximumValue = 1.0
        temperatureSlider.value = Float(currentTemperature)
        temperatureSlider.addTarget(self, action: #selector(temperatureSliderChanged(_:)), for: .valueChanged)
        temperatureSlider.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(temperatureSlider)

        temperatureLabel = UILabel()
        temperatureLabel.text = String(format: "Temp: %.2f", currentTemperature)
        temperatureLabel.font = Theme.font(name: Theme.FontName.body, size: 12)
        temperatureLabel.textColor = Theme.sepiaText
        temperatureLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(temperatureLabel)

        NSLayoutConstraint.activate([
            temperatureLabel.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 8),
            temperatureLabel.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 8),
            
            temperatureSlider.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 8),
            temperatureSlider.leadingAnchor.constraint(equalTo: temperatureLabel.trailingAnchor, constant: 8),
            temperatureSlider.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -8),
        ])
    }
    
    @objc func temperatureSliderChanged(_ sender: UISlider) {
        currentTemperature = Double(sender.value)
        temperatureLabel.text = String(format: "Temp: %.2f", currentTemperature)
    }

    func setupNavigationBar() {
        // SF Symbols for buttons. Tint color is handled by UIAppearance.
        let saveButtonImage = UIImage(systemName: "square.and.arrow.down.fill")
        let exportHomebreweryButtonImage = UIImage(systemName: "doc.richtext.fill")
        let generateButtonImage = UIImage(systemName: "wand.and.stars")

        let saveButton = UIBarButtonItem(image: saveButtonImage, style: .plain, target: self, action: #selector(saveDocument))
        let exportHomebreweryButton = UIBarButtonItem(image: exportHomebreweryButtonImage, style: .plain, target: self, action: #selector(handleExportHomebreweryTapped))
        
        let generateConceptAction = UIAction(title: "Generate Campaign Concept", image: UIImage(systemName: "doc.text.image")) { [weak self] _ in
            self?.handleGenerateConcept()
        }
        let generateToCAction = UIAction(title: "Generate Table of Contents", image: UIImage(systemName: "list.bullet.indent")) { [weak self] _ in
            self?.handleGenerateToC()
        }
        let suggestTitlesAction = UIAction(title: "Suggest Campaign Titles", image: UIImage(systemName: "text.magnifyingglass")) { [weak self] _ in
            self?.handleSuggestTitles()
        }
        let continueWritingAction = UIAction(title: "Continue Writing", image: UIImage(systemName: "pencil.and.outline")) { [weak self] _ in
            self?.handleContinueWriting()
        }

        let generateMenu = UIMenu(title: "Generate Content", children: [generateConceptAction, generateToCAction, suggestTitlesAction, continueWritingAction])
        let generateButton = UIBarButtonItem(image: generateButtonImage, menu: generateMenu)
        
        let randomItemButtonImage = UIImage(systemName: "dice.fill")
        let randomItemButton = UIBarButtonItem(image: randomItemButtonImage, style: .plain, target: self, action: #selector(handleRandomItemButtonTapped))
        
        let imageGenButtonImage = UIImage(systemName: "photo.on.rectangle.angled")
        let imageGenButton = UIBarButtonItem(image: imageGenButtonImage, style: .plain, target: self, action: #selector(handleGenerateImageButtonTapped))

        navigationItem.rightBarButtonItems = [saveButton, generateButton, randomItemButton, imageGenButton, exportHomebreweryButton]
        
        // LLM Provider Segmented Control
        llmSegmentedControl = UISegmentedControl(items: [LLMProvider.openAI.rawValue, LLMProvider.gemini.rawValue])
        llmSegmentedControl.selectedSegmentIndex = (selectedLLMProvider == .openAI) ? 0 : 1
        llmSegmentedControl.addTarget(self, action: #selector(llmProviderChanged(_:)), for: .valueChanged)
        
        // Theming for segmented control to match nav bar
        llmSegmentedControl.backgroundColor = Theme.navigationBarBackground.withAlphaComponent(0.5) // Slight transparency
        llmSegmentedControl.selectedSegmentTintColor = Theme.mutedGoldAccent
        llmSegmentedControl.setTitleTextAttributes([.foregroundColor: Theme.navigationBarText, .font: Theme.font(name: Theme.FontName.body, size: 13)], for: .normal)
        llmSegmentedControl.setTitleTextAttributes([.foregroundColor: Theme.sepiaText, .font: Theme.font(name: Theme.FontName.body, size: 13)], for: .selected)


        navigationItem.titleView = llmSegmentedControl
        
        // Add a back button that checks for unsaved changes. Text color set by UIAppearance.
        self.navigationItem.hidesBackButton = true 
        let backButton = UIBarButtonItem(title: "Back", style: .plain, target: self, action: #selector(handleBackButton))
        self.navigationItem.leftBarButtonItem = backButton
    }

    @objc func handleExportHomebreweryTapped() {
        guard let currentText = textView.text, !currentText.isEmpty else {
            showAlert(title: "Empty Document", message: "There is no content to export.")
            return
        }

        let markdownGenerator = MarkdownGenerator()
        
        // Simplified input gathering
        let mainContent = currentText
        let campaignTitle = self.title ?? (documentURL?.deletingPathExtension().lastPathComponent ?? "My Campaign")
        
        // Concept Header: First non-empty line, or placeholder
        let conceptHeader = mainContent.split(separator: "\n").first(where: { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }) ?? "Campaign Overview"
        
        // Table of Contents: Search for a line starting with "Table of Contents:", case-insensitive
        var tableOfContentsRaw = ""
        if let tocRange = mainContent.range(of: "Table of Contents:", options: .caseInsensitive) {
            // Find the end of the ToC section (e.g., next major heading or end of document)
            let subsequentText = mainContent[tocRange.upperBound...]
            if let nextSectionRange = subsequentText.range(of: "\n#") { // Assuming sections start with #
                 tableOfContentsRaw = String(subsequentText[..<nextSectionRange.lowerBound])
            } else {
                 tableOfContentsRaw = String(subsequentText)
            }
            // Remove the "Table of Contents:" line itself as the generator adds its own title
            tableOfContentsRaw = tableOfContentsRaw.replacingOccurrences(of: "Table of Contents:", with: "", options: .caseInsensitive).trimmingCharacters(in: .whitespacesAndNewlines)

        } else if let tocRangeLegacy = mainContent.range(of: PromptLibrary.generateTableOfContents.replacingOccurrences(of: "%@", with: ""), options: .literal) {
            // Handle if the old ToC prompt is still in the text
             let subsequentText = mainContent[tocRangeLegacy.upperBound...]
             if let nextSectionRange = subsequentText.range(of: "\n#") {
                 tableOfContentsRaw = String(subsequentText[..<nextSectionRange.lowerBound])
             } else {
                 tableOfContentsRaw = String(subsequentText)
             }
        }


        let homebreweryMarkdown = markdownGenerator.generateHomebreweryMarkdown(
            mainContent: mainContent,
            campaignTitle: campaignTitle,
            conceptHeader: String(conceptHeader),
            tableOfContentsRaw: tableOfContentsRaw
        )

        let exportVC = ExportViewController(markdownText: homebreweryMarkdown)
        let navigationController = UINavigationController(rootViewController: exportVC)
        // For modal presentation, ensure there's a way to dismiss (ExportViewController adds a Done button)
        present(navigationController, animated: true, completion: nil)
    }

    // MARK: - Image Generation Handler
    @objc private func handleGenerateImageButtonTapped() {
        // Placeholder for now - actual logic will be in the next subtask
        print("Generate Image button tapped. Prompt determination and LLM call to be implemented.")
        // For testing visibility:
        // thematicImageView.isHidden = !thematicImageView.isHidden
        // showAlert(title: "Image Gen", message: "To be implemented.")
    }

    // MARK: - Random Table Action Handlers
    @objc func handleRandomItemButtonTapped() {
        let tableNames = randomTableService.getAllTableNames()
        if tableNames.isEmpty {
            showAlert(title: "No Tables", message: "No random tables available.")
            return
        }

        let alertController = UIAlertController(title: "Select Table", message: nil, preferredStyle: .actionSheet)

        for tableName in tableNames {
            let action = UIAlertAction(title: tableName, style: .default) { [weak self] _ in
                self?.generateRandomItem(fromTable: tableName)
            }
            alertController.addAction(action)
        }

        let cancelAction = UIAlertAction(title: "Cancel", style: .cancel, handler: nil)
        alertController.addAction(cancelAction)

        // For iPad, provide sourceView/sourceRect for popover
        if let popoverController = alertController.popoverPresentationController {
            if let randomButtonView = navigationItem.rightBarButtonItems?.first(where: { $0.action == #selector(handleRandomItemButtonTapped) })?.value(forKey: "view") as? UIView {
                 popoverController.sourceView = randomButtonView
                 popoverController.sourceRect = randomButtonView.bounds
            } else { // Fallback if the button view cannot be found
                popoverController.sourceView = self.view
                popoverController.sourceRect = CGRect(x: self.view.bounds.midX, y: self.view.bounds.midY, width: 0, height: 0)
                popoverController.permittedArrowDirections = []
            }
        }
        present(alertController, animated: true, completion: nil)
    }

    private func generateRandomItem(fromTable tableName: String) {
        if let item = randomTableService.getRandomItem(fromTableNamed: tableName) {
            if !self.textView.text.isEmpty {
                self.textView.text += "\n" + item
            } else {
                self.textView.text += item
            }
            self.hasMadeChanges = true
            // Optionally show confirmation, but might be too noisy.
            // showAlert(title: "Item Added", message: "\"\(item)\" from \"\(tableName)\" was added.")
        } else {
            showAlert(title: "Error", message: "Could not get random item from \"\(tableName)\".")
        }
    }

    // MARK: - New LLM Action Handlers
    @objc func handleGenerateConcept() {
        guard let userInput = textView.text, !userInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            showAlert(title: "Empty Input", message: "Please enter some concepts to generate a campaign.")
            return
        }
        activityIndicator.startAnimating()
        view.isUserInteractionEnabled = false
        llmService.generateCampaignConcept(userInput: userInput) { [weak self] result in
            DispatchQueue.main.async {
                self?.activityIndicator.stopAnimating()
                self?.view.isUserInteractionEnabled = true
                switch result {
                case .success(let conceptText):
                    self?.textView.text = conceptText
                    self?.hasMadeChanges = true
                    self?.showAlert(title: "Concept Generated", message: "Campaign concept has been generated and replaced current text.")
                case .failure(let error):
                    self?.handleLLMError(error)
                }
            }
        }
    }

    @objc func handleGenerateToC() {
        guard let campaignText = textView.text, !campaignText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            showAlert(title: "Empty Document", message: "There is no content to generate a Table of Contents from.")
            return
        }
        activityIndicator.startAnimating()
        view.isUserInteractionEnabled = false
        llmService.generateTableOfContents(campaignText: campaignText) { [weak self] result in
            DispatchQueue.main.async {
                self?.activityIndicator.stopAnimating()
                self?.view.isUserInteractionEnabled = true
                switch result {
                case .success(let tocText):
                    self?.textView.text += "\n\n" + tocText
                    self?.hasMadeChanges = true
                    self?.showAlert(title: "ToC Generated", message: "Table of Contents has been appended.")
                case .failure(let error):
                    self?.handleLLMError(error)
                }
            }
        }
    }

    @objc func handleSuggestTitles() {
        guard let campaignConcept = textView.text, !campaignConcept.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            showAlert(title: "Empty Concept", message: "Please provide some campaign concept text to generate titles.")
            return
        }
        activityIndicator.startAnimating()
        view.isUserInteractionEnabled = false
        llmService.generateCampaignTitles(campaignConcept: campaignConcept) { [weak self] result in
            DispatchQueue.main.async {
                self?.activityIndicator.stopAnimating()
                self?.view.isUserInteractionEnabled = true
                switch result {
                case .success(let titles):
                    let titleString = titles.joined(separator: "\n")
                    self?.showAlert(title: "Suggested Titles", message: titleString.isEmpty ? "No titles generated." : titleString)
                case .failure(let error):
                    self?.handleLLMError(error)
                }
            }
        }
    }

    @objc func handleContinueWriting() {
        guard let currentChapterText = textView.text, !currentChapterText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            showAlert(title: "Empty Text", message: "There is no text to continue from.")
            return
        }
        activityIndicator.startAnimating()
        view.isUserInteractionEnabled = false
        // Simplified: campaignText and tocText are empty for now.
        llmService.continueWritingSection(campaignText: "", tocText: "", currentChapterText: currentChapterText, temperature: currentTemperature) { [weak self] result in
            DispatchQueue.main.async {
                self?.activityIndicator.stopAnimating()
                self?.view.isUserInteractionEnabled = true
                switch result {
                case .success(let continuedText):
                    self?.textView.text += continuedText
                    self?.hasMadeChanges = true
                    self?.showAlert(title: "Text Continued", message: "Additional text has been appended.")
                case .failure(let error):
                    self?.handleLLMError(error)
                }
            }
        }
    }
    
    private func handleLLMError(_ error: LLMError) {
        if case .apiKeyMissing = error {
            let keyName = self.selectedLLMProvider == .openAI ? "OpenAI" : "Gemini"
            self.showAlert(title: "API Key Missing", message: "Please set your \(keyName) API key in Secrets.swift and rebuild the app.")
        } else {
            self.showAlert(title: "LLM Error", message: error.localizedDescription)
        }
        print("LLM Error: \(String(describing: self.selectedLLMProvider.rawValue)) - \(error.localizedDescription)")
    }


    func loadDocumentContent() {
        guard let url = documentURL else {
            textView.text = ""
            showAlert(title: "Error", message: "No document URL provided.")
            return
        }
        do {
            let content = try String(contentsOf: url, encoding: .utf8)
            textView.text = content
            hasMadeChanges = false // Reset after loading
        } catch {
            print("Error loading document content: \(error)")
            textView.text = "" // Clear text view on error
            showAlert(title: "Error", message: "Could not load document: \(error.localizedDescription)")
        }
    }

    @objc func saveDocument() {
        guard let url = documentURL else {
            showAlert(title: "Error", message: "Cannot save, document URL is missing.")
            return
        }
        guard let content = textView.text else {
            showAlert(title: "Error", message: "Cannot save, no content found.")
            return
        }
        
        do {
            try content.write(to: url, atomically: true, encoding: .utf8)
            hasMadeChanges = false // Reset after saving
            showAlert(title: "Saved", message: "Document saved successfully.")
            // Update title in case it was a new untitled document that got its name from saving (not currently the flow, but good practice)
            title = url.deletingPathExtension().lastPathComponent
        } catch {
            print("Error saving document: \(error)")
            showAlert(title: "Error", message: "Could not save document: \(error.localizedDescription)")
        }
    }
    
    @objc func textDidChange(_ notification: Notification) {
        hasMadeChanges = true
    }

    @objc func handleBackButton() {
        if hasMadeChanges {
            let alert = UIAlertController(title: "Unsaved Changes", message: "You have unsaved changes. Do you want to save them before going back?", preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "Save", style: .default, handler: { [weak self] _ in
                self?.saveDocument()
                self?.navigationController?.popViewController(animated: true)
            }))
            alert.addAction(UIAlertAction(title: "Discard", style: .destructive, handler: { [weak self] _ in
                self?.navigationController?.popViewController(animated: true)
            }))
            alert.addAction(UIAlertAction(title: "Cancel", style: .cancel, handler: nil))
            present(alert, animated: true)
        } else {
            navigationController?.popViewController(animated: true)
        }
    }
    
    deinit {
        NotificationCenter.default.removeObserver(self)
    }

    // MARK: - Utility
    func showAlert(title: String, message: String, completion: (() -> Void)? = nil) {
        let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
        // Alert actions are tinted by the global tint color if not set directly on alert.view.tintColor
        // For this theme, this might mean alert actions are white if nav bar tint is globally applied.
        // If alert actions need specific color (e.g. Theme.mutedGoldAccent):
        // alert.view.tintColor = Theme.mutedGoldAccent
        alert.addAction(UIAlertAction(title: "OK", style: .default, handler: { _ in completion?() }))
        present(alert, animated: true)
    }
}
