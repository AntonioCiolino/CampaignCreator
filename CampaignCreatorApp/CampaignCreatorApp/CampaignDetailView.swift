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

    @State private var showingExportSheet = false
    @State private var exportedMarkdown = ""

    @State private var titleDebounceTimer: Timer?

    // For generating temporary client-side IDs for new sections
    @State private var nextTemporaryClientSectionID: Int = -1

    init(campaign: Campaign, campaignCreator: CampaignCreator) {
        self._campaign = State(initialValue: campaign)
        self._campaignCreator = ObservedObject(wrappedValue: campaignCreator)
        self._editableTitle = State(initialValue: campaign.title)
        self._editableConcept = State(initialValue: campaign.concept ?? "")
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // MARK: - Header and Title
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
                                Label("Generate", systemImage: "sparkles")
                            }
                            .buttonStyle(.borderedProminent).disabled(isSaving || isGeneratingText)

                            Button(action: { exportCampaignContent() }) {
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
                            titleDebounceTimer?.invalidate()
                            titleDebounceTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: false) { _ in
                                Task { await saveCampaignDetails(source: .titleField) }
                            }
                        }
                }
                .padding().background(Color(.systemGroupedBackground)).cornerRadius(12)

                // MARK: - Concept Editor
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Campaign Concept")
                            .font(.headline)
                        Spacer()
                        Button(isEditingConcept ? "Done" : "Edit") {
                            isEditingConcept.toggle()
                            if !isEditingConcept {
                                Task { await saveCampaignDetails(source: .conceptEditorDoneButton) }
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
                .padding().background(Color(.systemBackground)).cornerRadius(12)

                // MARK: - Sections Placeholder
                VStack(alignment: .leading) {
                    Text("Sections").font(.headline)
                    // TODO: Implement section listing and editing here
                    if campaign.sections.isEmpty {
                        Text("No sections yet. Use 'Generate' to create the first section from a prompt.")
                            .font(.subheadline).foregroundColor(.secondary).padding()
                            .frame(maxWidth: .infinity, alignment: .center)
                            .background(Color(.systemGroupedBackground)).cornerRadius(8)
                    } else {
                        ForEach(campaign.sections) { section in
                            SectionBox(title: section.title ?? "Untitled Section (\(section.order))") {
                                Text(section.content.prefix(200) + (section.content.count > 200 ? "..." : ""))
                                    .font(.body)
                                    .lineLimit(5)
                            }
                        }
                    }
                }
                .padding()
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
        .sheet(isPresented: $showingExportSheet) {
            exportSheetView
        }
    }

    private func generateTemporaryClientSectionID() -> Int {
        let tempID = nextTemporaryClientSectionID
        nextTemporaryClientSectionID -= 1
        return tempID
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
        displayTOC: [ // Example TOC with Int IDs
            TOCEntry(id: 201, title: "Introduction", type: "Introduction"),
            TOCEntry(id: 202, title: "Chapter 1 Link", type: "Chapter")
        ]
    )
    // campaignCreator.campaigns = [sampleCampaign] // If needed for preview consistency

    return NavigationView {
        CampaignDetailView(campaign: sampleCampaign, campaignCreator: campaignCreator)
    }
}