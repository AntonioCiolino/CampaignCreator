import UIKit

class ExportViewController: UIViewController {

    private let markdownText: String
    private var textView: UITextView!
    private var instructionLabel: UILabel!
    private var copyButton: UIButton!
    private var shareButton: UIButton! // Or use UIBarButtonItem if embedded in NavController

    // MARK: - Initialization
    init(markdownText: String) {
        self.markdownText = markdownText
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    // MARK: - View Lifecycle
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = Theme.parchmentBackground // Theme background
        title = "Export for Homebrewery" // Title font set by UIAppearance

        setupInstructionLabel()
        setupTextView()
        setupCopyButton()
        setupShareButton()
        setupConstraints()
        
        // Add a close button if presented modally without a navigation controller
        if self.navigationController == nil {
            let closeButton = UIBarButtonItem(barButtonSystemItem: .done, target: self, action: #selector(closeViewController))
            self.navigationItem.rightBarButtonItem = closeButton
        }
    }

    // MARK: - UI Setup
    private func setupInstructionLabel() {
        instructionLabel = UILabel()
        instructionLabel.text = "Your document is ready to be pasted into Homebrewery. Ensure you've used Markdown syntax and markers like \\page or \\column as needed."
        instructionLabel.font = Theme.font(name: Theme.FontName.body, size: 14)
        instructionLabel.textColor = Theme.sepiaText
        instructionLabel.numberOfLines = 0
        instructionLabel.textAlignment = .center
        instructionLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(instructionLabel)
    }

    private func setupTextView() {
        textView = UITextView()
        textView.text = markdownText
        textView.isEditable = false
        textView.backgroundColor = Theme.editorBackground // Consistent with editor
        textView.textColor = Theme.sepiaText
        textView.font = Theme.font(name: Theme.FontName.editorExportView, size: 13)
        textView.layer.borderColor = Theme.mutedGoldAccent.withAlphaComponent(0.5).cgColor
        textView.layer.borderWidth = 1.0
        textView.layer.cornerRadius = 5.0
        textView.textContainerInset = UIEdgeInsets(top: 8, left: 5, bottom: 8, right: 5)
        textView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(textView)
    }

    private func setupCopyButton() {
        copyButton = UIButton(type: .custom) // Use .custom for full control over styling
        copyButton.setTitle("Copy to Clipboard", for: .normal)
        copyButton.titleLabel?.font = Theme.boldFont(name: Theme.FontName.body, size: 15)
        copyButton.backgroundColor = Theme.mutedGoldAccent
        copyButton.setTitleColor(Theme.parchmentBackground, for: .normal) // Light text on dark gold
        copyButton.layer.cornerRadius = 8.0
        copyButton.addTarget(self, action: #selector(copyToClipboardTapped), for: .touchUpInside)
        copyButton.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(copyButton)
    }
    
    private func setupShareButton() {
        shareButton = UIButton(type: .custom) // Use .custom for full control
        shareButton.setTitle("Share", for: .normal)
        shareButton.titleLabel?.font = Theme.boldFont(name: Theme.FontName.body, size: 15)
        shareButton.backgroundColor = Theme.mutedGoldAccent
        shareButton.setTitleColor(Theme.parchmentBackground, for: .normal) // Light text on dark gold
        shareButton.layer.cornerRadius = 8.0
        shareButton.addTarget(self, action: #selector(shareTapped), for: .touchUpInside)
        shareButton.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(shareButton)
    }

    private func setupConstraints() {
        let safeArea = view.safeAreaLayoutGuide
        NSLayoutConstraint.activate([
            instructionLabel.topAnchor.constraint(equalTo: safeArea.topAnchor, constant: 16),
            instructionLabel.leadingAnchor.constraint(equalTo: safeArea.leadingAnchor, constant: 16),
            instructionLabel.trailingAnchor.constraint(equalTo: safeArea.trailingAnchor, constant: -16),

            textView.topAnchor.constraint(equalTo: instructionLabel.bottomAnchor, constant: 8),
            textView.leadingAnchor.constraint(equalTo: safeArea.leadingAnchor, constant: 16),
            textView.trailingAnchor.constraint(equalTo: safeArea.trailingAnchor, constant: -16),
            
            // Buttons layout (simple horizontal stack for now)
            copyButton.topAnchor.constraint(equalTo: textView.bottomAnchor, constant: 16),
            copyButton.leadingAnchor.constraint(equalTo: safeArea.leadingAnchor, constant: 16),
            copyButton.trailingAnchor.constraint(equalTo: view.centerXAnchor, constant: -8), // Half width
            copyButton.bottomAnchor.constraint(equalTo: safeArea.bottomAnchor, constant: -16),
            copyButton.heightAnchor.constraint(equalToConstant: 44),

            shareButton.topAnchor.constraint(equalTo: textView.bottomAnchor, constant: 16),
            shareButton.leadingAnchor.constraint(equalTo: view.centerXAnchor, constant: 8), // Half width
            shareButton.trailingAnchor.constraint(equalTo: safeArea.trailingAnchor, constant: -16),
            shareButton.bottomAnchor.constraint(equalTo: safeArea.bottomAnchor, constant: -16),
            shareButton.heightAnchor.constraint(equalToConstant: 44),
        ])
    }

    // MARK: - Actions
    @objc private func copyToClipboardTapped() {
        UIPasteboard.general.string = markdownText
        showAlert(title: "Copied", message: "Markdown copied to clipboard.")
    }
    
    @objc private func shareTapped() {
        let activityViewController = UIActivityViewController(activityItems: [markdownText], applicationActivities: nil)
        // For iPad, specify the source view/rect for the popover
        if let popoverController = activityViewController.popoverPresentationController {
            popoverController.sourceView = shareButton // Or another view
            popoverController.sourceRect = shareButton.bounds
        }
        present(activityViewController, animated: true, completion: nil)
    }
    
    @objc private func closeViewController() {
        dismiss(animated: true, completion: nil)
    }
    
    // MARK: - Utility
    private func showAlert(title: String, message: String) {
        let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
        // alert.view.tintColor = Theme.mutedGoldAccent // Optional: Theme alert actions
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}
