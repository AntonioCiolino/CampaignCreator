import SwiftUI
import CampaignCreatorLib // For potential shared models

// If CampaignDetailView.AvailableLLM is not accessible directly,
// it might need to be redefined here or moved to a shared location.
// For this example, we assume it might be passed or made accessible.
// A cleaner approach would be to move AvailableLLM to a more global scope.

struct CampaignLLMSettingsView: View {
    @Binding var selectedLLMId: String // Assumes parent uses .withDefault for non-optional
    @Binding var temperature: Double   // Assumes parent uses .withDefault for non-optional

    // Using the specific nested type from CampaignDetailView.
    // This could be improved by moving AvailableLLM to a shared scope.
    let availableLLMs: [AvailableLLM] // Corrected: Use the global AvailableLLM type

    let currentFont: Font
    let currentTextColor: Color

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
                .font(currentFont)
                .onChange(of: selectedLLMId) {
                    Task { await onLLMSettingsChange() }
                }
                Text("Note: This list is a placeholder. Ideally, available LLMs should be fetched from the server.")
                    .font(.caption2)
                    .foregroundColor(.orange)

                VStack(alignment: .leading) {
                    Text("Temperature: \(String(format: "%.2f", temperature))")
                        .font(currentFont.weight(.medium))
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
        .foregroundColor(currentTextColor)
        .font(currentFont)
        .padding()
    }
}
