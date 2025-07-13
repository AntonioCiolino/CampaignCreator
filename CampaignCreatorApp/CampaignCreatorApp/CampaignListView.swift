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

#Preview {
    let viewModel = CampaignListViewModel()
    viewModel.campaigns = [
        Campaign(id: 1, title: "Campaign 1", concept: nil, initial_user_prompt: nil, homebrewery_toc: nil, display_toc: nil, homebrewery_export: nil, sections: [], owner_id: 1, badge_image_url: nil, thematic_image_url: nil, thematic_image_prompt: nil, selected_llm_id: nil, temperature: nil, theme_primary_color: nil, theme_secondary_color: nil, theme_background_color: nil, theme_text_color: nil, theme_font_family: nil, theme_background_image_url: nil, theme_background_image_opacity: nil, mood_board_image_urls: nil),
        Campaign(id: 2, title: "Campaign 2", concept: nil, initial_user_prompt: nil, homebrewery_toc: nil, display_toc: nil, homebrewery_export: nil, sections: [], owner_id: 1, badge_image_url: nil, thematic_image_url: nil, thematic_image_prompt: nil, selected_llm_id: nil, temperature: nil, theme_primary_color: nil, theme_secondary_color: nil, theme_background_color: nil, theme_text_color: nil, theme_font_family: nil, theme_background_image_url: nil, theme_background_image_opacity: nil, mood_board_image_urls: nil)
    ]
    return CampaignListView()
}