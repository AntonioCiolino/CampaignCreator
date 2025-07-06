import SwiftUI
import CampaignCreatorLib // Ensure this import points to your actual library

struct CampaignDetailView: View {
    @State var campaign: Campaign // Use @State if you need to modify it directly and have UI update
    let campaignCreator: CampaignCreator // To save changes

    // State for editing title and concept
    @State private var editableTitle: String
    @State private var editableConcept: String

    @State private var isEditingConcept = false

    // TODO: Re-integrate AI generation and export when section editing is clearer
    @State private var showingGenerateSheet = false
    @State private var generatePrompt = ""
    @State private var isGenerating = false
    @State private var generationError: String?
    @State private var showingExportSheet = false
    @State private var exportedMarkdown = ""

    init(campaign: Campaign, campaignCreator: CampaignCreator) {
        self._campaign = State(initialValue: campaign)
        self.campaignCreator = campaignCreator
        self._editableTitle = State(initialValue: campaign.title)
        self._editableConcept = State(initialValue: campaign.concept ?? "")
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Campaign Info Header (Simplified for now)
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        VStack(alignment: .leading) {
                            // Display word count from campaign.wordCount
                            Text("\(campaign.wordCount) words (from sections)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text("Modified: \(campaign.modifiedAt, style: .date)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        // Action buttons (Generate/Export - to be re-enabled later)
                        /*
                        HStack(spacing: 12) {
                            Button(action: { showingGenerateSheet = true }) {
                                Label("Generate", systemImage: "sparkles")
                            }
                            .buttonStyle(.borderedProminent)

                            Button(action: { exportCampaignContent() }) {
                                Label("Export", systemImage: "square.and.arrow.up")
                            }
                            .buttonStyle(.bordered)
                        }
                        */
                    }
                     // Editable Title
                    TextField("Campaign Title", text: $editableTitle, onCommit: saveCampaignDetails)
                        .font(.largeTitle)
                        .textFieldStyle(PlainTextFieldStyle()) // Or any style you prefer
                        .padding(.bottom, 4)


                }
                .padding()
                .background(Color(.systemGroupedBackground))
                .cornerRadius(12)

                // Concept Editor
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Campaign Concept")
                            .font(.headline)
                        Spacer()
                        Button(isEditingConcept ? "Done" : "Edit") {
                            if isEditingConcept {
                                saveCampaignDetails() // Save when "Done" is tapped
                            }
                            isEditingConcept.toggle()
                        }
                        .buttonStyle(.bordered)
                    }

                    if isEditingConcept {
                        TextEditor(text: $editableConcept)
                            .frame(minHeight: 200, maxHeight: 400)
                            .padding(8)
                            .background(Color(.systemBackground))
                            .cornerRadius(8)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color(.systemGray4), lineWidth: 1)
                            )
                            .onDisappear(perform: saveCampaignDetails) // Save if view disappears while editing
                    } else {
                        Text(editableConcept.isEmpty ? "Tap Edit to add campaign concept..." : editableConcept)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .frame(minHeight: 100)
                            .padding()
                            .background(Color(.systemGroupedBackground))
                            .cornerRadius(8)
                            .foregroundColor(editableConcept.isEmpty ? .secondary : .primary)
                            .onTapGesture {
                                isEditingConcept = true
                            }
                    }
                }
                .padding()
                .background(Color(.systemBackground))
                .cornerRadius(12)

                // Placeholder for Sections View (to be implemented later)
                VStack(alignment: .leading) {
                    Text("Sections")
                        .font(.headline)
                    Text("Campaign sections will be listed and editable here in a future update.")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .center)
                        .background(Color(.systemGroupedBackground))
                        .cornerRadius(8)
                }
                .padding()
            }
            .padding()
        }
        .navigationTitle(editableTitle) // Dynamically update navigation title
        .navigationBarTitleDisplayMode(.inline) // Use inline to make space for editable title in content if desired
        .onDisappear(perform: saveCampaignDetails) // Save when the view disappears
        // TODO: Re-add sheets for AI generation and export
        /*
        .sheet(isPresented: $showingGenerateSheet) { ... }
        .sheet(isPresented: $showingExportSheet) { ... }
        */
    }

    private func saveCampaignDetails() {
        var updatedCampaign = campaign // Create a mutable copy
        updatedCampaign.title = editableTitle
        updatedCampaign.concept = editableConcept.isEmpty ? nil : editableConcept
        updatedCampaign.markAsModified()

        campaignCreator.updateCampaign(updatedCampaign)
        self.campaign = updatedCampaign // Update the local @State to reflect changes if needed
        print("Campaign details saved for: \(updatedCampaign.title)")
    }

    // TODO: Update generateContent and exportCampaignContent for new Campaign structure
    /*
    private func generateContent() {
        // ... adapt to use campaign.concept or a specific section's content ...
        // ... update campaign.concept or section content with generatedText ...
        // campaignCreator.updateCampaign(campaign)
    }

    private func exportCampaignContent() {
        // exportedMarkdown = campaignCreator.exportCampaignToHomebrewery(campaign)
        // showingExportSheet = true
    }
    */
}

#Preview {
    let campaignCreator = CampaignCreator()
    let sampleCampaign = campaignCreator.createCampaign(title: "My Epic Saga")
    // Add a concept for preview if desired
    // sampleCampaign.concept = "A thrilling adventure in a land of dragons and magic."
    // campaignCreator.updateCampaign(sampleCampaign) // If CampaignCreator needs to know about it for preview

    return NavigationView {
        CampaignDetailView(campaign: sampleCampaign, campaignCreator: campaignCreator)
    }
}