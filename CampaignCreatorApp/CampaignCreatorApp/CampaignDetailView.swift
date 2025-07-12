import SwiftUI
import CampaignCreatorLib
// import PhotosUI // REMOVED - No longer using PhotosPicker for badge

// Helper extension for Binding<Double?> to Double for Slider
extension Binding where Value == Double? {
    func withDefault(_ defaultValue: Double) -> Binding<Double> {
        Binding<Double>(
            get: { self.wrappedValue ?? defaultValue },
            set: { self.wrappedValue = $0 }
        )
    }
}

struct CampaignDetailView: View {
    @State var campaign: Campaign
    @ObservedObject var campaignCreator: CampaignCreator
    private let imageUploadService: ImageUploadService // Added image upload service
    
    @State private var editableTitle: String
    @State private var editableConcept: String
    
    @State private var isEditingConcept = false
    @State private var isSaving = false
    @State private var showErrorAlert = false
    @State private var errorMessage = ""
    
    @State private var showingGenerateSheet = false
    @State private var generatePrompt = ""
    @State private var isGeneratingText = false // Renamed for clarity
    @State private var generationError: String?
    @State private var imageGenerationError: String? // For image generation
    
    @State private var showingExportSheet = false
    @State private var exportedMarkdown = ""
    
    @State private var showingGenerateImageSheet = false // New state for image sheet
    @State private var imageGeneratePrompt = "" // Prompt for image generation
    @State private var showingCampaignEditSheet = false // Renamed from showingThemeEditSheet
    @State private var showingSetBadgeOptions = false
    @State private var showingGenerateBadgeWithAISheet = false
    @State private var showingSelectBadgeFromMoodboardSheet = false
    
    @State private var viewRefreshTrigger = UUID()
    @State private var initialLLMSettingsLoaded = false
    @State private var availableLLMsFromAPI: [CampaignCreatorLib.AvailableLLM] = []
    @State private var llmFetchError: String? = nil

    @State private var currentStandardSectionIndexForImageGen: Int? = nil
    @State private var showingImagePromptModalForStandardSection: Bool = false

    @State private var titleDebounceTimer: Timer?
    @State private var customSectionTitleDebounceTimers: [Int: Timer] = [:]
    @State private var customSectionContentDebounceTimers: [Int: Timer] = [:]
    
    @State private var nextTemporaryClientSectionID: Int = -1
    @State private var localCampaignCustomSections: [CampaignCustomSection]
    @State private var customTextViewCoordinators: [Int: CustomTextView.Coordinator] = [:]
    @State private var snippetFeatures: [Feature] = []
    @State private var isLoadingFeatures: Bool = false
    private let featureService = FeatureService()
    
    @State private var showingContextModal: Bool = false
    @State private var currentFeatureForModal: Feature? = nil
    @State private var currentSectionIdForModal: Int? = nil
    @State private var currentSelectedTextForModal: String = ""
    
    @State private var showingImagePromptModalForSection: Bool = false
    @State private var currentSectionIdForImageGen: Int? = nil
    @State private var imageGenPromptText: String = "" // Added back
    
    @State private var featureFetchError: String? = nil
    @State private var snippetProcessingError: String? = nil
    @State private var fullSectionRegenError: String? = nil
    @State private var sectionImageGenError: String? = nil
    
    private var computedErrorMessage: String? {
        let errors = [
            featureFetchError,
            snippetProcessingError,
            fullSectionRegenError,
            sectionImageGenError,
            errorMessage
        ].compactMap { $0 }
        return errors.isEmpty ? nil : errors.joined(separator: "\n---\n")
    }
    
    @Environment(\.horizontalSizeClass) var horizontalSizeClass
    
    private let sectionTypes = ["Generic", "NPC", "Character", "Location", "Item", "Quest", "Monster", "Chapter", "Note", "World Detail"]
    
    init(campaign: Campaign, campaignCreator: CampaignCreator) {
        self._campaign = State(initialValue: campaign)
        self._campaignCreator = ObservedObject(wrappedValue: campaignCreator)
        self._editableTitle = State(initialValue: campaign.title)
        self._editableConcept = State(initialValue: campaign.concept ?? "")
        self._localCampaignCustomSections = State(initialValue: campaign.customSections ?? [])
        self.imageUploadService = ImageUploadService(apiService: campaignCreator.apiService)
    }
    
    private func uiFontFrom(swiftUIFont: Font, defaultSize: CGFloat = 16) -> UIFont {
        if let fontName = campaign.themeFontFamily, !fontName.isEmpty {
            return UIFont(name: fontName, size: defaultSize) ?? UIFont.systemFont(ofSize: defaultSize)
        }
        return UIFont.systemFont(ofSize: defaultSize)
    }
    
    private var currentPrimaryColor: Color { campaign.themePrimaryColor.map { Color(hex: $0) } ?? .accentColor }
    private var currentSecondaryColor: Color { campaign.themeSecondaryColor.map { Color(hex: $0) } ?? .secondary }
    private var currentBackgroundColor: Color { campaign.themeBackgroundColor.map { Color(hex: $0) } ?? Color(.systemBackground) }
    private var currentTextColor: Color { campaign.themeTextColor.map { Color(hex: $0) } ?? Color(.label) }
    private var currentFont: Font {
        if let fontName = campaign.themeFontFamily, !fontName.isEmpty {
            return .custom(fontName, size: 16)
        }
        return .body
    }

