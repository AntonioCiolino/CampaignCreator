import SwiftUI
import CampaignCreatorLib
import SwiftData

struct RichTextEditorView: UIViewRepresentable {
    @Binding var text: NSAttributedString
    var onSnippetEdit: ((String) -> Void)?
    var onSelectionChange: ((NSRange) -> Void)?
    var featureService: FeatureService
    @EnvironmentObject var imageUploadService: ImageUploadService

    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView()
        textView.delegate = context.coordinator
        context.coordinator.textView = textView

        // No toolbar

        let menuInteraction = UIContextMenuInteraction(delegate: context.coordinator)
        textView.addInteraction(menuInteraction)

        return textView
    }

    func updateUIView(_ uiView: UITextView, context: Context) {
        uiView.attributedText = text
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, UITextViewDelegate, UIImagePickerControllerDelegate, UINavigationControllerDelegate, UIContextMenuInteractionDelegate {
        var parent: RichTextEditorView
        weak var textView: UITextView?
        private var features: [Feature] = []

        init(_ parent: RichTextEditorView) {
            self.parent = parent
            super.init()
            fetchFeatures()
        }

        private func fetchFeatures() {
            Task {
                do {
                    self.features = try await self.parent.featureService.fetchFeatures().filter { $0.feature_category == "Snippet" }
                } catch {
                    // Handle error
                    print("Failed to fetch features: \(error)")
                }
            }
        }

        func textViewDidChange(_ textView: UITextView) {
            parent.text = textView.attributedText
            parent.onSelectionChange?(textView.selectedRange)
        }

        func textViewDidChangeSelection(_ textView: UITextView) {
            // No need to do anything here
        }

        func textView(_ textView: UITextView, shouldChangeTextIn range: NSRange, replacementText text: String) -> Bool {
            if text == "\n" {
                textView.insertText("\n")
                return false
            }
            return true
        }

        @objc func toggleBold() {
            toggleFontTrait(.traitBold)
        }

        @objc func toggleItalic() {
            toggleFontTrait(.traitItalic)
        }

        @objc func toggleUnderline() {
            guard let textView = textView else { return }
            let range = textView.selectedRange
            let attributedString = NSMutableAttributedString(attributedString: textView.attributedText)

            if range.length > 0 {
                let existingAttributes = attributedString.attributes(at: range.location, effectiveRange: nil)
                if existingAttributes[.underlineStyle] == nil {
                    attributedString.addAttribute(.underlineStyle, value: NSUnderlineStyle.single.rawValue, range: range)
                } else {
                    attributedString.removeAttribute(.underlineStyle, range: range)
                }
            }

            parent.text = attributedString
        }

        @objc func insertImage() {
            let imagePicker = UIImagePickerController()
            imagePicker.delegate = self
            imagePicker.sourceType = .photoLibrary

            if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
               let rootViewController = windowScene.windows.first?.rootViewController {
                rootViewController.present(imagePicker, animated: true)
            }
        }

        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            picker.dismiss(animated: true)

            guard let image = info[.originalImage] as? UIImage, let textView = textView else { return }

            parent.imageUploadService.uploadImage(image) { result in
                switch result {
                case .success(let url):
                    let attributedString = NSAttributedString(string: "\n![image](\(url))\n")
                    let mutableAttributedString = NSMutableAttributedString(attributedString: textView.attributedText)
                    mutableAttributedString.insert(attributedString, at: textView.selectedRange.location)

                    self.parent.text = mutableAttributedString
                case .failure(let error):
                    print("Failed to upload image: \(error)")
                }
            }
        }

        private func toggleFontTrait(_ trait: UIFontDescriptor.SymbolicTraits) {
            guard let textView = textView else { return }
            let range = textView.selectedRange
            let attributedString = NSMutableAttributedString(attributedString: textView.attributedText)

            if range.length > 0 {
                let existingAttributes = attributedString.attributes(at: range.location, effectiveRange: nil)
                let existingFont = existingAttributes[.font] as? UIFont ?? UIFont.systemFont(ofSize: 14)

                var newFont: UIFont
                if existingFont.fontDescriptor.symbolicTraits.contains(trait) {
                    newFont = UIFont(descriptor: existingFont.fontDescriptor.withSymbolicTraits(existingFont.fontDescriptor.symbolicTraits.subtracting(trait))!, size: existingFont.pointSize)
                } else {
                    newFont = UIFont(descriptor: existingFont.fontDescriptor.withSymbolicTraits(existingFont.fontDescriptor.symbolicTraits.union(trait))!, size: existingFont.pointSize)
                }

                attributedString.addAttribute(.font, value: newFont, range: range)
            }

            parent.text = attributedString
        }

        func contextMenuInteraction(_ interaction: UIContextMenuInteraction, configurationForMenuAtLocation location: CGPoint) -> UIContextMenuConfiguration? {
            guard let textView = textView else { return nil }

            return UIContextMenuConfiguration(identifier: nil, previewProvider: nil) { suggestedActions in
                let bold = UIAction(title: "Bold", image: UIImage(systemName: "bold")) { _ in
                    self.toggleBold()
                }

                let italic = UIAction(title: "Italic", image: UIImage(systemName: "italic")) { _ in
                    self.toggleItalic()
                }

                let underline = UIAction(title: "Underline", image: UIImage(systemName: "underline")) { _ in
                    self.toggleUnderline()
                }

                let insertImage = UIAction(title: "Insert Image", image: UIImage(systemName: "photo")) { _ in
                    self.insertImage()
                }

                let formattingMenu = UIMenu(title: "Format", children: [bold, italic, underline, insertImage])

                let aiActions = self.features.map { feature in
                    UIAction(title: feature.name, image: UIImage(systemName: "wand.and.stars")) { action in
                        self.parent.onSnippetEdit?(feature.name)
                    }
                }

                let aiMenu = UIMenu(title: "AI Edits", children: aiActions)

                if textView.selectedRange.length > 0 {
                    return UIMenu(title: "", children: [formattingMenu, aiMenu])
                } else {
                    return UIMenu(title: "", children: [insertImage])
                }
            }
        }
    }
}
