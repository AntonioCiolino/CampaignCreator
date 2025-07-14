import SwiftUI

extension SnippetContextInputModal {
    struct HeaderView: View {
        let featureName: String
        let selectedText: String

        var body: some View {
            Section(header: Text("Provide Additional Context for '\(featureName)'").font(.headline)) {
                Text("Selected Text: \"\(selectedText.prefix(100))\(selectedText.count > 100 ? "..." : "")\"")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.bottom)
            }
        }
    }

    struct CharacterContextView: View {
        let campaignCharacters: [Character]

        var body: some View {
            if campaignCharacters.isEmpty {
                Text("This feature can use campaign characters, but no characters are currently in this campaign.")
                    .font(.caption)
                    .foregroundColor(.orange)
            } else {
                Text("Context: Uses existing campaign characters (\(campaignCharacters.map { $0.name }.joined(separator: ", ")))")
                    .font(.caption)
            }
        }
    }

    struct InputFieldsView: View {
        let requiredInputFields: [String]
        @Binding var contextData: [String: String]

        var body: some View {
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

        private func bindingFor(key: String) -> Binding<String> {
            return Binding<String>(
                get: { contextData[key] ?? "" },
                set: { contextData[key] = $0 }
            )
        }
    }

    struct SubmitButtonView: View {
        let formIsValid: Bool
        let requiredInputFields: [String]
        let onSubmit: () -> Void

        var body: some View {
            Button("Submit Context & Generate") {
                onSubmit()
            }
            .disabled(!formIsValid && !requiredInputFields.isEmpty)
        }
    }
}
