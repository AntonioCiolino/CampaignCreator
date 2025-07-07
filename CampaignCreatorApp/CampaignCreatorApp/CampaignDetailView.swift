import SwiftUI
import CampaignCreatorLib

struct CampaignDetailView: View {
    @State var campaign: Campaign
    @ObservedObject var campaignCreator: CampaignCreator

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
    @State private var showingThemeEditSheet = false // New state for theme edit sheet

    @State private var titleDebounceTimer: Timer?

    // For generating temporary client-side IDs for new sections
    @State private var nextTemporaryClientSectionID: Int = -1
    @State private var localCampaignCustomSections: [CampaignCustomSection] // ADDED
    @State private var customTextViewCoordinators: [UUID: CustomTextView.Coordinator] = [:] // ADDED for snippet ops
    @State private var snippetFeatures: [Feature] = [] // ADDED for snippet features
    @State private var isLoadingFeatures: Bool = false // ADDED
    private let featureService = FeatureService() // ADDED

    // State for Snippet Context Modal
    @State private var showingContextModal: Bool = false
    @State private var currentFeatureForModal: Feature? = nil
    @State private var currentSectionIdForModal: UUID? = nil // To know which section's coordinator to use
    @State private var currentSelectedTextForModal: String = ""

    // State for Image Generation Modal for sections
    @State private var showingImagePromptModalForSection: Bool = false
    @State private var currentSectionIdForImageGen: UUID? = nil
    @State private var imageGenPromptText: String = ""


    @Environment(\.horizontalSizeClass) var horizontalSizeClass

    private let sectionTypes = ["Generic", "NPC", "Character", "Location", "Item", "Quest", "Monster", "Chapter", "Note", "World Detail"]


    init(campaign: Campaign, campaignCreator: CampaignCreator) {
        self._campaign = State(initialValue: campaign)
        self._campaignCreator = ObservedObject(wrappedValue: campaignCreator)
        self._editableTitle = State(initialValue: campaign.title)
        self._editableConcept = State(initialValue: campaign.concept ?? "")
        self._localCampaignCustomSections = State(initialValue: campaign.customSections ?? []) // ADDED
    }

    // Helper to convert SwiftUI Font to UIFont (simplified)
    private func uiFontFrom(swiftUIFont: Font, defaultSize: CGFloat = 16) -> UIFont {
        // This is a simplified conversion. A full conversion is complex.
        // It currently relies on how `currentFont` is constructed.
        if let fontName = campaign.themeFontFamily, !fontName.isEmpty {
            return UIFont(name: fontName, size: defaultSize) ?? UIFont.systemFont(ofSize: defaultSize)
        }
        // Assuming .body maps to system font of defaultSize for this context
        return UIFont.systemFont(ofSize: defaultSize)
    }

    // Computed properties for theme colors
    private var currentPrimaryColor: Color { campaign.themePrimaryColor.map { Color(hex: $0) } ?? .accentColor }
    private var currentSecondaryColor: Color { campaign.themeSecondaryColor.map { Color(hex: $0) } ?? .secondary }
    private var currentBackgroundColor: Color { campaign.themeBackgroundColor.map { Color(hex: $0) } ?? Color(.systemBackground) }
    private var currentTextColor: Color { campaign.themeTextColor.map { Color(hex: $0) } ?? Color(.label) }
    private var currentFont: Font {
        if let fontName = campaign.themeFontFamily, !fontName.isEmpty {
            return .custom(fontName, size: 16) // Default size, can be made dynamic
        }
        return .body // Default system font
    }

