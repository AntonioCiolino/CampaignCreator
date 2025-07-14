import SwiftUI
import SwiftData

struct CampaignCreateView: View {
    @Environment(\.modelContext) private var modelContext
    @Binding var isPresented: Bool

    @State private var title = ""
    @State private var concept = ""

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Campaign Details")) {
                    TextField("Title", text: $title)
                    TextField("Concept", text: $concept)
                }
            }
            .navigationTitle("New Campaign")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        isPresented = false
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        saveCampaign()
                        isPresented = false
                    }
                    .disabled(title.isEmpty)
                }
            }
        }
    }

    private func saveCampaign() {
        let newCampaign = Campaign(
            id: Int.random(in: 1...1000),
            title: title,
            concept: concept,
            initial_user_prompt: nil,
            sections: [],
            owner_id: 0,
            badge_image_url: nil,
            thematic_image_url: nil,
            thematic_image_prompt: nil,
            selected_llm_id: nil,
            temperature: nil,
            theme_primary_color: nil,
            theme_secondary_color: nil,
            theme_background_color: nil,
            theme_text_color: nil,
            theme_font_family: nil,
            theme_background_image_url: nil,
            theme_background_image_opacity: nil,
            mood_board_image_urls: nil
        )
        modelContext.insert(newCampaign)
    }
}
