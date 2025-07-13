import SwiftUI
import Kingfisher
import CampaignCreatorLib

struct CampaignDetailView: View {
    @StateObject private var viewModel: CampaignDetailViewModel
    @State private var showingCreateSheet = false

    init(campaign: Campaign) {
        _viewModel = StateObject(wrappedValue: CampaignDetailViewModel(campaign: campaign))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading) {
                        Text(viewModel.campaign.title)
                            .font(.largeTitle)
                    }
                    Spacer()
                    if let badgeURL = viewModel.campaign.badge_image_url, let url = URL(string: badgeURL) {
                        KFImage(url)
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                            .frame(width: 50, height: 50)
                            .clipped()
                            .cornerRadius(4)
                    } else {
                        Image(systemName: "photo")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 50, height: 50)
                            .foregroundColor(.gray)
                    }
                }
                .padding(.bottom, 5)

                if let concept = viewModel.campaign.concept, !concept.isEmpty {
                    SectionBox(title: "Concept") { Text(concept) }
                }

                if let sections = viewModel.campaign.sections, !sections.isEmpty {
                    DisclosureGroup("Sections") {
                        ForEach(sections) { section in
                            VStack(alignment: .leading) {
                                if let title = section.title {
                                    Text(title).font(.headline)
                                }
                                Text(section.content)
                            }
                            .padding(.bottom, 5)
                        }
                    }
                }

                Spacer()
            }
            .padding()
        }
        .navigationTitle(viewModel.campaign.title)
        .navigationBarTitleDisplayMode(.inline)
        .refreshable {
            await viewModel.refreshCampaign()
        }
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                Button("Edit") {
                    showingCreateSheet = true
                }
            }
        }
        .sheet(isPresented: $showingCreateSheet, onDismiss: {
            Task {
                await viewModel.refreshCampaign()
            }
        }) {
            CampaignEditView(campaign: viewModel.campaign, isPresented: $showingCreateSheet, onCampaignUpdated: { updatedCampaign in
                viewModel.campaign = updatedCampaign
            })
        }
    }
}

struct CampaignDetailView_Previews: PreviewProvider {
    static var previews: some View {
        // Create a mock library campaign first
        let libCampaign = CampaignCreatorLib.Campaign(
            id: 1,
            ownerID: 1,
            title: "Campaign 1",
            concept: "A cool campaign",
            initialUserPrompt: "Initial prompt for preview.",
            temperature: 0.7,
            homebreweryTOC: nil,
            displayTOC: nil,
            homebreweryExport: nil,
            sections: [],
            badgeImageURL: nil,
            thematicImageURL: nil,
            thematicImagePrompt: nil,
            selectedLLMId: nil,
            themePrimaryColor: "#FF0000",
            themeSecondaryColor: "#00FF00",
            themeBackgroundColor: "#0000FF",
            themeTextColor: "#FFFFFF",
            themeFontFamily: "Arial",
            themeBackgroundImageURL: nil,
            themeBackgroundImageOpacity: 1.0,
            moodBoardImageURLs: [],
            linkedCharacterIDs: [],
            customSections: []
        )

        // Use the failable initializer to create the app-level campaign
        let sampleCampaign = Campaign(from: libCampaign)!

        return NavigationView {
            CampaignDetailView(campaign: sampleCampaign)
        }
    }
}
