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
        print("Saving campaign...")
        let newCampaign = Campaign(title: title, concept: concept, owner_id: 0)
        modelContext.insert(newCampaign)
        PersistenceController.shared.save()
        print("Campaign saved successfully.")
    }
}