    // MARK: - Extracted View Components for Body
    private var headerAndTitleSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading) {
                    Text("\(campaign.wordCount) words (from sections)")
                        .font(.caption).foregroundColor(.secondary)
                    Text(campaign.modifiedAt != nil ? "Modified: \(campaign.modifiedAt!, style: .date)" : "Modified: N/A")
                        .font(.caption).foregroundColor(.secondary)
                }
                Spacer()
                // ProgressView will be handled in toolbar or a more global status area if needed
            }

            TextField("Campaign Title", text: $editableTitle)
                .font(.largeTitle)
                .textFieldStyle(PlainTextFieldStyle())
                .padding(.bottom, 4)
                .disabled(isSaving || isGeneratingText)
                .onChange(of: editableTitle) { _ in
                    titleDebounceTimer?.invalidate()
                    titleDebounceTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: false) { _ in
                        Task { await self.saveCampaignDetails(source: .titleField) } // Added self.
                    }
                }
        }
        .padding().background(Color(.systemGroupedBackground)).cornerRadius(12)
        // Apply theme to specific text elements inside if needed, or globally if this section has distinct styling.
        // For now, relying on global theme application or default system styles for this section.
    }

    private var conceptEditorSection: some View {
        DisclosureGroup("Campaign Concept", isExpanded: $isEditingConcept.animation()) { // Added animation for smoother toggle
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Spacer() // Pushes button to the right
                    Button(isEditingConcept ? "Done" : "Edit") {
                        isEditingConcept.toggle()
                        if !isEditingConcept { // Save when "Done" is tapped
                            Task { await self.saveCampaignDetails(source: .conceptEditorDoneButton) } // Added self.
                        }
                    }
                    .buttonStyle(.bordered).disabled(isSaving || isGeneratingText)
                    .tint(currentPrimaryColor) // Apply theme primary color
                }

                if isEditingConcept {
                    TextEditor(text: $editableConcept)
                        .frame(minHeight: 200, maxHeight: 400).padding(8)
                        .background(Color(.secondarySystemGroupedBackground)) // Use a slightly different background for editor
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(.systemGray4), lineWidth: 1))
                        .disabled(isSaving || isGeneratingText)
                } else {
                    Text(editableConcept.isEmpty ? "Tap Edit to add campaign concept..." : editableConcept)
                        .frame(maxWidth: .infinity, alignment: .leading).frame(minHeight: 100)
                        .padding().background(Color(.systemGroupedBackground)).cornerRadius(8) // Keep original background for display
                        .foregroundColor(editableConcept.isEmpty ? .secondary : currentTextColor) // Use theme text color
                        .onTapGesture { if !isSaving && !isGeneratingText { isEditingConcept = true } }
                }
            }
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12) // Keep original outer padding/bg
        .font(currentFont) // Apply theme font
    }

    private var tableOfContentsSection: some View {
        // Ensure this only appears if tocEntries are available and not empty
        // The conditional logic is kept in the main body for clarity of structure
        DisclosureGroup("Table of Contents") {
            VStack(alignment: .leading, spacing: 8) {
                // Ensure campaign.displayTOC is not nil before trying to iterate
                ForEach(campaign.displayTOC ?? []) { entry in
                    Text(entry.title)
                        .font(.body) // Can be themed with currentFont if desired, or kept as .body
                        // TODO: Add navigation to section
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 4)
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
        .foregroundColor(currentTextColor) // Apply theme text color
        .font(currentFont) // Apply theme font
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

                Button("Customize Theme") { // Caption updated
                    showingThemeEditSheet = true
                }
                .buttonStyle(.bordered)
                .tint(currentPrimaryColor) // Apply theme primary color
                .padding(.top, 8)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 4)
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
        .foregroundColor(currentTextColor) // Apply theme text color
        .font(currentFont) // Apply theme font
    }

    private var sectionsDisplaySection: some View {
        VStack(alignment: .leading) {
            Text("Sections")
                .font(currentFont.weight(.bold)) // Use theme font, make bold
                .foregroundColor(currentPrimaryColor) // Use theme primary color for header
                .padding(.bottom, 4)

            if campaign.sections.isEmpty {
                Text("No sections yet. Use 'Generate' to create the first section from a prompt.")
                    .font(currentFont.italic()) // Theme font, italic
                    .foregroundColor(currentTextColor.opacity(0.7)) // Theme text color, slightly muted
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .center)
                    .background(Color(.systemGroupedBackground)).cornerRadius(8)
            } else {
                ForEach(campaign.sections) { section in
                    DisclosureGroup { // Content of DisclosureGroup
                        Text(section.content.prefix(200) + (section.content.count > 200 ? "..." : ""))
                            .font(currentFont) // Apply theme font
                            .lineLimit(5)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.top, 4)
                    } label: { // Label of DisclosureGroup
                        Text(section.title ?? "Untitled Section (\(section.order))")
                            .font(currentFont.weight(.semibold)) // Theme font, semibold for title
                            .foregroundColor(currentTextColor) // Theme text color for title
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .padding() // Outer padding for the whole sections block
        // Note: Individual DisclosureGroup backgrounds/paddings might need adjustment
        // if they clash with the overall theme. For now, applying font/color broadly.
    }

    private func handleImageGenerationForSection() async {
        guard let sectionId = currentSectionIdForImageGen,
              let coordinator = customTextViewCoordinators[sectionId] else {
            print("Error: Missing section ID or coordinator for image generation.")
            // TODO: Show error to user
            return
        }

        let prompt = imageGenPromptText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !prompt.isEmpty else {
            print("Error: Image generation prompt is empty.")
            // TODO: Show error to user
            return
        }

        // Consider adding loading state indication for this specific section or globally
        print("Generating image for section \(sectionId) with prompt: \(prompt)")

        do {
            let response = try await campaignCreator.generateImageForSection(
                prompt: prompt,
                campaignId: Int(campaign.id) // Assuming campaign.id is Int
                // Add other params like model, size if UI allows configuring them
            )

            let markdownImage = "\n![Generated Image: \(response.promptUsed)](\(response.imageUrl))\n"
            coordinator.insertTextAtCurrentCursor(markdownImage)

            // Update local state if content was changed directly through coordinator
            // This ensures the change is reflected if the binding didn't immediately pick it up
            // or if save logic relies on localCampaignCustomSections being perfectly in sync.
            if let index = localCampaignCustomSections.firstIndex(where: { $0.id == sectionId }) {
                 // The coordinator's insertTextAtCurrentCursor already updated parent.text binding.
                 // So, localCampaignCustomSections[index].content should be up-to-date.
                 // If not, manual update would be needed:
                 // localCampaignCustomSections[index].content = coordinator.textView?.text ?? localCampaignCustomSections[index].content
            }

            // Save the campaign to persist the new content with the image link
            await self.saveCampaignDetails(source: .customSectionChange, includeCustomSections: true)
            print("Image generated and inserted for section \(sectionId).")

        } catch {
            print("Error generating image for section \(sectionId): \(error.localizedDescription)")
            // TODO: Show error to user (e.g., update a @State var bound to an alert for this modal or section)
        }

        // Reset state
        self.currentSectionIdForImageGen = nil
        self.imageGenPromptText = ""
    }

    private func handleSnippetFeatureSelection(_ feature: Feature, forSection section: CampaignCustomSection) {
        guard let coordinator = customTextViewCoordinators[section.id] else {
            print("Coordinator not found for section \(section.id) to process snippet feature '\(feature.name)'.")
            // Optionally show an alert to the user
            return
        }

        guard let selectedText = coordinator.getSelectedText(), !selectedText.isEmpty else {
            print("No text selected in section \(section.id) for snippet feature '\(feature.name)'.")
            // Optionally show an alert to the user to select text
            return
        }

        let currentRange = coordinator.getCurrentSelectedRange() // Keep this to know where to replace later
        print("Snippet Feature '\(feature.name)' selected for text: '\(selectedText)' in section \(section.id) at range \(currentRange)")

        let additionalRequiredContext = feature.requiredContext?.filter { $0 != "selected_text" && $0 != "campaign_characters" } ?? []

        if additionalRequiredContext.isEmpty {
            // No additional context needed, proceed to (placeholder) LLM call
            print("No additional context required for feature '\(feature.name)'. Calling placeholder process.")
            // Placeholder for Step 4.D (Full LLM Interaction)
            // For now, simulate by replacing text.
            // This will eventually call a method that takes `feature`, `selectedText`, `section.id`, `currentRange`, and empty context.
            processSnippetWithLLM(feature: feature, sectionId: section.id, selectedText: selectedText, rangeToReplace: currentRange, additionalContext: [:])

        } else {
            // Additional context required, show modal
            print("Additional context required for feature '\(feature.name)': \(additionalRequiredContext). Showing modal.")
            self.currentFeatureForModal = feature
            self.currentSectionIdForModal = section.id
            self.currentSelectedTextForModal = selectedText
            // self.currentSelectionRangeForModal = currentRange // Store this if modal needs to pass it back for replacement
            self.showingContextModal = true
        }
    }

    private func handleFullSectionRegeneration(forSection section: CampaignCustomSection) {
        guard let coordinator = customTextViewCoordinators[section.id] else {
            print("Error: Coordinator not found for section \(section.id) for full regeneration.")
            // TODO: Show error to user
            return
        }

        // Determine the prompt: use selected text if any, otherwise the whole current content.
        let selectedText = coordinator.getSelectedText()
        let currentFullText = section.content // Use the bound content from localCampaignCustomSections

        let promptForRegeneration = selectedText ?? currentFullText // If text is selected, it's a hint/focus. Otherwise, use current content.

        Task {
            let payload = SectionRegeneratePayload(
                newPrompt: promptForRegeneration,
                newTitle: section.title,
                sectionType: section.type,
                modelIdWithPrefix: campaign.selectedLLMId, // Use campaign's selected LLM
                featureId: nil, // No specific feature for full regeneration
                contextData: selectedText != nil ? ["user_instructions": selectedText!] : nil // Pass selected text as user_instructions if it exists
            )

            do {
                print("Calling CampaignCreator to regenerate FULL content for section \(section.id)...")
                let updatedSectionData = try await campaignCreator.regenerateCampaignCustomSection(
                    campaignId: Int(campaign.id),
                    sectionId: section.id,
                    payload: payload
                )

                // Replace ENTIRE text in the CustomTextView
                // To do this via coordinator, it might need a `setText` method, or we update binding.
                // Forcing binding update:
                if let index = localCampaignCustomSections.firstIndex(where: { $0.id == section.id }) {
                    localCampaignCustomSections[index].content = updatedSectionData.content
                    // If the backend could also change title/type during full regeneration:
                    // localCampaignCustomSections[index].title = updatedSectionData.title
                    // localCampaignCustomSections[index].type = updatedSectionData.type
                }
                // The CustomTextView will update via its @Binding text.

                await self.saveCampaignDetails(source: .customSectionChange, includeCustomSections: true)
                print("Full section content regeneration successful for section \(section.id).")

            } catch {
                print("Error regenerating full section content for section \(section.id): \(error.localizedDescription)")
                // TODO: Show error to user
            }
        }
    }

    // Placeholder for actual LLM call logic (Step 4.D)
    private func processSnippetWithLLM(feature: Feature, sectionId: UUID, selectedText: String, rangeToReplace: NSRange, additionalContext: [String: String]) {
        guard let coordinator = customTextViewCoordinators[sectionId] else {
            print("Error: Coordinator not found for section \(sectionId) during LLM processing.")
            // TODO: Show error to user
            return
        }

        // Get current section details to pass to payload
        guard let currentCampaignSection = localCampaignCustomSections.first(where: { $0.id == sectionId }) else {
            print("Error: Could not find current campaign section with ID \(sectionId) in local state.")
            return
        }

        Task {
            let payload = SectionRegeneratePayload(
                newPrompt: selectedText, // The selected text is the primary "prompt" for the snippet feature
                newTitle: currentCampaignSection.title,
                sectionType: currentCampaignSection.type,
                modelIdWithPrefix: campaign.selectedLLMId, // Use campaign's selected LLM
                featureId: feature.id,
                contextData: additionalContext.merging(["selected_text": selectedText]) { (_, new) in new } // Ensure selected_text is in context
            )

            do {
                print("Calling CampaignCreator to regenerate snippet for section \(sectionId), feature '\(feature.name)'...")
                let updatedSectionData = try await campaignCreator.regenerateCampaignCustomSection(
                    campaignId: Int(campaign.id), // Assuming campaign.id is Int
                    sectionId: sectionId,
                    payload: payload
                )

                // Replace text in the CustomTextView
                coordinator.replaceText(inRange: rangeToReplace, with: updatedSectionData.content)

                // Update localCampaignCustomSections to reflect the new content and potentially other changes from backend
                if let index = localCampaignCustomSections.firstIndex(where: { $0.id == sectionId }) {
                    localCampaignCustomSections[index].content = updatedSectionData.content
                    // If backend can change title/type during regeneration, update them too:
                    // localCampaignCustomSections[index].title = updatedSectionData.title
                    // localCampaignCustomSections[index].type = updatedSectionData.type
                }

                // The campaign itself in campaignCreator.campaigns list should have been updated by regenerateCampaignCustomSection.
                // We might need to re-sync `self.campaign` if `CampaignDetailView`'s copy is stale.
                // This is complex. For now, assume `saveCampaignDetails` after this will handle persisting the locally modified section.
                // Or, even better, `CampaignCreator.regenerateCampaignCustomSection` should ensure its published `campaigns` array is updated,
                // and `CampaignDetailView` should observe that.

                // Persist the changes made by the LLM (which updated local state via coordinator)
                await self.saveCampaignDetails(source: .customSectionChange, includeCustomSections: true)
                print("Snippet processing successful for feature '\(feature.name)'.")

            } catch {
                print("Error processing snippet with LLM for feature '\(feature.name)': \(error.localizedDescription)")
                // TODO: Show error to user (e.g., update a @State var bound to an alert)
            }
        }
    }

    private func fetchSnippetFeatures() async {
        isLoadingFeatures = true
        do {
            let allFeatures = try await featureService.fetchFeatures()
            // Filter for "Snippet" category or other relevant criteria if needed
            // For now, assuming all fetched features might be usable as snippets,
            // or the backend / featureService already filters appropriately.
            // The web UI filters for category 'Snippet' or specific non-campaign/TOC related names.
            self.snippetFeatures = allFeatures.filter {
                $0.featureCategory?.lowercased() == "snippet" ||
                ($0.featureCategory == nil && !["Campaign", "TOC Homebrewery", "TOC Display", "Campaign Names"].contains($0.name))
            }
            print("Fetched \(self.snippetFeatures.count) snippet features.")
        } catch {
            print("Error fetching snippet features: \(error.localizedDescription)")
            // Handle error display if necessary
        }
        isLoadingFeatures = false
    }

    // MARK: - Campaign Custom Sections Editor
    private var campaignCustomSectionsEditorView: some View {
        DisclosureGroup("Custom Campaign Sections") {
            VStack(alignment: .leading, spacing: 12) {
                ForEach($localCampaignCustomSections) { $section in // Use localCampaignCustomSections
                    VStack(alignment: .leading) {
                        TextField("Section Title", text: $section.title)
                            .font(currentFont.weight(.semibold)) // Use theme font
                            .textFieldStyle(PlainTextFieldStyle())
                            .padding(.bottom, 2)

                        Picker("Section Type", selection: $section.type.withDefault("Generic")) {
                            ForEach(sectionTypes, id: \.self) { typeName in
                                Text(typeName).tag(typeName)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                        .font(currentFont.caption) // Apply themed font, smaller size
                        .padding(.bottom, 4)

                        CustomTextView(
                            text: $section.content,
                            font: uiFontFrom(swiftUIFont: currentFont),
                            textColor: UIColor(currentTextColor),
                            onCoordinatorCreated: { coordinator in
                                customTextViewCoordinators[section.id] = coordinator
                            }
                        )
                            .frame(minHeight: 100, maxHeight: 300)
                            .background(Color(.secondarySystemGroupedBackground))
                            .cornerRadius(8)
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(.systemGray4), lineWidth: 1))

                        HStack { // Group Delete and Test Snippet buttons
                            Button("Delete Section") {
                                localCampaignCustomSections.removeAll { $0.id == section.id }
                                customTextViewCoordinators.removeValue(forKey: section.id) // Clean up coordinator
                                Task { await self.saveCampaignDetails(source: .customSectionChange, includeCustomSections: true) }
                            }
                            .foregroundColor(.red)
                            .buttonStyle(.borderless)

                            Spacer()

                            Menu {
                                if isLoadingFeatures {
                                    Text("Loading features...")
                                } else if snippetFeatures.isEmpty {
                                    Text("No snippet features available.")
                                } else {
                                    ForEach(snippetFeatures) { feature in
                                        Button(feature.name) {
                                            handleSnippetFeatureSelection(feature, forSection: section)
                                        }
                                    }
                                }
                            } label: {
                                Label("Process Snippet", systemImage: "wand.and.stars")
                                    .font(.caption) // Apply caption font to the label
                            }
                            .buttonStyle(.bordered)
                            // .font(.caption) // This on Menu might not style the internal label as expected, applied to Label directly.
                            .disabled(isLoadingFeatures)

                            Button("Regenerate Content") {
                                handleFullSectionRegeneration(forSection: section)
                            }
                            .buttonStyle(.bordered)
                            .font(.caption)
                            .tint(currentPrimaryColor) // Optional: theme it or use default

                            Button { // Generate Image Button
                                self.currentSectionIdForImageGen = section.id
                                self.imageGenPromptText = section.title ?? "" // Pre-fill with section title
                                self.showingImagePromptModalForSection = true
                            } label: {
                                Label("Image", systemImage: "photo.badge.plus")
                                   .font(.caption)
                            }
                            .buttonStyle(.bordered)
                        }
                        .padding(.top, 4)
                    }
                    .padding(.vertical, 8)
                    Divider()
                }
                Button(action: addCampaignCustomSection) {
                    Label("Add Custom Section", systemImage: "plus.circle.fill")
                }
                .buttonStyle(.bordered)
                .tint(currentPrimaryColor) // Use theme color
            }
            .padding(.top, 8)
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
        .foregroundColor(currentTextColor)
        .font(currentFont)
    }

    private func addCampaignCustomSection() {
        let newSection = CampaignCustomSection(title: "New Section", content: "")
        localCampaignCustomSections.append(newSection)
        // Optionally trigger save immediately or rely on user saving via other actions
        // Task { await self.saveCampaignDetails(source: .customSectionChange, includeCustomSections: true) }
    }


    var body: some View {
        ZStack { // Use ZStack for background image handling
            // Background Image (if URL is provided)
            if let bgImageURLString = campaign.themeBackgroundImageURL, let bgImageURL = URL(string: bgImageURLString) {
                AsyncImage(url: bgImageURL) { image in
                    image.resizable().aspectRatio(contentMode: .fill)
                } placeholder: {
                    Color.clear // Or a placeholder color/progress view
                }
                .opacity(campaign.themeBackgroundImageOpacity ?? 1.0)
                .edgesIgnoringSafeArea(.all)
            } else {
                // Apply background color only if no image, or if image fails to load and placeholder is clear
                currentBackgroundColor.edgesIgnoringSafeArea(.all)
            }

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Apply general text color and font to the content of the ScrollView
                    // Specific elements can override this.
                    headerAndTitleSection // Using the extracted component
                    conceptEditorSection // Using the extracted component

                // MARK: - Table of Contents
                if let tocEntries = campaign.displayTOC, !tocEntries.isEmpty {
                    tableOfContentsSection // Using the extracted component
                }
                campaignThemeDisplaySection // Using the extracted component
                campaignCustomSectionsEditorView // ADDED Campaign Custom Sections UI
                sectionsDisplaySection // Using the extracted component (standard generated sections)
            }
            .padding()
            .font(currentFont) // Apply default theme font to all content within VStack
            .foregroundColor(currentTextColor) // Apply default theme text color
        }
        .navigationTitle(editableTitle)
        .navigationBarTitleDisplayMode(.inline)
        .disabled(isSaving || isGeneratingText)
        .onAppear {
            Task {
                await fetchSnippetFeatures()
            }
        }
        .sheet(isPresented: $showingContextModal) {
            if let feature = currentFeatureForModal, let sectionId = currentSectionIdForModal {
                SnippetContextInputModal(
                    isPresented: $showingContextModal,
                    feature: feature,
                    campaignCharacters: campaignCreator.characters, // Pass actual characters
                    selectedText: currentSelectedTextForModal,
                    onSubmit: { contextData in
                        // User submitted context from modal, now call LLM processing
                        if let coordinator = customTextViewCoordinators[sectionId] {
                            let rangeToReplace = coordinator.getCurrentSelectedRange() // Re-fetch range, or pass it through state
                            processSnippetWithLLM(
                                feature: feature,
                                sectionId: sectionId,
                                selectedText: currentSelectedTextForModal, // Or re-fetch if selection could change while modal is up
                                rangeToReplace: rangeToReplace,
                                additionalContext: contextData
                            )
                        } else {
                             print("Error: Coordinator disappeared while context modal was up for section \(sectionId).")
                        }
                    }
                )
            } else {
                // This should ideally not happen if state is set correctly before presentation
                Text("Error: Missing feature or section context for modal.")
                    .onAppear { showingContextModal = false } // Dismiss if error state
            }
        }
        .sheet(isPresented: $showingImagePromptModalForSection) {
            // Simple prompt modal for now
            NavigationView {
                VStack {
                    Text("Generate Image for Section")
                        .font(.headline)
                        .padding()
                    TextEditor(text: $imageGenPromptText)
                        .frame(height: 100)
                        .border(Color.gray)
                        .padding()

                    Button("Generate Image") {
                        Task {
                            await handleImageGenerationForSection()
                        }
                        showingImagePromptModalForSection = false
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(imageGenPromptText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    .padding()

                    Spacer()
                }
                .navigationTitle("Image Prompt")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button("Cancel") { showingImagePromptModalForSection = false }
                    }
                }
            }
        }
        .alert("Error", isPresented: $showErrorAlert) { // Generic error alert
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .onDisappear {
            titleDebounceTimer?.invalidate()
            if campaign.title != editableTitle || campaign.concept ?? "" != editableConcept {
                 Task { await saveCampaignDetails(source: .onDisappear) }
            }
        }
        // MARK: - Sheets
        .sheet(isPresented: $showingGenerateSheet) {
            generateSheetView
        }
        .sheet(isPresented: $showingGenerateImageSheet) { // New sheet modifier
            generateImageSheetView
        }
        .sheet(isPresented: $showingExportSheet) {
            exportSheetView
        }
        .sheet(isPresented: $showingThemeEditSheet) {
            CampaignThemeEditView(campaign: $campaign)
                .onDisappear {
                    // Changes to campaign theme are saved within CampaignThemeEditView's "Done" button.
                    // We might still need to trigger a broader save of the campaign object if
                    // the theme changes should also update the campaign's modifiedAt timestamp
                    // or if other side effects are needed.
                    // For now, assume CampaignThemeEditView handles its own persistence to the binding.
                    // If a specific save call is needed:
                    // Task { await saveCampaignDetails(source: .themeEditorDismissed) }
                    // However, saveCampaignDetails currently only saves title and concept.
                    // A more generic save or a specific theme save function might be needed on CampaignCreator.

                    // Let's make sure the main CampaignDetailView saves the campaign
                    // if theme properties were changed.
                    // We need to compare the campaign state before and after the sheet.
                    // This is tricky as the binding means `campaign` is already updated.
                    // A simple solution is to always mark as modified and save if the sheet was shown.
                    // More robust: check if any theme property actually changed.
                    // For now, a direct save call if the sheet was for theme editing.
                    print("Theme edit sheet dismissed. Campaign title: \(campaign.title)") // campaign is already updated due to @Binding
                    Task {
                        // We need a way to tell saveCampaignDetails to save *everything* or
                        // have a separate save for theme. Let's assume saveCampaignDetails
                        // should be smart enough or we add a specific theme save.
                        // For now, let's add a specific part to saveCampaignDetails for theme.
                        // This requires modifying saveCampaignDetails.
                        // Alternatively, call a specific save method on campaignCreator if available.
                         await saveCampaignDetails(source: .themeEditorDismissed, includeTheme: true)
                    }
                }
        }
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                if isSaving || isGeneratingText {
                    ProgressView()
                } else {
                    Button(action: { showingGenerateSheet = true }) {
                        Label("Generate Text", systemImage: "sparkles")
                    }
                    .disabled(isSaving || isGeneratingText)
                    .labelStyle(horizontalSizeClass == .compact ? .iconOnly : .automatic)

                    Button(action: { showingGenerateImageSheet = true }) {
                        Label("Generate Image", systemImage: "photo")
                    }
                    .disabled(isSaving || isGeneratingText)
                    .labelStyle(horizontalSizeClass == .compact ? .iconOnly : .automatic)

                    Button(action: { exportCampaignContent() }) {
                        Label("Export", systemImage: "square.and.arrow.up")
                    }
                    .disabled(isSaving || isGeneratingText)
                    .labelStyle(horizontalSizeClass == .compact ? .iconOnly : .automatic)
                }
            }
        }
        .onChange(of: horizontalSizeClass) { newSizeClass in
            // This is mostly for debugging or if specific non-label-style changes were needed.
            // .labelStyle modifier handles the change automatically.
            print("Horizontal size class changed to: \(String(describing: newSizeClass))")
        }
    }

    @ViewBuilder
    private var commonToolbarButtons: some View {
        // This approach allows for dynamic labelStyle but might be overly complex
        // if .labelStyle(.iconOnly) on the button itself works well with @Environment.
        // Sticking to simpler individual button modifiers for now.
        EmptyView()
    }

    private func generateTemporaryClientSectionID() -> Int {
        let tempID = nextTemporaryClientSectionID
        nextTemporaryClientSectionID -= 1
        return tempID
    }

    // MARK: - Image Generation Logic (Campaign Thematic Image)
    private var generateImageSheetView: some View {
        NavigationView {
            VStack(spacing: 20) {
                Text("AI Image Generation").font(.headline)
                Text("Describe the thematic image you'd like to generate for your campaign.")
                    .font(.subheadline).foregroundColor(.secondary)
                TextEditor(text: $imageGeneratePrompt)
                    .frame(height: 120).padding(8)
                    .background(Color(.systemGroupedBackground)).cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(.systemGray4), lineWidth: 1))

                if let error = imageGenerationError { Text(error).foregroundColor(.red).font(.caption) }
                Spacer()
                Button(action: { Task { await performAICampaignImageGeneration() } }) {
                    HStack {
                        // Assuming isGeneratingText can be reused or a new @State isGeneratingImage exists
                        if isGeneratingText { ProgressView().progressViewStyle(.circular).tint(.white) }
                        Text(isGeneratingText ? "Generating..." : "Generate Thematic Image")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(imageGeneratePrompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isGeneratingText)
            }
            .padding()
            .navigationTitle("Generate Image").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { showingGenerateImageSheet = false; imageGeneratePrompt = ""; imageGenerationError = nil }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }

    private func performAICampaignImageGeneration() async {
        guard !imageGeneratePrompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        // Use a separate state for image generation progress if text generation can happen concurrently
        // For now, reusing isGeneratingText for simplicity, assuming modal operation.
        isGeneratingText = true // Or a new @State isGeneratingImage = true
        imageGenerationError = nil

        do {
            // Placeholder for actual image generation call
            // let imageURL = try await campaignCreator.generateCampaignImage(campaignId: campaign.id, prompt: imageGeneratePrompt)
            // For now, simulate a delay and a fake URL
            try await Task.sleep(nanoseconds: 2_000_000_000) // Simulate network request
            let simulatedImageURL = "https://picsum.photos/seed/\(UUID().uuidString)/600/400"

            var campaignToUpdate = self.campaign
            campaignToUpdate.thematicImageURL = simulatedImageURL
            campaignToUpdate.thematicImagePrompt = imageGeneratePrompt // Save the prompt used
            campaignToUpdate.markAsModified()

            try await campaignCreator.updateCampaign(campaignToUpdate)

            if let refreshedCampaign = campaignCreator.campaigns.first(where: { $0.id == campaignToUpdate.id }) {
                self.campaign = refreshedCampaign
                self.editableTitle = refreshedCampaign.title
                self.editableConcept = refreshedCampaign.concept ?? ""
            }

            showingGenerateImageSheet = false
            imageGeneratePrompt = ""
            print("Simulated campaign image generated and campaign updated.")

        } catch let error as APIError {
            imageGenerationError = "Failed to save campaign with new image: \(error.localizedDescription)"
            print("❌ API Error saving campaign after image generation: \(error.localizedDescription)")
        } catch {
            imageGenerationError = "An unexpected error occurred: \(error.localizedDescription)"
            print("❌ Unexpected error during campaign image generation: \(error.localizedDescription)")
        }
        isGeneratingText = false // Or isGeneratingImage = false
    }

    // MARK: - Save Logic
    enum SaveSource { case titleField, conceptEditorDoneButton, onDisappear, themeEditorDismissed, customSectionChange } // Added customSectionChange
    private func saveCampaignDetails(source: SaveSource, includeTheme: Bool = false, includeCustomSections: Bool = false) async { // Added includeCustomSections
        guard !isSaving else { print("Save already in progress from source: \(source). Skipping."); return }

        // It's important to use a fresh copy of `self.campaign` for comparison
        // if the binding was already updated by a sub-view (like CampaignThemeEditView).
        // However, for title and concept, editableTitle and editableConcept are the source of truth.
        // For theme, campaign itself IS the source of truth due to @Binding.

        var campaignToUpdate = self.campaign // Use the @State campaign as the source of truth for theme properties.
                                         // For title/concept, we compare against editable fields.
        var changed = false
        if campaignToUpdate.title != editableTitle {
            campaignToUpdate.title = editableTitle
            changed = true
        }
        let conceptToSave = editableConcept.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        if campaignToUpdate.concept != conceptToSave {
             campaignToUpdate.concept = conceptToSave
             changed = true
        }

        if includeTheme {
            // If includeTheme is true, we assume theme data might have changed.
            // The `campaignToUpdate` already reflects these changes due to @Binding.
            // We just need to ensure 'changed' is true so the save proceeds.
            // A more robust check would compare current theme values to original ones
            // if we had stored them before opening the theme editor.
            // For now, if source is themeEditorDismissed, we force a save.
            if source == .themeEditorDismissed {
                print("Theme editor dismissed, marking campaign as changed for saving theme properties.")
                changed = true
            }
            // Note: campaignToUpdate already has the latest theme values from the binding.
            // No need to explicitly copy them here again.
        }

        if includeCustomSections {
            // Filter out any completely empty custom sections before saving
            let sectionsToSave = localCampaignCustomSections.filter {
                !$0.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
                !$0.content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            }
            // Check if the custom sections have actually changed compared to the campaign's current state.
            // This is a bit more complex due to array of objects. A simpler check for now:
            // If includeCustomSections is true, we'll update the campaign object with the current localCustomSections.
            // The `changed` flag will be set if this assignment actually alters campaignToUpdate.customSections.
            // This requires CampaignCustomSection to be Equatable for an exact comparison,
            // or we rely on other parts of 'changed' logic or always save if includeCustomSections is true.
            // For now, if includeCustomSections is true, we will assign and mark as changed.
            // This is simpler than a deep comparison here.
            let sectionsToSave = localCampaignCustomSections.filter {
                !$0.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
                !$0.content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            }
            campaignToUpdate.customSections = sectionsToSave.isEmpty ? nil : sectionsToSave
            // We need to ensure 'changed' is true if custom sections were part of the trigger.
            // The most straightforward way is if the source indicates it, or if `includeCustomSections` was passed as true.
            if source == .customSectionChange || includeCustomSections { // If called with this intent, assume changes.
                changed = true
                print("Custom sections included in save operation.")
            }
        }

        guard changed else { print("No changes to save from source: \(source)."); return }

        isSaving = true
        errorMessage = ""
        campaignToUpdate.markAsModified()

        do {
            try await campaignCreator.updateCampaign(campaignToUpdate)
            // After successful save, campaignCreator.campaigns will be updated (if fetchCampaigns is called in updateCampaign)
            // We should refresh our local @State campaign from that source
            if let refreshedCampaign = campaignCreator.campaigns.first(where: { $0.id == campaignToUpdate.id }) {
                self.campaign = refreshedCampaign // This updates the view
                // Re-sync editable fields if they were out of sync or if server transformed data
                self.editableTitle = refreshedCampaign.title
                self.editableConcept = refreshedCampaign.concept ?? ""
                self.localCampaignCustomSections = refreshedCampaign.customSections ?? [] // Re-sync custom sections
            } else {
                 self.campaign = campaignToUpdate // Fallback, should ideally find it
                 // If falling back, ensure localCampaignCustomSections reflects campaignToUpdate
                 self.localCampaignCustomSections = campaignToUpdate.customSections ?? []
            }
            print("Campaign details saved successfully via \(source).")
        } catch let error as APIError {
            errorMessage = "Save failed: \(error.localizedDescription)"
            showErrorAlert = true
            print("❌ Error saving campaign: \(errorMessage)")
        } catch {
            errorMessage = "Save failed: An unexpected error occurred: \(error.localizedDescription)"
            showErrorAlert = true
            print("❌ Unexpected error saving campaign: \(errorMessage)")
        }
        isSaving = false
    }

    // MARK: - AI Generation Logic
    private var generateSheetView: some View {
        NavigationView {
            VStack(spacing: 20) {
                Text("AI Text Generation").font(.headline)
                Text("Describe what you'd like to generate. This will create a new section in your campaign.")
                    .font(.subheadline).foregroundColor(.secondary)
                TextEditor(text: $generatePrompt)
                    .frame(height: 120).padding(8)
                    .background(Color(.systemGroupedBackground)).cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(.systemGray4), lineWidth: 1))

                if let error = generationError { Text(error).foregroundColor(.red).font(.caption) }
                Spacer()
                Button(action: { Task { await performAIGeneration() } }) {
                    HStack {
                        if isGeneratingText { ProgressView().progressViewStyle(.circular).tint(.white) }
                        Text(isGeneratingText ? "Generating..." : "Generate New Section")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(generatePrompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isGeneratingText)
            }
            .padding()
            .navigationTitle("Generate Content").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { showingGenerateSheet = false; generatePrompt = ""; generationError = nil }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }

    private func performAIGeneration() async {
        guard !generatePrompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        isGeneratingText = true
        generationError = nil

        do {
            let generatedText = try await campaignCreator.generateText(prompt: generatePrompt)

            var updatedCampaign = self.campaign
            let newSection = CampaignSection(
                id: generateTemporaryClientSectionID(), // Use temporary negative ID
                title: generatePrompt.prefix(50) + (generatePrompt.count > 50 ? "..." : ""), // Use prompt as title
                content: generatedText,
                order: (updatedCampaign.sections.map(\.order).max() ?? -1) + 1 // Ensure new section is last
            )
            updatedCampaign.sections.append(newSection)
            updatedCampaign.markAsModified()

            try await campaignCreator.updateCampaign(updatedCampaign) // Save campaign with new section

            // Refresh local state from campaignCreator's published list
            if let refreshedCampaign = campaignCreator.campaigns.first(where: { $0.id == updatedCampaign.id }) {
                self.campaign = refreshedCampaign
                self.editableTitle = refreshedCampaign.title // Resync in case title was part of update
                self.editableConcept = refreshedCampaign.concept ?? ""
            }

            showingGenerateSheet = false
            generatePrompt = ""
        } catch let error as LLMError {
            generationError = error.localizedDescription
            print("❌ LLM Generation failed: \(error.localizedDescription)")
        } catch let error as APIError {
            generationError = "Failed to save new section: \(error.localizedDescription)"
            print("❌ API Error saving generated section: \(error.localizedDescription)")
        } catch {
            generationError = "An unexpected error occurred: \(error.localizedDescription)"
            print("❌ Unexpected error during/after generation: \(error.localizedDescription)")
        }
        isGeneratingText = false
    }

    // MARK: - Export Logic
    private var exportSheetView: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Homebrewery Export").font(.headline)
                    Text("Your campaign has been converted to Homebrewery-compatible markdown:").font(.subheadline).foregroundColor(.secondary)
                    Text(exportedMarkdown).font(.system(.body, design: .monospaced)).padding()
                        .background(Color(.systemGroupedBackground)).cornerRadius(8)
                    Button("Copy to Clipboard") { UIPasteboard.general.string = exportedMarkdown }
                        .buttonStyle(.borderedProminent).frame(maxWidth: .infinity)
                }.padding()
            }
            .navigationTitle("Export").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .navigationBarTrailing) { Button("Done") { showingExportSheet = false } } }
        }
    }

    private func exportCampaignContent() {
        exportedMarkdown = campaignCreator.exportCampaignToHomebrewery(campaign)
        showingExportSheet = true
    }
}

