import SwiftUI
import Kingfisher
import SwiftData

struct CampaignDetailView: View {
    let campaign: CampaignModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                CampaignHeaderView(campaign: campaign, editableTitle: .constant(campaign.title), isSaving: false, isGeneratingText: false, currentPrimaryColor: .blue, onSetBadgeAction: {})

                if let concept = campaign.concept, !concept.isEmpty {
                    SectionBox(title: "Concept") {
                        Text(concept)
                    }
                }

                // Add more sections as needed

            }
            .padding()
        }
        .navigationTitle(campaign.title)
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
