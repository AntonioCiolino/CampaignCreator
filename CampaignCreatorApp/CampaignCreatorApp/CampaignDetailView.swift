import SwiftUI
import Kingfisher
import SwiftData

struct CampaignDetailView: View {
    let campaign: CampaignModel

    @State private var showingEditSheet = false
    @State private var selectedLLMId = ""
    @State private var temperature = 0.7
    @StateObject private var themeManager = CampaignThemeManager()
    @StateObject private var viewModel = CampaignDetailViewModel()
    @State private var showingSetBadgeSheet = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                CampaignHeaderView(campaign: campaign, editableTitle: .constant(campaign.title), isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor, onSetBadgeAction: {
                    showingSetBadgeSheet = true
                })

                SectionBox(title: "Campaign Concept") {
                    TextEditor(text: .init(get: { campaign.concept ?? "" }, set: { campaign.concept = $0 }))
                        .frame(height: 150)
                        .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                }

                SectionBox(title: "Table of Contents") {
                    // TOC items
                }

                SectionBox(title: "Campaign Sections") {
                    // Campaign sections
                }

                SectionBox(title: "Character Linking") {
                    // Character linking
                }

                CampaignLLMSettingsView(selectedLLMId: $selectedLLMId, temperature: $temperature, availableLLMs: viewModel.availableLLMs, currentFont: themeManager.bodyFont, currentTextColor: themeManager.textColor, onLLMSettingsChange: {
                    campaign.selected_llm_id = selectedLLMId
                    campaign.temperature = Float(temperature)
                }, onRefresh: {
                    Task {
                        await viewModel.fetchAvailableLLMs()
                    }
                })

                CampaignMoodboardView(campaign: campaign)

            }
        }
        .refreshable {
            await viewModel.refreshCampaign(campaign: campaign)
        }
        .navigationTitle(campaign.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                Button("Edit") {
                    showingEditSheet = true
                }
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
                onGenerateAIImage: { prompt in
                    // This will be handled by the CommonMoodBoardView
                    return ""
                }
            )
        }
        .onAppear {
            themeManager.updateTheme(from: campaign)
            viewModel.fetchAvailableLLMs()
            selectedLLMId = campaign.selected_llm_id ?? ""
            temperature = Double(campaign.temperature ?? 0.7)
        }
    }
}
