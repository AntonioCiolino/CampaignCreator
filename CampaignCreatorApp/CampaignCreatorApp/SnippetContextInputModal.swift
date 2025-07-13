import SwiftUI

struct SnippetContextInputModal: View {
    @Binding var isPresented: Bool
    let feature: Feature
    let campaignCharacters: [Character]
    let selectedText: String
    let onSubmit: (([String: String]) -> Void)

    @State private var contextData: [String: String] = [:]
    @State private var formIsValid: Bool = false

    private var requiredInputFields: [String] {
        feature.required_context?.filter { $0 != "selected_text" && $0 != "campaign_characters" } ?? []
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Provide Additional Context for '\(feature.name)'").font(.headline)) {
                    Text("Selected Text: \"\(selectedText.prefix(100))\(selectedText.count > 100 ? "..." : "")\"")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.bottom)

                    if feature.required_context?.contains("campaign_characters") == true {
                        if campaignCharacters.isEmpty {
                            Text("This feature can use campaign characters, but no characters are currently in this campaign.")
                                .font(.caption)
                                .foregroundColor(.orange)
                        } else {
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
                                Text(key.replacingOccurrences(of: "_", with: " ").capitalized + ":")
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
                    .disabled(!formIsValid && !requiredInputFields.isEmpty)

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
            initialData[key] = ""
        }
        self.contextData = initialData
        validateForm()
    }

    private func validateForm() {
        if requiredInputFields.isEmpty {
            formIsValid = true
            return
        }
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
        user_id: 1,
        required_context: ["selected_text", "weather", "time_of_day", "campaign_characters"],
        compatible_types: nil,
        feature_category: nil
    )
    static let sampleFeatureNoExtraContext = Feature(
        id: 2,
        name: "Summarize",
        template: "Summarize: {selected_text}",
        user_id: 1,
        required_context: ["selected_text"],
        compatible_types: nil,
        feature_category: nil
    )
    static let sampleCharacters = [
        Character(id: 1, owner_id: 1, name: "Aella", description: "A fierce warrior", appearance_description: "Tall and imposing", image_urls: [], video_clip_urls: [], notes_for_llm: "Loves to fight", stats: CharacterStats(strength: 18, dexterity: 14, constitution: 16, intelligence: 10, wisdom: 12, charisma: 8), export_format_preference: "Complex"),
        Character(id: 2, owner_id: 1, name: "Bram", description: "A wise wizard", appearance_description: "Short and frail", image_urls: [], video_clip_urls: [], notes_for_llm: "Loves to read", stats: CharacterStats(strength: 8, dexterity: 12, constitution: 10, intelligence: 18, wisdom: 16, charisma: 14), export_format_preference: "Complex")
    ]

    static var previews: some View {
        StatefulPreviewWrapper(isPresented: true, feature: sampleFeatureWithContext)
        StatefulPreviewWrapper(isPresented: true, feature: sampleFeatureNoExtraContext)
    }

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
