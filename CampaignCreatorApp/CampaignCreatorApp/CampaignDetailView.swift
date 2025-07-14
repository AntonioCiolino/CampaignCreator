import SwiftUI
import Kingfisher
import SwiftData

struct CampaignDetailView: View {
    let campaign: CampaignModel

    @State private var showingEditSheet = false

    @State private var showingEditSheet = false
    @State private var isEditingConcept = false
    @State private var editableConcept = ""
    @State private var selectedLLMId = ""
    @State private var temperature = 0.7
    @StateObject private var themeManager = CampaignThemeManager()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                CampaignHeaderView(campaign: campaign, editableTitle: .constant(campaign.title), isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor, onSetBadgeAction: {})

                CampaignConceptEditorView(isEditingConcept: $isEditingConcept, editableConcept: $editableConcept, isSaving: false, isGeneratingText: false, currentPrimaryColor: themeManager.primaryColor, currentFont: themeManager.bodyFont, currentTextColor: themeManager.textColor, onSaveChanges: {
                    // on save changes
                })

                SectionBox(title: "Table of Contents") {
                    // TOC items
                }

                CampaignLLMSettingsView(selectedLLMId: $selectedLLMId, temperature: $temperature, availableLLMs: [], currentFont: themeManager.bodyFont, currentTextColor: themeManager.textColor, onLLMSettingsChange: {
                    // on LLM settings change
                })

                CampaignMoodboardView(campaign: campaign)

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
        .onAppear {
            themeManager.updateTheme(from: campaign)
            editableConcept = campaign.concept ?? ""
        }
    }
}
