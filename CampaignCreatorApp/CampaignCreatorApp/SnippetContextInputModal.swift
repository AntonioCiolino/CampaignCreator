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
                HeaderView(featureName: feature.name, selectedText: selectedText)

                if feature.required_context?.contains("campaign_characters") == true {
                    CharacterContextView(campaignCharacters: campaignCharacters)
                }

                InputFieldsView(requiredInputFields: requiredInputFields, contextData: $contextData)

                Section {
                    SubmitButtonView(formIsValid: formIsValid, requiredInputFields: requiredInputFields) {
                        onSubmit(contextData)
                        isPresented = false
                    }

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
            .onChange(of: contextData) {
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
        compatible_types: [],
        feature_category: ""
    )
    static let sampleFeatureNoExtraContext = Feature(
        id: 2,
        name: "Summarize",
        template: "Summarize: {selected_text}",
        user_id: 1,
        required_context: ["selected_text"],
        compatible_types: [],
        feature_category: ""
    )
    static let sampleCharacters: [Character] = []

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
