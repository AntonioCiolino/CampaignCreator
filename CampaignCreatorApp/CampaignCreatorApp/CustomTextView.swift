import SwiftUI
import UIKit

struct CustomTextView: UIViewRepresentable {
    @Binding var text: String
    // @Binding var selectedRange: NSRange // REMOVED selectedRange binding for now

    private var font: UIFont = .systemFont(ofSize: 16)
    private var textColor: UIColor = .label
    private var temporaryBackgroundColor: UIColor = .clear // Changed for integration
    var onCoordinatorCreated: ((Coordinator) -> Void)? // Callback to expose coordinator

    // Initializer to allow font and color customization later if needed
    init(text: Binding<String>, font: UIFont? = nil, textColor: UIColor? = nil, onCoordinatorCreated: ((Coordinator) -> Void)? = nil) { // selectedRange Binding REMOVED
        self._text = text
        // self._selectedRange = selectedRange // REMOVED
        if let font = font {
            self.font = font
        }
        if let textColor = textColor {
            self.textColor = textColor
        }
        self.onCoordinatorCreated = onCoordinatorCreated
    }

    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView()
        context.coordinator.textView = textView // Assign the UITextView to the Coordinator
        textView.delegate = context.coordinator
        textView.font = font
        textView.textColor = textColor
        textView.backgroundColor = temporaryBackgroundColor // For development visibility
        textView.isScrollEnabled = true
        textView.isEditable = true
        textView.isUserInteractionEnabled = true
        textView.text = text // Set initial text

        // Expose the coordinator
        DispatchQueue.main.async { // Ensure this runs after the context is fully set up.
            self.onCoordinatorCreated?(context.coordinator)
        }
        return textView
    }

    func updateUIView(_ uiView: UITextView, context: Context) {
        // Update the UITextView's text if the binding changes externally
        // Only update if the content is actually different to avoid cursor jumps
        // and re-triggering delegate methods unnecessarily.
        if uiView.text != self.text {
            // Store current selected range
            let currentSelectedRange = uiView.selectedRange
            uiView.text = self.text
            // Try to restore the selected range if it's still valid
            if currentSelectedRange.location + currentSelectedRange.length <= self.text.count {
                uiView.selectedRange = currentSelectedRange
            }
        }
        // Update selectedRange from the binding if it changes externally - REMOVED
        // if uiView.selectedRange != self.selectedRange {
        //    if self.selectedRange.location + self.selectedRange.length <= uiView.text.count {
        //        uiView.selectedRange = self.selectedRange
        //    }
        // }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, UITextViewDelegate {
        var parent: CustomTextView
        weak var textView: UITextView? // Hold a weak reference to the UITextView
        var internalSelectedRange: NSRange = NSRange(location: 0, length: 0)

        init(_ parent: CustomTextView) {
            self.parent = parent
        }

        func textViewDidChange(_ textView: UITextView) {
            if self.parent.text != textView.text {
                self.parent.text = textView.text
            }
        }

        func textViewDidChangeSelection(_ textView: UITextView) {
            self.internalSelectedRange = textView.selectedRange
        }

        // MARK: - Helper Methods (Callable by parent view if it has a reference to this Coordinator)

        func getCurrentSelectedRange() -> NSRange {
            return internalSelectedRange
        }

        func getSelectedText() -> String? {
            guard let tv = textView, internalSelectedRange.length > 0 else { return nil }
            guard let text = tv.text, let range = Range(internalSelectedRange, in: text) else { return nil }
            return String(text[range])
        }

        func replaceText(inRange range: NSRange, with newText: String) {
            guard let tv = textView else { return }

            // Update the UITextView directly
            if let textRange = Range(range, in: tv.text) {
                tv.text.replaceSubrange(textRange, with: newText)

                // Update the binding
                parent.text = tv.text

                // Update selection to be after the newly inserted text
                let newLocation = range.location + newText.utf16.count
                tv.selectedRange = NSRange(location: newLocation, length: 0)
                internalSelectedRange = tv.selectedRange // also update internal state
            }
        }

        func insertTextAtCurrentCursor(_ textToInsert: String) {
            guard let tv = textView else { return }
            let cursorPosition = internalSelectedRange.location

            if let textRange = Range(NSRange(location: cursorPosition, length: 0), in: tv.text) {
                tv.text.insert(contentsOf: textToInsert, at: textRange.lowerBound)
                parent.text = tv.text // Update binding

                let newLocation = cursorPosition + textToInsert.utf16.count
                tv.selectedRange = NSRange(location: newLocation, length: 0)
                internalSelectedRange = tv.selectedRange
            }
        }
    }
}

// Extension to provide the helper methods more directly (conceptual for now)
// This requires a way to get the underlying UITextView instance.
// A common way is to pass a callback from makeUIView or use a library like Introspect.
// For now, we'll assume the parent view will manage changes through the @Binding text.
// Programmatic text replacement would typically involve modifying the `text` binding.
// Getting selected text would involve reading the `selectedRange` binding and slicing `text`.

// Extension for helper methods related to selectedRange REMOVED as selectedRange binding is removed.
// Parent view will need another mechanism if it needs to trigger selection-based operations
// without direct access to the UITextView instance or its coordinator's internal state.

#if DEBUG
struct CustomTextView_Previews: View {
    @State private var text: String = "Hello, Custom Text View!\nThis is a second line.\nAnd a third."
    // @State private var selectedRange: NSRange = NSRange(location: 0, length: 0) // REMOVED
    // @State private var selectedTextPreview: String = "" // REMOVED

    var body: some View {
        VStack {
            Text("Custom Text View Demo")
                .font(.headline)
            // CustomTextView(text: $text, selectedRange: $selectedRange) // MODIFIED
            CustomTextView(text: $text)
                .frame(height: 200)
                .border(Color.gray)

            Text("SwiftUI Text Binding: \(text)")
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.gray.opacity(0.1))

            // Text("Selected Range: Location \(selectedRange.location), Length \(selectedRange.length)") // REMOVED
            // Button("Get Selected Text") { // REMOVED
            //     if selectedRange.length > 0, let range = Range(selectedRange, in: text) {
            //         selectedTextPreview = String(text[range])
            //     } else {
            //         selectedTextPreview = "None"
            //     }
            // }
            // Text("Preview of Selected: \(selectedTextPreview)") // REMOVED

            Button("Replace 'Text' with 'UITextView' in Binding") {
                 if let rangeToReplace = text.range(of: "Text") {
                    // To programmatically replace, we modify the text binding
                    text.replaceSubrange(rangeToReplace, with: "UITextView")
                    // selectedRange update is removed as binding is removed
                 }
            }
            // Button("Set Selection (Line 2)") { // REMOVED
            //    if let rangeOfSecondLine = text.range(of: "This is a second line.") {
            //        selectedRange = NSRange(rangeOfSecondLine, in: text)
            //    }
            // }
        }
        .padding()
    }
}

struct CustomTextView_PreviewProvider: PreviewProvider {
    static var previews: some View {
        CustomTextView_Previews()
    }
}
#endif
