import SwiftUI
import CampaignCreatorLib

struct CampaignConceptEditorView: View {
    @Binding var isEditingConcept: Bool
    @Binding var editableConcept: String

    let isSaving: Bool
    let isGeneratingText: Bool
    let currentPrimaryColor: Color
    let currentFont: Font
    let currentTextColor: Color

    let onSaveChanges: () async -> Void

    var body: some View {
        SectionBox(title: "Campaign Concept") {
            VStack(alignment: .leading, spacing: 12) {
                if isEditingConcept {
                    TextEditor(text: $editableConcept)
                        .frame(minHeight: 200, maxHeight: 400).padding(8)
                        .background(Color(.secondarySystemGroupedBackground))
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(.systemGray4), lineWidth: 1))
                        .disabled(isSaving || isGeneratingText)
                    Button("Done") {
                        Task {
                            await onSaveChanges()
                            isEditingConcept = false
                        }
                    }
                    .buttonStyle(.bordered)
                    .tint(currentPrimaryColor)
                    .disabled(isSaving || isGeneratingText)
                } else {
                    Text(editableConcept.isEmpty ? "Tap Edit to add campaign concept..." : editableConcept)
                        .frame(maxWidth: .infinity, alignment: .leading).frame(minHeight: 100)
                        .padding().background(Color(.systemGroupedBackground))
                        .cornerRadius(8)
                        .foregroundColor(editableConcept.isEmpty ? .secondary : currentTextColor)
                    Button("Edit") {
                        isEditingConcept = true
                    }
                    .buttonStyle(.bordered)
                    .tint(currentPrimaryColor)
                    .disabled(isSaving || isGeneratingText)
                }
            }
        }
        .padding().background(Color(.systemBackground)).cornerRadius(12)
        .font(currentFont)
    }
}
