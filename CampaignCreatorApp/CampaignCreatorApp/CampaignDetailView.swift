import SwiftUI
import Kingfisher
import SwiftData

struct CampaignDetailView: View {
    @Bindable var campaign: CampaignModel

    @State private var showingEditSheet = false
    @State private var isEditingConcept = false
    @State private var editableConcept = ""
    @State private var selectedLLMId = ""
    @State private var temperature = 0.7
    @StateObject private var themeManager = CampaignThemeManager()
    @StateObject private var llmService = LLMService()
    @State private var showingSetBadgeSheet = false
    @State private var showingErrorAlert = false
    @State private var errorMessage = ""

    @Environment(\.modelContext) private var modelContext

    var body: some View {
        ScrollView {
            ZStack {
                // Background color from theme
                themeManager.backgroundColor.edgesIgnoringSafeArea(.all)

                // Background image from theme
                if let bgURL = themeManager.backgroundImageUrl {
                    KFImage(bgURL)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .edgesIgnoringSafeArea(.all)
                        .opacity(themeManager.backgroundImageOpacity)
                }

                VStack(alignment: .leading, spacing: 16) {
                    CampaignHeaderView(campaign: campaign, editableTitle: .constant(campaign.title), isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor)

                    CampaignConceptEditorView(isEditingConcept: $isEditingConcept, editableConcept: $editableConcept, isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor, currentFont: themeManager.bodyFont, currentTextColor: themeManager.textColor, onSaveChanges: {
                        campaign.concept = editableConcept
                    })

                    CollapsibleSectionView(title: "Table of Contents") {
                        Text("Not yet implemented.")
                            .foregroundColor(themeManager.textColor)
                    }

                    CollapsibleSectionView(title: "Campaign Sections") {
                        Text("Not yet implemented.")
                            .foregroundColor(themeManager.textColor)
                    }


                    CampaignLLMSettingsView(selectedLLMId: $selectedLLMId, temperature: $temperature, availableLLMs: llmService.availableLLMs, currentFont: themeManager.bodyFont, currentTextColor: themeManager.textColor, onLLMSettingsChange: {
                        campaign.selected_llm_id = selectedLLMId
                        campaign.temperature = temperature
                    })

                    CampaignMoodboardView(campaign: campaign, onSetBadgeAction: {
                        showingSetBadgeSheet = true
                    })

                }
                .padding()
            }
        }
        .onDisappear(perform: {
            if campaign.hasChanges {
                campaign.needsSync = true
                try? modelContext.save()
            }
        })
        .navigationTitle(campaign.title)
        .navigationBarTitleDisplayMode(.inline)
        .background(themeManager.backgroundColor)
        .navigationBarColor(backgroundColor: themeManager.primaryColor,
                              tintColor: themeManager.textColor,
                              titleColor: themeManager.textColor)
        .refreshable {
            await refreshCampaign()
        }
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                Button("Edit") {
                    showingEditSheet = true
                }
                .foregroundColor(themeManager.textColor)
            }
        }
        .sheet(isPresented: $showingEditSheet) {
            CampaignEditView(campaign: campaign, isPresented: $showingEditSheet)
        }
        .sheet(isPresented: $showingSetBadgeSheet) {
            SelectBadgeFromMoodboardView(
                moodBoardImageURLs: campaign.mood_board_image_urls ?? [],
                thematicImageURL: campaign.thematic_image_url,
                onImageSelected: { selectedURL in
                    campaign.badge_image_url = selectedURL
                },
                apiService: llmService.apiService
            )
        }
        .onAppear {
            themeManager.updateTheme(from: campaign)
            editableConcept = campaign.concept ?? ""
            selectedLLMId = campaign.selected_llm_id ?? ""
            temperature = campaign.temperature ?? 0.7
            Task {
                do {
                    try await llmService.fetchAvailableLLMs()
                } catch {
                    errorMessage = error.localizedDescription
                    showingErrorAlert = true
                }
            }
        }
        .alert("Error", isPresented: $showingErrorAlert) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .onDisappear {
            themeManager.resetTheme()
        }
    }

    private func refreshCampaign() async {
        do {
            let refreshedCampaign = try await llmService.apiService.fetchCampaign(id: campaign.id)
            campaign.title = refreshedCampaign.title
            campaign.concept = refreshedCampaign.concept
            campaign.initial_user_prompt = refreshedCampaign.initialUserPrompt
            campaign.badge_image_url = refreshedCampaign.badgeImageURL
            campaign.thematic_image_url = refreshedCampaign.thematicImageURL
            campaign.thematic_image_prompt = refreshedCampaign.thematicImagePrompt
            campaign.selected_llm_id = refreshedCampaign.selectedLLMId
            campaign.temperature = refreshedCampaign.temperature
            campaign.theme_primary_color = refreshedCampaign.themePrimaryColor
            campaign.theme_secondary_color = refreshedCampaign.themeSecondaryColor
            campaign.theme_background_color = refreshedCampaign.themeBackgroundColor
            campaign.theme_text_color = refreshedCampaign.themeTextColor
            campaign.theme_font_family = refreshedCampaign.themeFontFamily
            campaign.theme_background_image_url = refreshedCampaign.themeBackgroundImageURL
            campaign.theme_background_image_opacity = refreshedCampaign.themeBackgroundImageOpacity
            campaign.mood_board_image_urls = refreshedCampaign.moodBoardImageURLs
        } catch {
            errorMessage = "Failed to refresh campaign: \(error.localizedDescription)"
            showingErrorAlert = true
        }
    }
}
