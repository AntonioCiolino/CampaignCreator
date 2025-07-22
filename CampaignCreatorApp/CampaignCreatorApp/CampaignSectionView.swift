import SwiftUI
import SwiftData

struct CampaignSectionView: View {
    @StateObject var viewModel: CampaignSectionViewModel
    @State private var showingDeleteConfirmation = false
    @State private var showingEditor = false
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // TODO: Add character linking UI here
            if let title = viewModel.section.title {
                Text(title)
                    .font(.title)
                    .fontWeight(.bold)
            }

            ScrollView {
                Text(viewModel.section.content)
                    .font(.body)
            }

            HStack {
                Button("Edit") {
                    showingEditor = true
                }
                Button("Delete") {
                    showingDeleteConfirmation = true
                }
                .alert("Delete Section", isPresented: $showingDeleteConfirmation) {
                    Button("Delete", role: .destructive) {
                        viewModel.delete()
                    }
                    Button("Cancel", role: .cancel) { }
                } message: {
                    Text("Are you sure you want to delete this section? This action cannot be undone.")
                }
            }
            .sheet(isPresented: $showingEditor) {
                CampaignSectionEditorView(viewModel: viewModel, isPresented: $showingEditor)
            }
        }
        .padding()
    }
}
