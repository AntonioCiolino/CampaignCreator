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

    @State private var titleDebounceTimer: Timer?

    // For generating temporary client-side IDs for new sections
    @State private var nextTemporaryClientSectionID: Int = -1

    init(campaign: Campaign, campaignCreator: CampaignCreator) {
        self._campaign = State(initialValue: campaign)
        self._campaignCreator = ObservedObject(wrappedValue: campaignCreator)
        self._editableTitle = State(initialValue: campaign.title)
        self._editableConcept = State(initialValue: campaign.concept ?? "")
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

                Button("Edit Theme") {
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

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                CampaignHeaderView(
                    campaign: campaign,
                    editableTitle: $editableTitle,
                    isSaving: isSaving,
                    isGeneratingText: isGeneratingText,
                    showingGenerateSheet: $showingGenerateSheet,
                    showingGenerateImageSheet: $showingGenerateImageSheet,
                    exportCampaignContent: exportCampaignContent,
                    saveTitleAction: {
                        // Debounce logic moved here or called from here
                        titleDebounceTimer?.invalidate()
                        titleDebounceTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: false) { _ in
                            Task { await saveCampaignDetails(source: .titleField) }
                        }
                    }
                )

                CampaignConceptView(
                    editableConcept: $editableConcept,
                    isEditingConcept: $isEditingConcept,
                    isSaving: isSaving,
                    isGeneratingText: isGeneratingText,
                    saveConceptAction: {
                        Task { await saveCampaignDetails(source: .conceptEditorDoneButton) }
                    }
                )

                // MARK: - Table of Contents
                if let tocEntries = campaign.displayTOC, !tocEntries.isEmpty {
                    CampaignTableOfContentsView(tocEntries: tocEntries)
                }

                CampaignThemeDisplayView(
                    campaign: campaign,
                    errorMessage: $errorMessage,
                    showErrorAlert: $showErrorAlert
                )

                CampaignSectionsListView(campaign: campaign)
            }
            .padding()
        }
        .navigationTitle(editableTitle)
        .navigationBarTitleDisplayMode(.inline)
        .disabled(isSaving || isGeneratingText)
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
    enum SaveSource { case titleField, conceptEditorDoneButton, onDisappear }
    private func saveCampaignDetails(source: SaveSource) async {
        guard !isSaving else { print("Save already in progress from source: \(source). Skipping."); return }

        var campaignToUpdate = campaign // Use the @State campaign as the source
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
            } else {
                 self.campaign = campaignToUpdate // Fallback, should ideally find it
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

struct CampaignSectionsListView: View {
    let campaign: Campaign

    var body: some View {
        VStack(alignment: .leading) {
            Text("Sections").font(.headline)
            if campaign.sections.isEmpty {
                Text("No sections yet. Use 'Generate' to create the first section from a prompt.")
                    .font(.subheadline).foregroundColor(.secondary).padding()
                    .frame(maxWidth: .infinity, alignment: .center)
                    .background(Color(.systemGroupedBackground)).cornerRadius(8)
            } else {
                ForEach(campaign.sections) { section in
                    DisclosureGroup(section.title ?? "Untitled Section (\(section.order))") {
                        Text(section.content.prefix(200) + (section.content.count > 200 ? "..." : ""))
                            .font(.body)
                            .lineLimit(5)
                            .frame(maxWidth: .infinity, alignment: .leading) // Ensure text aligns left
                            .padding(.top, 4) // Add some padding below the DisclosureGroup title
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .padding()
    }
}

struct CampaignThemeDisplayView: View {
    let campaign: Campaign
    @Binding var errorMessage: String
    @Binding var showErrorAlert: Bool

    var body: some View {
        DisclosureGroup("Campaign Theme") {
            VStack(alignment: .leading, spacing: 8) {
                ThemePropertyRow(label: "Primary Color", value: campaign.themePrimaryColor)
                ThemePropertyRow(label: "Secondary Color", value: campaign.themeSecondaryColor)
                ThemePropertyRow(label: "Background Color", value: campaign.themeBackgroundColor)
                ThemePropertyRow(label: "Text Color", value: campaign.themeTextColor)
                ThemePropertyRow(label: "Font Family", value: campaign.themeFontFamily)
                ThemePropertyRow(label: "Background Image URL", value: campaign.themeBackgroundImageURL, isURL: true)
                ThemePropertyRow(label: "BG Image Opacity", value: campaign.themeBackgroundImageOpacity.map { String(format: "%.2f", $0) })

                Button("Edit Theme (Placeholder)") {
                    // TODO: Implement theme editing
                    print("Edit Theme button tapped - functionality not yet implemented.")
                    errorMessage = "Theme editing is not yet implemented."
                    showErrorAlert = true
                }
                .buttonStyle(.bordered)
                .padding(.top, 8)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 4)
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
    }
}

struct CampaignTableOfContentsView: View {
    let tocEntries: [TOCEntry]

    var body: some View {
        DisclosureGroup("Table of Contents") {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(tocEntries) { entry in
                    Text(entry.title)
                        .font(.body)
                        // TODO: Add navigation to section
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 4)
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
    }
}

// MARK: - Extracted Subviews

struct CampaignHeaderView: View {
    let campaign: Campaign
    @Binding var editableTitle: String
    let isSaving: Bool
    let isGeneratingText: Bool
    @Binding var showingGenerateSheet: Bool
    @Binding var showingGenerateImageSheet: Bool
    let exportCampaignContent: () -> Void
    let saveTitleAction: () -> Void // For debounced save

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading) {
                    Text("\(campaign.wordCount) words (from sections)")
                        .font(.caption).foregroundColor(.secondary)
                    Text(campaign.modifiedAt != nil ? "Modified: \(campaign.modifiedAt!, style: .date)" : "Modified: N/A")
                        .font(.caption).foregroundColor(.secondary)
                }
                Spacer()
                if isSaving || isGeneratingText { // Show progress if saving or generating
                    ProgressView().padding(.trailing, 5)
                }
                // Action buttons
                HStack(spacing: 12) {
                    Button(action: { showingGenerateSheet = true }) {
                        Label("Text", systemImage: "sparkles")
                    }
                    .buttonStyle(.borderedProminent).disabled(isSaving || isGeneratingText)

                    Button(action: { showingGenerateImageSheet = true }) {
                        Label("Image", systemImage: "photo")
                    }
                    .buttonStyle(.bordered).disabled(isSaving || isGeneratingText)

                    Button(action: exportCampaignContent) {
                        Label("Export", systemImage: "square.and.arrow.up")
                    }
                    .buttonStyle(.bordered).disabled(isSaving || isGeneratingText)
                }
            }

            TextField("Campaign Title", text: $editableTitle)
                .font(.largeTitle)
                .textFieldStyle(PlainTextFieldStyle())
                .padding(.bottom, 4)
                .disabled(isSaving || isGeneratingText)
                .onChange(of: editableTitle) { _ in
                    saveTitleAction() // Call the debounced save action
                }
        }
        .padding().background(Color(.systemGroupedBackground)).cornerRadius(12)
    }
}

struct CampaignConceptView: View {
    @Binding var editableConcept: String
    @Binding var isEditingConcept: Bool
    let isSaving: Bool
    let isGeneratingText: Bool
    let saveConceptAction: () async -> Void

    var body: some View {
        DisclosureGroup("Campaign Concept", isExpanded: $isEditingConcept) {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Spacer() // Pushes button to the right
                    Button(isEditingConcept ? "Done" : "Edit") {
                        isEditingConcept.toggle()
                        if !isEditingConcept {
                            Task { await saveConceptAction() }
                        }
                    }
                    .buttonStyle(.bordered).disabled(isSaving || isGeneratingText)
                }

                if isEditingConcept {
                    TextEditor(text: $editableConcept)
                        .frame(minHeight: 200, maxHeight: 400).padding(8)
                        .background(Color(.systemBackground)).cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(.systemGray4), lineWidth: 1))
                        .disabled(isSaving || isGeneratingText)
                } else {
                    Text(editableConcept.isEmpty ? "Tap Edit to add campaign concept..." : editableConcept)
                        .frame(maxWidth: .infinity, alignment: .leading).frame(minHeight: 100)
                        .padding().background(Color(.systemGroupedBackground)).cornerRadius(8)
                        .foregroundColor(editableConcept.isEmpty ? .secondary : .primary)
                        .onTapGesture { if !isSaving && !isGeneratingText { isEditingConcept = true } }
                }
            }
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
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
        themeFontFamily: "Arial"
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
