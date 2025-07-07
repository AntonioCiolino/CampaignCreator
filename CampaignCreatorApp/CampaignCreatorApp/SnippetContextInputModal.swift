import SwiftUI
import CampaignCreatorLib // For Feature struct

struct SnippetContextInputModal: View {
    @Binding var isPresented: Bool
    let feature: Feature
    let campaignCharacters: [Character] // Using Character model from CampaignCreatorLib
    let selectedText: String
    let onSubmit: (([String: String]) -> Void) // Returns dictionary of contextKey: value

    @State private var contextData: [String: String] = [:]
    @State private var formIsValid: Bool = false // To enable/disable submit button

    // Determine required context fields excluding 'selected_text' and 'campaign_characters'
    private var requiredInputFields: [String] {
        feature.requiredContext?.filter { $0 != "selected_text" && $0 != "campaign_characters" } ?? []
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Provide Additional Context for '\(feature.name)'").font(.headline)) {
                    Text("Selected Text: \"\(selectedText.prefix(100))\(selectedText.count > 100 ? "..." : "")\"")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.bottom)

                    if feature.requiredContext?.contains("campaign_characters") == true {
                        if campaignCharacters.isEmpty {
                            Text("This feature can use campaign characters, but no characters are currently in this campaign.")
                                .font(.caption)
                                .foregroundColor(.orange)
                        } else {
                            // Non-interactive display or simple selection if needed later.
                            // For now, just acknowledging it's a context.
                            // If actual selection is needed, this would be a Picker or MultiSelector.
                            Text("Context: Uses existing campaign characters (\(campaignCharacters.map { $0.name }.joined(separator: ", ")))")
                                .font(.caption)
                        }
                    }

                    if requiredInputFields.isEmpty {
                        Text("No additional context required for this feature beyond the selected text and any automatic context (like characters).")
                            .font(.callout)
                    } else {
                        ForEach(requiredInputFields, id: \.self) { key in
                            VStack(alignment: .leading) {
                                Text(key.replacingOccurrences(of: "_", with: " ").capitalized + ":") // User-friendly label
                                TextField("Enter \(key.replacingOccurrences(of: "_", with: " "))", text: bindingFor(key: key))
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                            }
                        }
                    }
                }

                Section {
                    Button("Submit Context & Generate") {
                        onSubmit(contextData)
                        isPresented = false
                    }
                    .disabled(!formIsValid && !requiredInputFields.isEmpty) // Disable if form isn't valid and there are fields

                    Button("Cancel") {
                        isPresented = false
                    }
                    .foregroundColor(.red)
                }
            }
            .navigationTitle("Feature Context")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { isPresented = false }
                }
            }
            .onAppear(perform: initializeContextDataAndValidation)
            .onChange(of: contextData) { _ in
                validateForm()
            }
        }
    }

    private func bindingFor(key: String) -> Binding<String> {
        return Binding<String>(
            get: { contextData[key] ?? "" },
            set: { contextData[key] = $0 }
        )
    }

    private func initializeContextDataAndValidation() {
        var initialData: [String: String] = [:]
        for key in requiredInputFields {
            initialData[key] = "" // Initialize with empty strings
        }
        self.contextData = initialData
        validateForm() // Perform initial validation
    }

    private func validateForm() {
        if requiredInputFields.isEmpty {
            formIsValid = true // No fields to validate
            return
        }
        // Check if all required fields (that need input) have non-empty values
        formIsValid = requiredInputFields.allSatisfy { key in
            !(contextData[key]?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ?? true)
        }
    }
}

struct SnippetContextInputModal_Previews: PreviewProvider {
    static let sampleFeatureWithContext = Feature(
        id: 1,
        name: "Describe Mood",
        template: "Describe the mood of the selected text: {selected_text}. Consider the current weather: {weather} and time of day: {time_of_day}.",
        requiredContext: ["selected_text", "weather", "time_of_day", "campaign_characters"]
    )
    static let sampleFeatureNoExtraContext = Feature(
        id: 2,
        name: "Summarize",
        template: "Summarize: {selected_text}",
        requiredContext: ["selected_text"]
    )
    static let sampleCharacters = [
        Character(id: 1, name: "Aella", modifiedAt: Date()),
        Character(id: 2, name: "Bram", modifiedAt: Date())
    ]

    static var previews: some View {
        // Preview 1: Feature requiring extra context
        StatefulPreviewWrapper(isPresented: true, feature: sampleFeatureWithContext)

        // Preview 2: Feature requiring no extra context (beyond selected_text)
        StatefulPreviewWrapper(isPresented: true, feature: sampleFeatureNoExtraContext)
    }

    // Helper for @State in previews
    struct StatefulPreviewWrapper: View {
        @State var isPresented: Bool
        let feature: Feature

        var body: some View {
            Text("Tap to show modal for \(feature.name)")
                .onTapGesture { isPresented = true }
                .sheet(isPresented: $isPresented) {
                    SnippetContextInputModal(
                        isPresented: $isPresented,
                        feature: feature,
                        campaignCharacters: SnippetContextInputModal_Previews.sampleCharacters,
                        selectedText: "The old house stood on a windswept hill, its windows like vacant eyes.",
                        onSubmit: { data in
                            print("Modal submitted for \(feature.name) with context: \(data)")
                        }
                    )
                }
        }
    }
}