    private var linkedCharactersSection: some View {
        Group {
            if let charIDs = campaign.linkedCharacterIDs, !charIDs.isEmpty {
                DisclosureGroup("Linked Characters") {
                    ForEach(charIDs, id: \.self) { id in
                        if let char = campaignCreator.characters.first(where: { $0.id == id }) {
                            Text(char.name)
                        } else {
                            Text("Character ID: \(id) (Not loaded)")
                        }
                    }
                }
                .padding().background(Color(.secondarySystemBackground)).cornerRadius(12)
                .font(currentFont)
                .foregroundColor(currentTextColor)
            } else {
                Text("No characters linked yet.")
                    .font(currentFont.italic())
                    .foregroundColor(currentTextColor.opacity(0.7))
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .center)
            }
        }
    }

    // Handler for snippet selection in STANDARD sections
    private func handleStandardSnippetFeatureSelection(_ feature: Feature, forSectionAtIndex index: Int) {
        print("Placeholder: handleStandardSnippetFeatureSelection for feature \(feature.name) at index \(index) (Standard Section)")
        let sectionTitle = (index < campaign.sections.count) ? (campaign.sections[index].title ?? "Untitled") : "Unknown Section"
        self.errorMessage = "Snippet feature '\(feature.name)' not yet implemented for standard section '\(sectionTitle)'."
        self.showErrorAlert = true
    }

    // Handler for regeneration of STANDARD sections
    private func handleStandardSectionRegeneration(forSectionAtIndex index: Int) {
        print("Placeholder: handleStandardSectionRegeneration for section at index \(index) (Standard Section)")
        if index < campaign.sections.count {
            let sectionTitle = campaign.sections[index].title ?? "Untitled"
            self.errorMessage = "Regeneration for standard section '\(sectionTitle)' not yet implemented."
        } else {
            self.errorMessage = "Regeneration for standard section (index out of bounds) not yet implemented."
        }
        self.showErrorAlert = true
    }
    
    // Handler for snippet selection in CUSTOM sections (different signature)
    private func handleSnippetFeatureSelection(forCustomSection feature: Feature, section: CampaignCustomSection) {
        guard let coordinator = customTextViewCoordinators[section.id] else {
            print("Coordinator not found for custom section \(section.id) to process snippet feature '\(feature.name)'.")
            return
        }
        guard let selectedText = coordinator.getSelectedText(), !selectedText.isEmpty else {
            print("No text selected in custom section \(section.id) for snippet feature '\(feature.name)'.")
            return
        }
        let currentRange = coordinator.getCurrentSelectedRange()
        let additionalRequiredContext = feature.requiredContext?.filter { $0 != "selected_text" && $0 != "campaign_characters" } ?? []
        if additionalRequiredContext.isEmpty {
            processSnippetWithLLM(feature: feature, sectionId: section.id, selectedText: selectedText, rangeToReplace: currentRange, additionalContext: [:])
        } else {
            self.currentFeatureForModal = feature
            self.currentSectionIdForModal = section.id
            self.currentSelectedTextForModal = selectedText
            self.showingContextModal = true
        }
    }

    // Handler for regeneration of CUSTOM sections (different signature)
    private func handleFullSectionRegeneration(forCustomSection section: CampaignCustomSection) {
        fullSectionRegenError = nil
        guard let coordinator = customTextViewCoordinators[section.id] else {
            fullSectionRegenError = "Error: Coordinator not found for section \(section.id) for full regeneration."
            return
        }
        let selectedText = coordinator.getSelectedText()
        let currentFullText = section.content
        let promptForRegeneration = selectedText ?? currentFullText

        Task {
            let payload = SectionRegeneratePayload(
                newPrompt: promptForRegeneration,
                newTitle: section.title,
                sectionType: section.type,
                modelIdWithPrefix: campaign.selectedLLMId,
                featureId: nil,
                contextData: selectedText != nil ? ["user_instructions": selectedText!] : nil
            )
            do {
                let _ = try await campaignCreator.regenerateCampaignCustomSection(
                    campaignId: Int(campaign.id),
                    sectionId: section.id,
                    payload: payload
                )
                if let refreshedCampaignFromCreator = campaignCreator.campaigns.first(where: { $0.id == self.campaign.id }) {
                    self.campaign = refreshedCampaignFromCreator
                    self.localCampaignCustomSections = refreshedCampaignFromCreator.customSections ?? []
                }
                await self.saveCampaignDetails(source: .customSectionChange, includeCustomSections: true)
            } catch {
                let errorDescription = "Error regenerating full content for section \(section.title): \(error.localizedDescription)"
                fullSectionRegenError = errorDescription
                self.errorMessage = "Content Regeneration Failed (Section: \(section.title))"
                self.showErrorAlert = true
            }
        }
    }

    private var tableOfContentsSection: some View {
        DisclosureGroup("Table of Contents") {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(campaign.displayTOC ?? []) { entry in Text(entry.title).font(.body) }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 4)
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
        .foregroundColor(currentTextColor).font(currentFont)
    }
    
    private var campaignThemeDisplaySection: some View {
        DisclosureGroup("Campaign Theme") {
            VStack(alignment: .leading, spacing: 8) {
                ThemePropertyRow(label: "Primary Color", value: campaign.themePrimaryColor)
                ThemePropertyRow(label: "Secondary Color", value: campaign.themeSecondaryColor)
                ThemePropertyRow(label: "Background Color", value: campaign.themeBackgroundColor)
                ThemePropertyRow(label: "Text Color", value: campaign.themeTextColor)
                ThemePropertyRow(label: "Font Family", value: campaign.themeFontFamily)
                ThemePropertyRow(label: "Background Image URL", value: campaign.themeBackgroundImageURL, isURL: true)
                ThemePropertyRow(label: "BG Image Opacity", value: campaign.themeBackgroundImageOpacity.map { String(format: "%.2f", $0) })
                if let linkedIDs = campaign.linkedCharacterIDs, !linkedIDs.isEmpty {
                    Text("Linked Characters:").font(currentFont.weight(.semibold)).padding(.top, 5)
                    ForEach(linkedIDs, id: \.self) { charID in
                        if let char = campaignCreator.characters.first(where: { $0.id == charID }) {
                            Text("  - \(char.name)").font(currentFont)
                        } else {
                            Text("  - Character ID: \(charID) (Not found)").font(currentFont.italic()).foregroundColor(.gray)
                        }
                    }
                }
                Button("Edit Campaign Details") { showingCampaignEditSheet = true }
                .buttonStyle(.bordered).tint(currentPrimaryColor).padding(.top, 8)
            }
            .frame(maxWidth: .infinity, alignment: .leading).padding(.top, 4)
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
        .foregroundColor(currentTextColor).font(currentFont)
    }
    
    // sectionsDisplaySection, standardSectionContentView, and standardSectionActionButtons are now part of CampaignStandardSectionsView

    private func handleImageGenerationForSection() async {
        sectionImageGenError = nil
        guard let sectionId = currentSectionIdForImageGen,
              let coordinator = customTextViewCoordinators[sectionId] else {
            sectionImageGenError = "Error: Missing section ID or coordinator for image generation."
            return
        }
        let prompt = imageGenPromptText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !prompt.isEmpty else {
            sectionImageGenError = "Error: Image generation prompt is empty."
            return
        }
        print("Generating image for section \(sectionId) with prompt: \(prompt)")
        do {
            let response = try await campaignCreator.generateImageForSection(prompt: prompt, campaignId: Int(campaign.id))
            let markdownImage = "\n![Generated Image: \(response.promptUsed)](\(response.imageUrl))\n"
            coordinator.insertTextAtCurrentCursor(markdownImage)
            if let index = localCampaignCustomSections.firstIndex(where: { $0.id == sectionId }),
               let currentCoordinatorText = coordinator.textView?.text {
                if localCampaignCustomSections[index].content != currentCoordinatorText {
                    localCampaignCustomSections[index].content = currentCoordinatorText
                }
            }
            await self.saveCampaignDetails(source: .customSectionChange, includeCustomSections: true)
        } catch {
            let errorDescription = "Error generating image for section \(sectionId): \(error.localizedDescription)"
            sectionImageGenError = errorDescription
            self.errorMessage = "Image Generation Failed (For section related to prompt: \"\(prompt.prefix(30))...\")"
            self.showErrorAlert = true
        }
        self.currentSectionIdForImageGen = nil
        self.imageGenPromptText = ""
    }

    private func processSnippetWithLLM(feature: Feature, sectionId: Int, selectedText: String, rangeToReplace: NSRange, additionalContext: [String: String]) {
        snippetProcessingError = nil
        guard let coordinator = customTextViewCoordinators[sectionId] else {
            snippetProcessingError = "Error: Coordinator not found for section \(sectionId) during LLM processing."
            return
        }
        guard let currentCampaignSection = localCampaignCustomSections.first(where: { $0.id == sectionId }) else {
            snippetProcessingError = "Error: Could not find current campaign section with ID \(sectionId) in local state for snippet processing."
            return
        }
        Task {
            let payload = SectionRegeneratePayload(
                newPrompt: selectedText,
                newTitle: currentCampaignSection.title,
                sectionType: currentCampaignSection.type,
                modelIdWithPrefix: campaign.selectedLLMId,
                featureId: feature.id,
                contextData: additionalContext.merging(["selected_text": selectedText]) { (_, new) in new }
            )
            do {
                let returnedUpdatedSectionData = try await campaignCreator.regenerateCampaignCustomSection(
                    campaignId: Int(campaign.id),
                    sectionId: sectionId,
                    payload: payload
                )
                coordinator.replaceText(inRange: rangeToReplace, with: returnedUpdatedSectionData.content)
                if let refreshedCampaignFromCreator = campaignCreator.campaigns.first(where: { $0.id == self.campaign.id }) {
                    self.campaign = refreshedCampaignFromCreator
                    self.localCampaignCustomSections = refreshedCampaignFromCreator.customSections ?? []
                    if let index = self.localCampaignCustomSections.firstIndex(where: { $0.id == sectionId }) {
                        if self.localCampaignCustomSections[index].content != returnedUpdatedSectionData.content {
                            self.localCampaignCustomSections[index].content = returnedUpdatedSectionData.content
                        }
                    }
                }
                await self.saveCampaignDetails(source: .customSectionChange, includeCustomSections: true)
            } catch {
                let errorDescription = "Error processing snippet for feature '\(feature.name)': \(error.localizedDescription)"
                snippetProcessingError = errorDescription
                self.errorMessage = "Snippet Processing Failed (Section: \(currentCampaignSection.title))"
                self.showErrorAlert = true
            }
        }
    }

    private func fetchSnippetFeatures() async {
        isLoadingFeatures = true
        featureFetchError = nil
        do {
            let allFeatures = try await featureService.fetchFeatures()
            self.snippetFeatures = allFeatures.filter {
                $0.featureCategory?.lowercased() == "snippet" ||
                ($0.featureCategory == nil && !["Campaign", "TOC Homebrewery", "TOC Display", "Campaign Names"].contains($0.name))
            }
        } catch {
            let errorDescription = "Error fetching snippet features: \(error.localizedDescription)"
            featureFetchError = errorDescription
            self.errorMessage = "Feature Loading Failed"
            self.showErrorAlert = true
        }
        isLoadingFeatures = false
    }

    // Extracted view for campaign content sections
    @ViewBuilder
    private var campaignContentSections: some View {
        DisclosureGroup("Campaign Sections") {
            VStack(alignment: .leading, spacing: 16) {
                CampaignCustomSectionsEditor(
                    localCampaignCustomSections: $localCampaignCustomSections,
                    customSectionTitleDebounceTimers: $customSectionTitleDebounceTimers,
                    customSectionContentDebounceTimers: $customSectionContentDebounceTimers,
                    customTextViewCoordinators: $customTextViewCoordinators,
                    nextTemporaryClientSectionID: $nextTemporaryClientSectionID,
                    showingImagePromptModalForSection: $showingImagePromptModalForSection,
                    currentSectionIdForImageGen: $currentSectionIdForImageGen,
                    imageGenPromptText: $imageGenPromptText,
                    currentFont: currentFont,
                    currentFontFamily: campaign.themeFontFamily,
                    currentPrimaryColor: currentPrimaryColor,
                    currentTextColor: currentTextColor,
                    sectionTypes: sectionTypes,
                    snippetFeatures: snippetFeatures,
                    isLoadingFeatures: isLoadingFeatures,
                    saveCampaignDetails: { source, includeTheme, includeCustom, includeStandard, editingSectionID, latestContent in
                        await self.saveCampaignDetails(source: source, includeTheme: includeTheme, includeCustomSections: includeCustom, includeStandardSections: includeStandard, editingSectionID: editingSectionID, latestSectionContent: latestContent)
                    },
                    handleSnippetFeatureSelection: self.handleSnippetFeatureSelection,
                    handleFullSectionRegeneration: self.handleFullSectionRegeneration
                )
                CampaignStandardSectionsView(
                    sections: $campaign.sections,
                    customSectionTitleDebounceTimers: $customSectionTitleDebounceTimers,
                    customSectionContentDebounceTimers: $customSectionContentDebounceTimers,
                    customTextViewCoordinators: $customTextViewCoordinators,
                    showingImagePromptModalForStandardSection: $showingImagePromptModalForStandardSection,
                    currentStandardSectionIndexForImageGen: $currentStandardSectionIndexForImageGen,
                    imageGenPromptText: $imageGenPromptText,
                    currentFont: currentFont,
                    currentFontFamily: campaign.themeFontFamily,
                    currentPrimaryColor: currentPrimaryColor,
                    currentTextColor: currentTextColor,
                    snippetFeatures: snippetFeatures,
                    isLoadingFeatures: isLoadingFeatures,
                    saveCampaignDetails: { source, includeTheme, includeCustom, includeStandard, editingSectionID, latestContent in
                        await self.saveCampaignDetails(source: source, includeTheme: includeTheme, includeCustomSections: includeCustom, includeStandardSections: includeStandard, editingSectionID: editingSectionID, latestSectionContent: latestContent)
                    },
                    handleStandardSnippetFeatureSelection: self.handleStandardSnippetFeatureSelection,
                    handleStandardSectionRegeneration: self.handleStandardSectionRegeneration
                )
            }
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
        .font(currentFont).foregroundColor(currentTextColor)
    }

    // Extracted view for LLM settings and related messages
    @ViewBuilder
    private var campaignLLMSettingsAndMessages: some View {
        CampaignLLMSettingsView(
            selectedLLMId: $campaign.selectedLLMId.withDefault((availableLLMsFromAPI.first ?? placeholderLLMs.first)?.id ?? "default-llm-id"),
            temperature: $campaign.temperature.withDefault(0.7),
            availableLLMs: availableLLMsFromAPI.isEmpty ? placeholderLLMs : availableLLMsFromAPI,
            currentFont: currentFont,
            currentTextColor: currentTextColor,
            onLLMSettingsChange: { await self.saveCampaignDetails(source: .llmSettingsChange, includeLLMSettings: true) }
        )
        if !campaignCreator.isLLMServiceAvailable {
            Text("Note: AI Text Generation features require OpenAI API key configuration in settings.")
                .font(.caption).foregroundColor(.orange).padding(.vertical).frame(maxWidth: .infinity, alignment: .center)
        }
        if let llmFetchError = llmFetchError {
            Text("Error fetching LLM list: \(llmFetchError)")
                .font(.caption).foregroundColor(.red).padding(.vertical).frame(maxWidth: .infinity, alignment: .center)
        }
    }

    // Extracted main content view to help with compiler performance
    @ViewBuilder
    private var mainContentView: some View {
        VStack(alignment: .leading, spacing: 16) {
            CampaignHeaderView(campaign: campaign, editableTitle: $editableTitle, isSaving: isSaving, isGeneratingText: isGeneratingText, currentPrimaryColor: currentPrimaryColor, onSetBadgeAction: { self.showingSetBadgeOptions = true })
            CampaignConceptEditorView(isEditingConcept: $isEditingConcept, editableConcept: $editableConcept, isSaving: isSaving, isGeneratingText: isGeneratingText, currentPrimaryColor: currentPrimaryColor, currentFont: currentFont, currentTextColor: currentTextColor, onSaveChanges: { await self.saveCampaignDetails(source: .conceptEditorDoneButton) })
            if let tocEntries = campaign.displayTOC, !tocEntries.isEmpty { tableOfContentsSection }

            campaignContentSections // Extracted View

            linkedCharactersSection

            campaignLLMSettingsAndMessages // Extracted View
        }
        .padding().font(currentFont).foregroundColor(currentTextColor)
    }

    var body: some View {
        ZStack {
            if let bgImageURLString = campaign.themeBackgroundImageURL, let bgImageURL = URL(string: bgImageURLString) {
                AsyncImage(url: bgImageURL) { image in image.resizable().aspectRatio(contentMode: .fill) } placeholder: { Color.clear }
                .opacity(campaign.themeBackgroundImageOpacity ?? 1.0).edgesIgnoringSafeArea(.all).clipped()
            } else {
                currentBackgroundColor.edgesIgnoringSafeArea(.all)
            }
            ScrollView {
                mainContentView // Using the extracted main content view
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .refreshable {
            do {
                let refreshedCampaignData = try await campaignCreator.refreshCampaign(id: campaign.id)
                self.campaign = refreshedCampaignData
                self.editableTitle = refreshedCampaignData.title
                self.editableConcept = refreshedCampaignData.concept ?? ""
                self.localCampaignCustomSections = refreshedCampaignData.customSections ?? []
                self.viewRefreshTrigger = UUID()
            } catch {
                self.errorMessage = "Failed to refresh campaign: \(error.localizedDescription)"
                self.showErrorAlert = true
            }
        }
        .id(viewRefreshTrigger)
        .navigationTitle(editableTitle)
        .navigationBarTitleDisplayMode(.inline)
        .disabled(isSaving || isGeneratingText)
        .onAppear {
            if !initialLLMSettingsLoaded {
                print("[LLM_DEBUG CampaignDetailView] View appeared. Initial campaign LLM Settings: ID=\(campaign.selectedLLMId ?? "nil"), Temp=\(campaign.temperature?.description ?? "not set")")
                initialLLMSettingsLoaded = true
            }
            Task {
                if availableLLMsFromAPI.isEmpty {
                    do {
                        let fetchedLLMs = try await campaignCreator.apiService.fetchAvailableLLMs()
                        self.availableLLMsFromAPI = fetchedLLMs
                        self.llmFetchError = nil
                        if self.campaign.selectedLLMId == nil || !fetchedLLMs.contains(where: { $0.id == self.campaign.selectedLLMId }) {
                            if let firstAPILLM = fetchedLLMs.first {
                                self.campaign.selectedLLMId = firstAPILLM.id
                                await self.saveCampaignDetails(source: .llmSettingsChange, includeLLMSettings: true)
                            }
                        }
                    } catch {
                        self.llmFetchError = error.localizedDescription
                    }
                }
                await fetchSnippetFeatures()
                if (!campaignCreator.initialCharacterFetchAttempted || campaignCreator.characterError != nil) && !campaignCreator.isLoadingCharacters {
                    await campaignCreator.fetchCharacters()
                }
                if let updatedCampaignFromList = campaignCreator.campaigns.first(where: { $0.id == self.campaign.id }) {
                    if updatedCampaignFromList.modifiedAt != self.campaign.modifiedAt ||
                       updatedCampaignFromList.moodBoardImageURLs != self.campaign.moodBoardImageURLs ||
                       updatedCampaignFromList.badgeImageURL != self.campaign.badgeImageURL ||
                       updatedCampaignFromList.title != self.campaign.title {
                        self.campaign = updatedCampaignFromList
                        self.editableTitle = updatedCampaignFromList.title
                        self.editableConcept = updatedCampaignFromList.concept ?? ""
                        self.localCampaignCustomSections = updatedCampaignFromList.customSections ?? []
                        self.viewRefreshTrigger = UUID()
                    }
                } else {
                    do {
                        let refreshedCampaign = try await campaignCreator.refreshCampaign(id: self.campaign.id)
                        self.campaign = refreshedCampaign
                        self.editableTitle = refreshedCampaign.title
                        self.editableConcept = refreshedCampaign.concept ?? ""
                        self.localCampaignCustomSections = refreshedCampaign.customSections ?? []
                        self.viewRefreshTrigger = UUID()
                    } catch {
                        self.errorMessage = "Failed to refresh campaign data: \(error.localizedDescription)"
                        self.showErrorAlert = true
                    }
                }
            }
        }
        .sheet(isPresented: $showingContextModal) {
            if let feature = currentFeatureForModal, let sectionId = currentSectionIdForModal {
                SnippetContextInputModal(isPresented: $showingContextModal, feature: feature, campaignCharacters: campaignCreator.characters, selectedText: currentSelectedTextForModal,
                    onSubmit: { contextData in
                        if let coordinator = customTextViewCoordinators[sectionId] {
                            let rangeToReplace = coordinator.getCurrentSelectedRange()
                            processSnippetWithLLM(feature: feature, sectionId: sectionId, selectedText: currentSelectedTextForModal, rangeToReplace: rangeToReplace, additionalContext: contextData)
                        }
                    }
                )
            } else {
                Text("Error: Missing feature or section context for modal.").onAppear { showingContextModal = false }
            }
        }
        .sheet(isPresented: $showingImagePromptModalForSection) {
            NavigationView {
                VStack {
                    Text("Generate Image for Section").font(.headline).padding()
                    TextEditor(text: $imageGenPromptText).frame(height: 100).border(Color.gray).padding()
                    Button("Generate Image") { Task { await handleImageGenerationForSection() }; showingImagePromptModalForSection = false }
                    .buttonStyle(.borderedProminent).disabled(imageGenPromptText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty).padding()
                    Spacer()
                }
                .navigationTitle("Image Prompt").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .navigationBarLeading) { Button("Cancel") { showingImagePromptModalForSection = false } } }
            }
        }
        .alert(isPresented: $showErrorAlert) {
            Alert(title: Text(errorMessage), message: Text(computedErrorMessage ?? "An unexpected error occurred. Please try again."),
                dismissButton: .default(Text("OK")) {
                    featureFetchError = nil; snippetProcessingError = nil; fullSectionRegenError = nil; sectionImageGenError = nil; self.errorMessage = ""
                }
            )
        }
        .onDisappear {
            titleDebounceTimer?.invalidate()
            customSectionTitleDebounceTimers.values.forEach { $0.invalidate() }
            customSectionContentDebounceTimers.values.forEach { $0.invalidate() }
            customSectionTitleDebounceTimers.removeAll()
            customSectionContentDebounceTimers.removeAll()
            if campaign.title != editableTitle || campaign.concept ?? "" != editableConcept {
                Task { await saveCampaignDetails(source: .onDisappear) }
            }
        }
        .sheet(isPresented: $showingGenerateSheet) { generateSheetView }
        .sheet(isPresented: $showingGenerateImageSheet) { generateImageSheetView }
        .sheet(isPresented: $showingExportSheet) { exportSheetView }
        .sheet(isPresented: $showingCampaignEditSheet, onDismiss: {
            Task {
                do {
                    let refreshedCampaign = try await campaignCreator.refreshCampaign(id: self.campaign.id)
                    self.campaign = refreshedCampaign; self.editableTitle = refreshedCampaign.title; self.editableConcept = refreshedCampaign.concept ?? ""; self.localCampaignCustomSections = refreshedCampaign.customSections ?? []; self.viewRefreshTrigger = UUID()
                } catch {
                    self.errorMessage = "Failed to update campaign details. Please try refreshing."; self.showErrorAlert = true
                }
            }
        }) { CampaignEditView(campaign: $campaign, campaignCreator: campaignCreator, isPresented: $showingCampaignEditSheet) }
        .toolbar { detailViewToolbarContent() }
        .onChange(of: horizontalSizeClass) { newSizeClass in print("Horizontal size class changed to: \((newSizeClass != nil ? String(describing: newSizeClass!) : "nil"))") }
        .sheet(isPresented: $showingGenerateBadgeWithAISheet) { generateBadgeSheetView }
        .sheet(isPresented: $showingSelectBadgeFromMoodboardSheet) {
            SelectBadgeFromMoodboardView(moodBoardImageURLs: campaign.moodBoardImageURLs ?? [], thematicImageURL: campaign.thematicImageURL,
                onImageSelected: { selectedURL in self.campaign.badgeImageURL = selectedURL; self.campaign.markAsModified(); Task { await self.saveCampaignDetails(source: .badgeImageUpdate) }; self.showingSelectBadgeFromMoodboardSheet = false }
            )
        }
        .confirmationDialog("Set Campaign Badge", isPresented: $showingSetBadgeOptions, titleVisibility: .visible) {
            Button("Generate with AI") { self.imageGeneratePrompt = "Campaign badge for: \(campaign.title)"; self.showingGenerateBadgeWithAISheet = true }
            Button("Select from Mood Board") { self.showingSelectBadgeFromMoodboardSheet = true }
            if campaign.badgeImageURL != nil { Button("Remove Badge", role: .destructive) { campaign.badgeImageURL = nil; campaign.markAsModified(); Task { await saveCampaignDetails(source: .badgeImageUpdate) } } }
            Button("Cancel", role: .cancel) { }
        } message: { Text("Choose a source for your campaign badge.") }
    }

    @ToolbarContentBuilder
    private func detailViewToolbarContent() -> some ToolbarContent {
        ToolbarItemGroup(placement: .navigationBarTrailing) {
            if isSaving || isGeneratingText { ProgressView() }
            else {
                Button { showingCampaignEditSheet = true } label: { Label("Theme", systemImage: "paintbrush.pointed.fill") }.disabled(isSaving || isGeneratingText)
                NavigationLink(destination: CampaignMoodboardView(campaign: campaign, campaignCreator: campaignCreator).environmentObject(imageUploadService)) { Label("Mood Board", systemImage: "photo.on.rectangle.angled") }.disabled(isSaving || isGeneratingText)
                Button { showingGenerateSheet = true } label: { Label("Generate Section", systemImage: "sparkles") }.disabled(isSaving || isGeneratingText || !campaignCreator.isLLMServiceAvailable)
            }
        }
    }

    private func generateTemporaryClientSectionID() -> Int {
        let tempID = nextTemporaryClientSectionID
        nextTemporaryClientSectionID -= 1
        return tempID
    }

    private var generateImageSheetView: some View { EmptyView() }
    private var generateBadgeSheetView: some View { EmptyView() }
    private func performAICampaignImageGeneration() async { /* ... existing ... */ }
    private func performAIBadgeGeneration() async { /* ... existing ... */ }
    enum SaveSource { case titleField, conceptEditorDoneButton, onDisappear, themeEditorDismissed, customSectionChange, standardSectionChange, llmSettingsChange, badgeImageUpdate }
    private func saveCampaignDetails(source: SaveSource, includeTheme: Bool = false, includeCustomSections: Bool = false, includeStandardSections: Bool = false, includeLLMSettings: Bool = false, editingSectionID: Int? = nil, latestSectionContent: String? = nil) async { /* ... existing ... */ }
    private var generateSheetView: some View { EmptyView() }
    private func performAIGeneration() async { /* ... existing ... */ }
    private var exportSheetView: some View { EmptyView() }
    private func exportCampaignContent() { /* ... existing ... */ }
}

// String extensions like stripSuffix and nilIfEmpty are now in StringUtils.swift

struct ThemePropertyRow: View {
    let label: String
    let value: String?
    var isURL: Bool = false

    var body: some View {
        if let value = value, !value.isEmpty {
            HStack {
                Text(label)
                    .font(Font.caption.weight(.semibold))
                    .foregroundColor(.secondary)
                Spacer()
                if isURL {
                    if let url = URL(string: value) {
                        Link(destination: url) {
                            Text(value)
                                .truncationMode(.middle)
                                .lineLimit(1)
                                .foregroundColor(.accentColor)
                        }
                    } else {
                        Text(value)
                            .truncationMode(.middle)
                            .lineLimit(1)
                            .foregroundColor(.gray)
                    }
                } else {
                    Text(value)
                        .foregroundColor(.primary)
                }
            }
            .padding(.vertical, 2)
        }
    }
}

struct CampaignStandardSectionsView: View {
    @Binding var sections: [CampaignSection]
    @Binding var customSectionTitleDebounceTimers: [Int: Timer]
    @Binding var customSectionContentDebounceTimers: [Int: Timer]
    @Binding var customTextViewCoordinators: [Int: CustomTextView.Coordinator]

    @Binding var showingImagePromptModalForStandardSection: Bool
    @Binding var currentStandardSectionIndexForImageGen: Int?
    @Binding var imageGenPromptText: String

    let currentFont: Font
    let currentFontFamily: String?
    let currentPrimaryColor: Color
    let currentTextColor: Color
    let snippetFeatures: [Feature]
    let isLoadingFeatures: Bool

    let saveCampaignDetails: (_ source: CampaignDetailView.SaveSource, _ includeTheme: Bool, _ includeCustomSections: Bool, _ includeStandardSections: Bool, _ editingSectionID: Int?, _ latestSectionContent: String?) async -> Void
    let handleStandardSnippetFeatureSelection: (Feature, Int) -> Void
    let handleStandardSectionRegeneration: (Int) -> Void

    private func uiFontFrom(fontName: String?, defaultSize: CGFloat = 16) -> UIFont {
        if let fontName = fontName, !fontName.isEmpty {
            return UIFont(name: fontName, size: defaultSize) ?? UIFont.systemFont(ofSize: defaultSize)
        }
        return UIFont.systemFont(ofSize: defaultSize)
    }

    var body: some View {
        VStack(alignment: .leading) {
            if sections.isEmpty {
                Text("No standard sections yet. Use 'Generate' to create the first section from a prompt.")
                    .font(currentFont.italic())
                    .foregroundColor(currentTextColor.opacity(0.7))
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .center)
                    .background(Color(.systemGroupedBackground)).cornerRadius(8)
            } else {
                ForEach($sections.indices, id: \.self) { index in
                    let sectionBinding = $sections[index]
                    DisclosureGroup(
                        sectionBinding.title.wrappedValue ?? "Untitled Section \(sections[index].order)"
                    ) {
                        standardSectionContentView(sectionBinding: sectionBinding, index: index)
                    }
                    .padding(.bottom, 4)
                    Divider()
                }
            }
        }
    }

    @ViewBuilder
    private func standardSectionContentView(sectionBinding: Binding<CampaignSection>, index: Int) -> some View {
        VStack(alignment: .leading) {
            TextField("Section Title", text: sectionBinding.title.withDefault("Untitled Section \(sectionBinding.wrappedValue.order)"))
                .font(currentFont.weight(.semibold))
                .textFieldStyle(PlainTextFieldStyle())
                .padding(.bottom, 2)
                .onChange(of: sectionBinding.wrappedValue.title) { newValue in
                    let sectionId = sectionBinding.wrappedValue.id
                    customSectionTitleDebounceTimers[sectionId]?.invalidate()
                    customSectionTitleDebounceTimers[sectionId] = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: false) { _ in
                        Task { await self.saveCampaignDetails(.standardSectionChange, false, false, true, sectionId, sectionBinding.wrappedValue.content) }
                    }
                }

            CustomTextView(
                text: sectionBinding.content,
                font: uiFontFrom(fontName: currentFontFamily),
                textColor: UIColor(currentTextColor),
                onCoordinatorCreated: { coordinator in
                    customTextViewCoordinators[sectionBinding.wrappedValue.id] = coordinator
                }
            )
            .frame(minHeight: 100, maxHeight: 300)
            .background(Color(.secondarySystemGroupedBackground))
            .cornerRadius(8)
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(.systemGray4), lineWidth: 1))
            .onChange(of: sectionBinding.wrappedValue.content) { newContent in
                let sectionId = sectionBinding.wrappedValue.id
                customSectionContentDebounceTimers[sectionId]?.invalidate()
                customSectionContentDebounceTimers[sectionId] = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: false) { _ in
                    Task { await self.saveCampaignDetails(.standardSectionChange, false, false, true, sectionId, newContent) }
                }
            }

            standardSectionActionButtons(sectionBinding: sectionBinding, index: index)
        }
        .padding(.vertical, 8)
    }

    @ViewBuilder
    private func standardSectionActionButtons(sectionBinding: Binding<CampaignSection>, index: Int) -> some View {
        HStack {
            Button("Delete") {
                if index < sections.count {
                    let sectionIdToDelete = sections[index].id
                    sections.remove(at: index)
                    customTextViewCoordinators.removeValue(forKey: sectionIdToDelete)
                    Task { await self.saveCampaignDetails(.standardSectionChange, false, false, true, nil, nil) }
                }
            }
            .foregroundColor(.red)
            .buttonStyle(.borderless)

            Spacer()

            Menu {
                if isLoadingFeatures { Text("Loading features...") }
                else if snippetFeatures.isEmpty { Text("No snippet features.") }
                else {
                    ForEach(snippetFeatures) { feature in
                        Button(feature.name) {
                            if index < sections.count {
                                handleStandardSnippetFeatureSelection(feature, index)
                            }
                        }
                    }
                }
            } label: {
                Label("Snippet", systemImage: "wand.and.stars").font(.caption)
            }
            .buttonStyle(.bordered).disabled(isLoadingFeatures)

            Button("Regen") {
                if index < sections.count {
                    handleStandardSectionRegeneration(index)
                }
            }
            .buttonStyle(.bordered).font(.caption)

            Button {
                if index < sections.count {
                    self.currentStandardSectionIndexForImageGen = index
                    self.imageGenPromptText = sections[index].title ?? "Image for section \(sections[index].order)"
                    self.showingImagePromptModalForStandardSection = true
                }
            } label: {
                Label("Image", systemImage: "photo.badge.plus").font(.caption)
            }
            .buttonStyle(.bordered)
        }
        .padding(.top, 4)
    }
}


