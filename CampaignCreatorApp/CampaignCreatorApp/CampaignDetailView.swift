import SwiftUI
import Kingfisher
import SwiftData
import CampaignCreatorLib

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
    @State private var selectedSection: CampaignSection?

    @Environment(\.modelContext) private var modelContext

    var body: some View {
        ScrollView {
            ZStack {
                backgroundView
                content
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
            if let firstSection = campaign.sections?.first {
                self.selectedSection = firstSection
            }
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

    private var backgroundView: some View {
        Group {
            themeManager.backgroundColor.edgesIgnoringSafeArea(.all)
            if let bgURL = themeManager.backgroundImageUrl {
                KFImage(bgURL)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .edgesIgnoringSafeArea(.all)
                    .opacity(themeManager.backgroundImageOpacity)
            }
        }
    }

    private var content: some View {
        VStack(alignment: .leading, spacing: 16) {
            CampaignHeaderView(campaign: campaign, editableTitle: .constant(campaign.title), isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor)
            CampaignConceptEditorView(isEditingConcept: $isEditingConcept, editableConcept: $editableConcept, isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor, currentFont: themeManager.bodyFont, currentTextColor: themeManager.textColor, onSaveChanges: {
                campaign.concept = editableConcept
            })
            tocSection
            sectionsSection
            selectedSectionView
            addSectionButton
            llmSettingsSection
            moodboardSection
        }
        .padding()
    }

    private var tocSection: some View {
        CollapsibleSectionView(title: "Table of Contents") {
            TOCView(campaign: campaign, selectedSection: $selectedSection, llmService: llmService)
        }
    }

    private var sectionsSection: some View {
        CollapsibleSectionView(title: "Sections") {
            if let sections = campaign.sections, !sections.isEmpty {
                Picker("Section", selection: $selectedSection) {
                    ForEach(sections, id: \.self) { section in
                        Text(section.title ?? "Untitled Section").tag(section as CampaignSection?)
                    }
                }
                .pickerStyle(MenuPickerStyle())
            } else {
                Text("No sections available. Add a section to get started.")
                    .foregroundColor(.secondary)
            }
        }
    }

    @ViewBuilder
    private var selectedSectionView: some View {
        if let selectedSection = selectedSection {
            let featureService = FeatureService()
            featureService.setModelContext(modelContext)
            CampaignSectionView(viewModel: CampaignSectionViewModel(section: selectedSection, llmService: llmService, featureService: featureService, onDelete: {
                if let index = campaign.sections?.firstIndex(where: { $0.id == selectedSection.id }) {
                    campaign.sections?.remove(at: index)
                    self.selectedSection = nil
                }
            }))
        }
    }

    private var addSectionButton: some View {
        Button("Add Section") {
            addSection()
        }
    }

    private var llmSettingsSection: some View {
        CampaignLLMSettingsView(selectedLLMId: $selectedLLMId, temperature: $temperature, availableLLMs: llmService.availableLLMs, currentFont: themeManager.bodyFont, currentTextColor: themeManager.textColor, onLLMSettingsChange: {
            campaign.selected_llm_id = selectedLLMId
            campaign.temperature = temperature
        })
    }

    private var moodboardSection: some View {
        CampaignMoodboardView(campaign: campaign, onSetBadgeAction: {
            showingSetBadgeSheet = true
        })
    }

    private func addSection() {
        Task {
            do {
                let newSection = try await llmService.apiService.addCampaignSection(
                    campaignId: campaign.id,
                    payload: CampaignSectionCreatePayload(title: "New Section", bypass_llm: true)
                )
                DispatchQueue.main.async {
                    let newCampaignSection = CampaignSection(id: newSection.id, campaign_id: newSection.campaign_id ?? 0, title: newSection.title, content: newSection.content, order: newSection.order, type: newSection.type)
                    campaign.sections?.append(newCampaignSection)
                }
            } catch {
                errorMessage = "Failed to add section: \(error.localizedDescription)"
                showingErrorAlert = true
            }
        }
    }

    private func refreshCampaign() async {
        do {
            let refreshedCampaignData = try await llmService.apiService.fetchCampaign(id: campaign.id)
            DispatchQueue.main.async {
                self.campaign.title = refreshedCampaignData.title
                self.campaign.concept = refreshedCampaignData.concept
                self.campaign.initial_user_prompt = refreshedCampaignData.initialUserPrompt
                self.campaign.badge_image_url = refreshedCampaignData.badgeImageURL
                self.campaign.thematic_image_url = refreshedCampaignData.thematicImageURL
                self.campaign.thematic_image_prompt = refreshedCampaignData.thematicImagePrompt
                self.campaign.selected_llm_id = refreshedCampaignData.selectedLLMId
                self.campaign.temperature = refreshedCampaignData.temperature
                self.campaign.theme_primary_color = refreshedCampaignData.themePrimaryColor
                self.campaign.theme_secondary_color = refreshedCampaignData.themeSecondaryColor
                self.campaign.theme_background_color = refreshedCampaignData.themeBackgroundColor
                self.campaign.theme_text_color = refreshedCampaignData.themeTextColor
                self.campaign.theme_font_family = refreshedCampaignData.themeFontFamily
                self.campaign.theme_background_image_url = refreshedCampaignData.themeBackgroundImageURL
                self.campaign.theme_background_image_opacity = refreshedCampaignData.themeBackgroundImageOpacity
                self.campaign.mood_board_image_urls = refreshedCampaignData.moodBoardImageURLs
                self.campaign.sections = refreshedCampaignData.sections.map { CampaignSection(id: $0.id, campaign_id: $0.campaign_id ?? 0, title: $0.title, content: $0.content, order: $0.order, type: $0.type) }
            }
        } catch {
            errorMessage = "Failed to refresh campaign: \(error.localizedDescription)"
            showingErrorAlert = true
        }
    }
}
