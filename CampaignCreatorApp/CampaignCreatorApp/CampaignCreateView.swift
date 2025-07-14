import SwiftUI
import SwiftData

struct CampaignCreateView: View {
    @Environment(\.modelContext) private var modelContext
    @Binding var isPresented: Bool
    var ownerId: Int

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
        print("Attempting to save campaign with title: \(title) and owner_id: \(ownerId)")
        let newCampaign = Campaign(title: title, concept: concept, owner_id: ownerId)
        modelContext.insert(newCampaign)

        do {
            try modelContext.save()
            print("Successfully saved model context from saveCampaign.")
        } catch {
            print("Error saving model context from saveCampaign: \(error.localizedDescription)")
        }
    }
}
