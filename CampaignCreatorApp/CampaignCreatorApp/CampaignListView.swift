import SwiftUI
import Kingfisher

struct CampaignListView: View {
    @StateObject private var viewModel = CampaignListViewModel()
    @State private var showingCreateSheet = false

    var body: some View {
        NavigationView {
            Group {
                if viewModel.isLoading && viewModel.campaigns.isEmpty {
                    ProgressView("Loading Campaigns...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let error = viewModel.errorMessage {
                    VStack {
                        Text("Error Loading Campaigns")
                            .font(.headline)
                        Text(error)
                            .font(.caption)
                            .multilineTextAlignment(.center)
                        Button("Retry") {
                            Task {
                                await viewModel.fetchCampaigns()
                            }
                        }
                        .padding(.top)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if viewModel.campaigns.isEmpty {
                    Text("No campaigns yet. Tap '+' to create one.")
                        .foregroundColor(.secondary)
                        .font(.title2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(viewModel.campaigns) { campaign in
                            NavigationLink(destination: CampaignDetailView(campaign: campaign)) {
                                HStack {
                                    if let badgeURL = campaign.badge_image_url, let url = URL(string: badgeURL) {
                                        KFImage(url)
                                            .resizable()
                                            .aspectRatio(contentMode: .fill)
                                            .frame(width: 40, height: 40)
                                            .clipped()
                                            .cornerRadius(4)
                                    } else {
                                        Image(systemName: "photo")
                                            .resizable()
                                            .aspectRatio(contentMode: .fit)
                                            .frame(width: 40, height: 40)
                                            .foregroundColor(.gray)
                                    }
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(campaign.title)
                                            .font(.headline)
                                            .foregroundColor(.primary)
                                    }
                                }
                                .padding(.vertical, 2)
                            }
                        }
                        .onDelete(perform: deleteCampaigns)
                    }
                    .refreshable {
                        await viewModel.fetchCampaigns()
                    }
                }
            }
            .navigationTitle("Campaigns")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if viewModel.isLoading && !viewModel.campaigns.isEmpty {
                        ProgressView()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingCreateSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet, onDismiss: {
                Task {
                    await viewModel.fetchCampaigns()
                }
            }) {
                CampaignCreateView(isPresented: $showingCreateSheet)
            }
            .onAppear {
                Task {
                    await viewModel.fetchCampaigns()
                }
            }
        }
    }

    private func deleteCampaigns(offsets: IndexSet) {
        let campaignsToDelete = offsets.map { viewModel.campaigns[$0] }
        Task {
            for campaign in campaignsToDelete {
                await viewModel.deleteCampaign(campaign)
            }
        }
    }
}

//#if DEBUG
//extension Campaign {
//    static func mock(
//        id: Int,
//        title: String,
//        concept: String? = "A mock concept",
//        initial_user_prompt: String? = "A mock prompt",
//        homebrewery_toc: [String: String]? = nil,
//        display_toc: [String: String]? = nil,
//        homebrewery_export: String? = nil,
//        sections: [CampaignSection]? = [],
//        owner_id: Int = 1,
//        badge_image_url: String? = "https://picsum.photos/seed/campaign/100/100",
//        thematic_image_url: String? = "https://picsum.photos/seed/campaign/800/600",
//        thematic_image_prompt: String? = "A mock thematic prompt",
//        selected_llm_id: String? = "mock_llm",
//        temperature: Float? = 0.7,
//        theme_primary_color: String? = "#3498db",
//        theme_secondary_color: String? = "#2ecc71",
//        theme_background_color: String? = "#ecf0f1",
//        theme_text_color: String? = "#2c3e50",
//        theme_font_family: String? = "Helvetica",
//        theme_background_image_url: String? = nil,
//        theme_background_image_opacity: Float? = 1.0,
//        mood_board_image_urls: [String]? = []
//    ) -> Campaign {
//        return Campaign(
//            id: id,
//            title: title,
//            concept: concept,
//            initial_user_prompt: initial_user_prompt,
//            homebrewery_toc: homebrewery_toc,
//            display_toc: display_toc,
//            homebrewery_export: homebrewery_export,
//            sections: sections,
//            owner_id: owner_id,
//            badge_image_url: badge_image_url,
//            thematic_image_url: thematic_image_url,
//            thematic_image_prompt: thematic_image_prompt,
//            selected_llm_id: selected_llm_id,
//            temperature: temperature,
//            theme_primary_color: theme_primary_color,
//            theme_secondary_color: theme_secondary_color,
//            theme_background_color: theme_background_color,
//            theme_text_color: theme_text_color,
//            theme_font_family: theme_font_family,
//            theme_background_image_url: theme_background_image_url,
//            theme_background_image_opacity: theme_background_image_opacity,
//            mood_board_image_urls: mood_board_image_urls
//        )
//    }
//}
//
//
//#Preview {
//    let viewModel = CampaignListViewModel()
//    viewModel.campaigns = [
//        Campaign.mock(id: 1, title: "Voyage of the Starseeker"),
//        Campaign.mock(id: 2, title: "The Sunken City of Aeridor"),
//        Campaign.mock(id: 3, title: "Chronicles of the Iron Empire")
//    ]
//
//    return CampaignListView()
//}
//#endif