#Preview {
    let campaignCreator = CampaignCreator()
    // Ensure all model instantiations have their required 'id: Int'
    let sampleCampaign = Campaign(
        id: 1, // Correct: Campaign ID is Int
        title: "My Preview Saga",
        concept: "A test concept.",
        displayTOC: [ // Corrected order: displayTOC before sections
            TOCEntry(id: 201, title: "Introduction", type: "Introduction"),
            TOCEntry(id: 202, title: "Chapter 1 Link", type: "Chapter")
        ],
        sections: [
            CampaignSection(
                id: 101, // Correct: CampaignSection ID is Int
                title: "Intro",
                content: "This is the intro section.",
                order: 0
            ),
            CampaignSection(
                id: 102, // Correct: CampaignSection ID is Int
                title: "Chapter 1",
                content: "Content for chapter 1.",
                order: 1
            )
        ],
        themePrimaryColor: "#FF0000",
        themeFontFamily: "Arial",
        customSections: [ // ADDED Sample Campaign Custom Sections
            CampaignCustomSection(title: "World History", content: "A brief history of the world..."),
            CampaignCustomSection(title: "Key Factions", content: "Details about important groups...")
        ]
    )
    // campaignCreator.campaigns = [sampleCampaign] // If needed for preview consistency

    NavigationView { // Removed explicit 'return'
        CampaignDetailView(campaign: sampleCampaign, campaignCreator: campaignCreator)
    }
}


// Helper view for displaying theme properties
struct ThemePropertyRow: View {
    let label: String
    let value: String?
    var isURL: Bool = false

    var body: some View {
        HStack {
            Text(label + ":")
                .font(.caption)
                .fontWeight(.medium)
            if let val = value, !val.isEmpty {
                if isURL, let url = URL(string: val) {
                    Link(val, destination: url)
                        .font(.caption)
                        .lineLimit(1)
                } else {
                    Text(val)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            } else {
                Text("Not set")
                    .font(.caption)
                    .italic()
                    .foregroundColor(.gray)
            }
            Spacer() // Pushes content to the left
        }
    }
}
