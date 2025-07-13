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
        let libCampaign = CampaignCreatorLib.Campaign(id: 1)
        let sampleCampaign = Campaign(from: libCampaign)

        return NavigationView {
            CampaignDetailView(campaign: sampleCampaign)
        }
    }
}
