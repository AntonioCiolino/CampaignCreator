import SwiftUI
import Kingfisher
import SwiftData

struct CampaignDetailView: View {
    @StateObject private var viewModel: CampaignDetailViewModel
    @Environment(\.modelContext) private var modelContext

    init(campaign: Campaign) {
        _viewModel = StateObject(wrappedValue: CampaignDetailViewModel(campaign: campaign))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // your UI...
            }
            .padding()
            .onAppear {
                viewModel.setModelContext(modelContext)
            }
        }
        .navigationTitle(viewModel.campaign.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                Button("Edit") {
                    // ...
                }
            }
        }
    }
}
