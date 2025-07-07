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

    @Environment(\.horizontalSizeClass) var horizontalSizeClass

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
                        Task { await saveCampaignDetails(source: .titleField) }
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
                            Task { await saveCampaignDetails(source: .conceptEditorDoneButton) }
                        }
                    }
                    .buttonStyle(.bordered).disabled(isSaving || isGeneratingText)
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
                sectionsDisplaySection // Using the extracted component
            }
            .padding()
            .font(currentFont) // Apply default theme font to all content within VStack
            .foregroundColor(currentTextColor) // Apply default theme text color
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
    enum SaveSource { case titleField, conceptEditorDoneButton, onDisappear, themeEditorDismissed } // Added themeEditorDismissed
    private func saveCampaignDetails(source: SaveSource, includeTheme: Bool = false) async { // Added includeTheme
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
