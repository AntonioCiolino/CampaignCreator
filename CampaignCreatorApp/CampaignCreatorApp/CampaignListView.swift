import SwiftUI
import Kingfisher
import SwiftData
import CampaignCreatorLib

struct CampaignListView: View {
    @Environment(\.modelContext) private var modelContext
    @EnvironmentObject var contentViewModel: ContentViewModel
    @Query(sort: \CampaignModel.title) private var campaigns: [CampaignModel]
    @State private var showingCreateSheet = false
    @State private var showingErrorAlert = false
    @State private var errorMessage = ""
    @State private var isLoading = false
    @State private var showingDeleteConfirmation = false
    @State private var campaignToDelete: CampaignModel?

    private let apiService = CampaignCreatorLib.APIService()

    var body: some View {
        NavigationView {
            Group {
                if isLoading {
                    ProgressView()
                } else if campaigns.isEmpty {
                    Text("No campaigns yet. Tap '+' to create one.")
                        .foregroundColor(.secondary)
                        .font(.title2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(campaigns) { campaign in
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
                        await refreshCampaigns()
                    }
                    .alert("Delete Campaign", isPresented: $showingDeleteConfirmation) {
                        Button("Delete", role: .destructive) {
                            if let campaignToDelete = self.campaignToDelete {
                                deleteCampaign(campaignToDelete)
                            }
                        }
                        Button("Cancel", role: .cancel) { }
                    } message: {
                        Text("Are you sure you want to delete this campaign? This action cannot be undone.")
                    }
                }
            }
            .navigationTitle("Campaigns")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingCreateSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet) {
                if let user = contentViewModel.currentUser {
                    CampaignCreateView(isPresented: $showingCreateSheet, ownerId: user.id)
                        .environmentObject(contentViewModel)
                        .environment(\.modelContext, modelContext)
                }
            }
            .alert("Error", isPresented: $showingErrorAlert) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .onAppear {
                Task {
                    await refreshCampaigns()
                }
            }
        }
    }

    private func deleteCampaigns(offsets: IndexSet) {
        for index in offsets {
            let campaignToDelete = campaigns[index]
            self.campaignToDelete = campaignToDelete
            showingDeleteConfirmation = true
        }
    }

    private func deleteCampaign(_ campaign: CampaignModel) {
        withAnimation {
            modelContext.delete(campaign)
            do {
                try modelContext.save()
            } catch {
                errorMessage = "Failed to delete campaign: \(error.localizedDescription)"
                showingErrorAlert = true
            }
        }
    }

    @EnvironmentObject var networkMonitor: NetworkMonitor

    private func refreshCampaigns() async {
        isLoading = true
        defer { isLoading = false }

        if networkMonitor.isConnected {
            await syncDirtyCampaigns()
        }

        do {
            let fetchedCampaigns = try await apiService.fetchCampaigns()

            // Clear out existing campaigns to avoid duplicates
            for campaign in campaigns {
                modelContext.delete(campaign)
            }

            // Insert or update campaigns
            for campaign in fetchedCampaigns {
                if let existingCampaign = campaigns.first(where: { $0.id == campaign.id }) {
                    existingCampaign.title = campaign.title
                    existingCampaign.concept = campaign.concept
                    existingCampaign.initial_user_prompt = campaign.initialUserPrompt
                    existingCampaign.badge_image_url = campaign.badgeImageURL
                    existingCampaign.thematic_image_url = campaign.thematicImageURL
                    existingCampaign.thematic_image_prompt = campaign.thematicImagePrompt
                    existingCampaign.selected_llm_id = campaign.selectedLLMId
                    existingCampaign.temperature = campaign.temperature
                    existingCampaign.theme_primary_color = campaign.themePrimaryColor
                    existingCampaign.theme_secondary_color = campaign.themeSecondaryColor
                    existingCampaign.theme_background_color = campaign.themeBackgroundColor
                    existingCampaign.theme_text_color = campaign.themeTextColor
                    existingCampaign.theme_font_family = campaign.themeFontFamily
                    existingCampaign.theme_background_image_url = campaign.themeBackgroundImageURL
                    existingCampaign.theme_background_image_opacity = campaign.themeBackgroundImageOpacity
                    existingCampaign.mood_board_image_urls = campaign.moodBoardImageURLs
                    existingCampaign.sections = campaign.sections.map { CampaignSection(id: $0.id, campaign_id: $0.campaign_id ?? 0, title: $0.title, content: $0.content, order: $0.order, type: $0.type) }
                } else {
                    let campaignModel = CampaignModel.from(campaign: campaign)
                    modelContext.insert(campaignModel)
                }
            }

            try modelContext.save()
        } catch {
            errorMessage = "Failed to refresh campaigns: \(error.localizedDescription)"
            showingErrorAlert = true
        }
    }

    private func syncDirtyCampaigns() async {
        let dirtyCampaigns = campaigns.filter { $0.needsSync }
        for campaign in dirtyCampaigns {
            do {
                let campaignUpdate = CampaignUpdate(
                    title: campaign.title,
                    initial_user_prompt: campaign.initial_user_prompt,
                    concept: campaign.concept,
                    badge_image_url: campaign.badge_image_url,
                    thematic_image_url: campaign.thematic_image_url,
                    thematic_image_prompt: campaign.thematic_image_prompt,
                    selected_llm_id: campaign.selected_llm_id,
                    temperature: Float(campaign.temperature ?? 0.7),
                    theme_primary_color: campaign.theme_primary_color,
                    theme_secondary_color: campaign.theme_secondary_color,
                    theme_background_color: campaign.theme_background_color,
                    theme_text_color: campaign.theme_text_color,
                    theme_font_family: campaign.theme_font_family,
                    theme_background_image_url: campaign.theme_background_image_url,
                    theme_background_image_opacity: Float(campaign.theme_background_image_opacity ?? 1.0),
                    mood_board_image_urls: campaign.mood_board_image_urls
                )
                let body = try JSONEncoder().encode(campaignUpdate)
                let _: CampaignCreatorLib.Campaign = try await apiService.performRequest(endpoint: "/campaigns/\(campaign.id)", method: "PUT", body: body)
                campaign.needsSync = false
                try modelContext.save()
            } catch {
                print("Failed to sync campaign \(campaign.id): \(error.localizedDescription)")
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
