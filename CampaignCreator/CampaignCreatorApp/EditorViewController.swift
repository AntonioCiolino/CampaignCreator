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

    private var activityIndicator: UIActivityIndicatorView!

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = Theme.parchmentBackground // Theme background
        // Title will be set by the segmented control
        
        loadSelectedLLMProvider() // Load preference first
        updateLLMService() // Initialize llmService
        
        setupTextView()
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
        NSLayoutConstraint.activate([
            textView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 8), // Add some padding
            textView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -8),
            textView.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 8),
            textView.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -8)
        ])
    }

    func setupNavigationBar() {
        // SF Symbols for buttons. Tint color is handled by UIAppearance.
        let saveButtonImage = UIImage(systemName: "square.and.arrow.down.fill")
        let suggestButtonImage = UIImage(systemName: "lightbulb.fill")
        let exportHomebreweryButtonImage = UIImage(systemName: "doc.richtext.fill")

        let saveButton = UIBarButtonItem(image: saveButtonImage, style: .plain, target: self, action: #selector(saveDocument))
        let suggestButton = UIBarButtonItem(image: suggestButtonImage, style: .plain, target: self, action: #selector(handleSuggestButtonTapped))
        let exportHomebreweryButton = UIBarButtonItem(image: exportHomebreweryButtonImage, style: .plain, target: self, action: #selector(handleExportHomebreweryTapped))
        
        navigationItem.rightBarButtonItems = [saveButton, suggestButton, exportHomebreweryButton]
        
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
        let homebreweryMarkdown = markdownGenerator.generateHomebreweryMarkdown(from: currentText)

        let exportVC = ExportViewController(markdownText: homebreweryMarkdown)
        let navigationController = UINavigationController(rootViewController: exportVC)
        // For modal presentation, ensure there's a way to dismiss (ExportViewController adds a Done button)
        present(navigationController, animated: true, completion: nil)
    }

    @objc func handleSuggestButtonTapped() {
        guard let prompt = textView.text, !prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            showAlert(title: "Empty Prompt", message: "Please enter some text to get suggestions.")
            return
        }

        activityIndicator.startAnimating()
        view.isUserInteractionEnabled = false // Disable UI while loading

        llmService.generateCompletion(prompt: prompt) { [weak self] result in
            DispatchQueue.main.async {
                self?.activityIndicator.stopAnimating()
                self?.view.isUserInteractionEnabled = true // Re-enable UI

                switch result {
                case .success(let completionText):
                    // Append suggestion and mark changes
                    self?.textView.text += completionText
                    self?.hasMadeChanges = true
                    self?.showAlert(title: "Suggestion Applied", message: "Text suggestion has been appended.")
                case .failure(let error):
                    // If apiKeyMissing, guide the user.
                    if case .apiKeyMissing = error {
                        let keyName = self?.selectedLLMProvider == .openAI ? "OpenAI" : "Gemini"
                        self?.showAlert(title: "API Key Missing", message: "Please set your \(keyName) API key in Secrets.swift and rebuild the app.")
                    } else {
                        self?.showAlert(title: "Suggestion Failed", message: error.localizedDescription)
                    }
                    print("LLM Error: \(String(describing: self?.selectedLLMProvider.rawValue)) - \(error.localizedDescription)")
                }
            }
        }
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
