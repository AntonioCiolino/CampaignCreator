import SwiftUI
import CampaignCreatorLib

struct CharacterLLMSettingsView: View {
    @Binding var selectedLLMId: String
    @Binding var temperature: Double

    let availableLLMs: [AvailableLLM]

    let onLLMSettingsChange: () async -> Void

    var body: some View {
        DisclosureGroup("LLM Settings") {
            VStack(alignment: .leading, spacing: 12) {
                Picker("Selected LLM", selection: $selectedLLMId) {
                    ForEach(availableLLMs) { llm in
                        Text(llm.name).tag(llm.id)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                .onChange(of: selectedLLMId) {
                    Task { await onLLMSettingsChange() }
                }
                Text("Note: This list is a placeholder. Ideally, available LLMs should be fetched from the server.")
                    .font(.caption2)
                    .foregroundColor(.orange)

                VStack(alignment: .leading) {
                    Text("Temperature: \(String(format: "%.2f", temperature))")
                        .fontWeight(.medium)
                    Slider(value: $temperature, in: 0.0...1.0, step: 0.05) {
                        Text("Temperature") // Accessibility label
                    } onEditingChanged: { editing in
                        if !editing { // Trigger save when the user releases the slider
                            Task { await onLLMSettingsChange() }
                        }
                    }
                }

                Text("Lower temperature (e.g., 0.2) means more focused output. Higher (e.g., 0.8 for more creative output, max 1.0).")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 4)
        }
        .padding()
    }
}