struct CampaignCustomSectionsEditor: View {
    @Binding var localCampaignCustomSections: [CampaignCustomSection]
    @Binding var customSectionTitleDebounceTimers: [Int: Timer]
    @Binding var customSectionContentDebounceTimers: [Int: Timer]
    @Binding var customTextViewCoordinators: [Int: CustomTextView.Coordinator]
    @Binding var nextTemporaryClientSectionID: Int
    @Binding var showingImagePromptModalForSection: Bool
    @Binding var currentSectionIdForImageGen: Int?
    @Binding var imageGenPromptText: String

    let currentFont: Font
    let currentFontFamily: String?
    let currentPrimaryColor: Color
    let currentTextColor: Color
    let sectionTypes: [String]
    let snippetFeatures: [Feature]
    let isLoadingFeatures: Bool
    
    let saveCampaignDetails: (_ source: CampaignDetailView.SaveSource, _ includeTheme: Bool, _ includeCustomSections: Bool, _ includeStandardSections: Bool, _ editingSectionID: Int?, _ latestSectionContent: String?) async -> Void
    let handleSnippetFeatureSelection: (Feature, CampaignCustomSection) -> Void       // Adjusted for custom section
    let handleFullSectionRegeneration: (CampaignCustomSection) -> Void         // Adjusted for custom section

