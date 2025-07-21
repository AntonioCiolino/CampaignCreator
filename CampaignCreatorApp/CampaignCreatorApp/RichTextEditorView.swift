import SwiftUI
import CampaignCreatorLib
import SwiftData

struct RichTextEditorView: UIViewRepresentable {
    @Binding var text: NSAttributedString
    var onSnippetEdit: ((String) -> Void)?
    var onSelectionChange: ((NSRange) -> Void)?
    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView()
        textView.delegate = context.coordinator
        context.coordinator.textView = textView

        let toolbar = UIToolbar(frame: CGRect(x: 0, y: 0, width: 100, height: 44))
        let boldButton = UIBarButtonItem(title: "Bold", style: .plain, target: context.coordinator, action: #selector(Coordinator.toggleBold))
        let italicButton = UIBarButtonItem(title: "Italic", style: .plain, target: context.coordinator, action: #selector(Coordinator.toggleItalic))
        let underlineButton = UIBarButtonItem(title: "Underline", style: .plain, target: context.coordinator, action: #selector(Coordinator.toggleUnderline))
        let imageButton = UIBarButtonItem(image: UIImage(systemName: "photo"), style: .plain, target: context.coordinator, action: #selector(Coordinator.insertImage))

        toolbar.items = [boldButton, italicButton, underlineButton, imageButton]
        textView.inputAccessoryView = toolbar

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
                    let featureService = FeatureService(modelContext: try! ModelContainer(for: CampaignModel.self, CharacterModel.self, MemoryModel.self, ChatMessageModel.self, UserModel.self).mainContext)
                    self.features = try await featureService.fetchFeatures().filter { $0.feature_category == "Snippet" }
                } catch {
                    // Handle error
                    print("Failed to fetch features: \(error)")
                }
            }
        }

        func textViewDidChange(_ textView: UITextView) {
            parent.text = textView.attributedText
        }

        func textViewDidChangeSelection(_ textView: UITextView) {
            parent.onSelectionChange?(textView.selectedRange)
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

            let attachment = NSTextAttachment()
            attachment.image = image

            let attributedString = NSAttributedString(attachment: attachment)
            let mutableAttributedString = NSMutableAttributedString(attributedString: textView.attributedText)
            mutableAttributedString.insert(attributedString, at: textView.selectedRange.location)

            parent.text = mutableAttributedString
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
            guard let textView = textView, textView.selectedRange.length > 0 else { return nil }

            return UIContextMenuConfiguration(identifier: nil, previewProvider: nil) { suggestedActions in
                let actions = self.features.map { feature in
                    UIAction(title: feature.name, image: UIImage(systemName: "wand.and.stars")) { action in
                        self.parent.onSnippetEdit?(feature.name)
                    }
                }

                return UIMenu(title: "AI Edits", children: actions)
            }
        }
    }
}
