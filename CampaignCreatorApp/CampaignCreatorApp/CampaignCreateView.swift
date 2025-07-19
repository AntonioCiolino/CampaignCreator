import SwiftUI
import SwiftData

struct CampaignCreateView: View {
    @Environment(\.modelContext) private var modelContext
    @Binding var isPresented: Bool
    var ownerId: Int

    @State private var title = ""
    @State private var concept = ""

    init(isPresented: Binding<Bool>, ownerId: Int) {
        _isPresented = isPresented
        self.ownerId = ownerId
        print("CampaignCreateView init")
    }

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Section(header: Text("Campaign Details")) {
                        TextField("Title", text: $title)
                        TextField("Concept", text: $concept)
                    }
                }
                .padding()
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
        let newCampaign = CampaignModel(id: 0, title: title, concept: concept, owner_id: ownerId)
        modelContext.insert(newCampaign)

        do {
            try modelContext.save()
            print("Successfully saved model context from saveCampaign.")
        } catch {
            print("Error saving model context from saveCampaign: \(error.localizedDescription)")
        }
    }
}