    private func uiFontFrom(fontName: String?, defaultSize: CGFloat = 16) -> UIFont {
        if let fontName = fontName, !fontName.isEmpty {
            return UIFont(name: fontName, size: defaultSize) ?? UIFont.systemFont(ofSize: defaultSize)
        }
        return UIFont.systemFont(ofSize: defaultSize)
    }
    
    private func addCampaignCustomSection() {
        let newId = nextTemporaryClientSectionID
        nextTemporaryClientSectionID -= 1
        let newSection = CampaignCustomSection(id: newId, title: "New Section", content: "", type: "Generic")
        localCampaignCustomSections.append(newSection)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Custom Sections")
                .font(currentFont.weight(.semibold))
                .foregroundColor(currentPrimaryColor.opacity(0.8))
                .padding(.bottom, 2)

            ForEach($localCampaignCustomSections) { $section in
                DisclosureGroup {
                    VStack(alignment: .leading) {
                        TextField("Section Title", text: $section.title.withDefault("New Custom Section"))
                            .font(currentFont.weight(.semibold))
                            .textFieldStyle(PlainTextFieldStyle())
                            .padding(.bottom, 2)
                            .onChange(of: section.title) { newValue in
                                let sectionId = section.id
                                customSectionTitleDebounceTimers[sectionId]?.invalidate()
                                customSectionTitleDebounceTimers[sectionId] = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: false) { _ in
                                    Task { await self.saveCampaignDetails(.customSectionChange, false, true, false, sectionId, section.content) }
                                }
                            }

                        Picker("Section Type", selection: $section.type.withDefault("Generic")) {
                            ForEach(sectionTypes, id: \.self) { typeName in
                                Text(typeName).tag(typeName)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                        .font(.caption)
                        .padding(.bottom, 4)
                        .onChange(of: section.type) { _ in
                            Task { await self.saveCampaignDetails(.customSectionChange, false, true, false, section.id, section.content) }
                        }

                        CustomTextView(
                            text: $section.content,
                            font: uiFontFrom(fontName: currentFontFamily),
                            textColor: UIColor(currentTextColor),
                            onCoordinatorCreated: { coordinator in
                                customTextViewCoordinators[section.id] = coordinator
                            }
                        )
                        .frame(minHeight: 100, maxHeight: 300)
                        .background(Color(.secondarySystemGroupedBackground))
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(.systemGray4), lineWidth: 1))
                        .onChange(of: section.content) { newContent in
                            let sectionId = section.id
                            customSectionContentDebounceTimers[sectionId]?.invalidate()
                            customSectionContentDebounceTimers[sectionId] = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: false) { _ in
                                Task { await self.saveCampaignDetails(.customSectionChange, false, true, false, sectionId, newContent) }
                            }
                        }

                        HStack {
                            Button(role: section.id < 0 ? .none : .destructive) {
                                let sectionIdToDelete = section.id
                                localCampaignCustomSections.removeAll { $0.id == sectionIdToDelete }
                                customTextViewCoordinators.removeValue(forKey: sectionIdToDelete)
                                if sectionIdToDelete >= 0 {
                                    Task { await self.saveCampaignDetails(.customSectionChange, false, true, false, nil, nil) }
                                }
                            } label: {
                                Text(section.id < 0 ? "Remove" : "Delete Section")
                            }
                            .foregroundColor(section.id < 0 ? .blue : .red)
                            .buttonStyle(.borderless)

                            Spacer()

                            Menu {
                                if isLoadingFeatures { Text("Loading features...") }
                                else if snippetFeatures.isEmpty { Text("No snippet features available.") }
                                else {
                                    ForEach(snippetFeatures) { feature in
                                        Button(feature.name) {
                                            handleSnippetFeatureSelection(feature, section)
                                        }
                                    }
                                }
                            } label: {
                                Label("Process Snippet", systemImage: "wand.and.stars").font(.caption)
                            }
                            .buttonStyle(.bordered)
                            .disabled(isLoadingFeatures)

                            Button("Regenerate Content") {
                                handleFullSectionRegeneration(section)
                            }
                            .buttonStyle(.bordered).font(.caption)
                            .tint(currentPrimaryColor)

                            Button {
                                self.currentSectionIdForImageGen = section.id
                                self.imageGenPromptText = section.title
                                self.showingImagePromptModalForSection = true
                            } label: {
                                Label("Image", systemImage: "photo.badge.plus").font(.caption)
                            }
                            .buttonStyle(.bordered)
                        }
                        .padding(.top, 4)
                    }
                    .padding(.vertical, 8)
                } label: {
                    Text(section.title ?? "New Custom Section")
                        .font(currentFont.weight(.bold))
                        .foregroundColor(currentTextColor)
                }
                .padding(.bottom, 4)
                Divider()
            }
            Button(action: addCampaignCustomSection) {
                Label("Add Custom Section", systemImage: "plus.circle.fill")
            }
            .buttonStyle(.bordered)
            .tint(currentPrimaryColor)
        }
        .padding(.top, 8)
    }
}
