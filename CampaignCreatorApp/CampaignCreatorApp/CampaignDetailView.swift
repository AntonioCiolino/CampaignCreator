import SwiftUI
import Kingfisher
import SwiftData

struct CampaignDetailView: View {
    let campaign: CampaignModel

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

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                CampaignHeaderView(campaign: campaign, editableTitle: .constant(campaign.title), isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor)

                CampaignConceptEditorView(isEditingConcept: $isEditingConcept, editableConcept: $editableConcept, isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor, currentFont: themeManager.bodyFont, currentTextColor: themeManager.textColor, onSaveChanges: {
                    campaign.concept = editableConcept
                })

                SectionBox(title: "Table of Contents") {
                    // TOC items
                }

                SectionBox(title: "Campaign Sections") {
                    // Campaign sections
                }

                SectionBox(title: "Character Linking") {
                    // Character linking
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
    }
}
