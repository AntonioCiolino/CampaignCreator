import Foundation
import SwiftUI
import CampaignCreatorLib

class CampaignSectionViewModel: ObservableObject {
    @Published var section: CampaignSection
    @Published var isEditing = false
    @Published var editedContent: String

    private var llmService: LLMService

    // Add a closure to inform the parent view of deletion
    var onDelete: (() -> Void)?

    init(section: CampaignSection, llmService: LLMService, onDelete: (() -> Void)? = nil) {
        self.section = section
        self.editedContent = section.content
        self.llmService = llmService
        self.onDelete = onDelete
    }

    func save() {
        Task {
            do {
                let updatedSection = try await llmService.apiService.updateCampaignSection(
                    campaignId: section.campaign_id,
                    sectionId: section.id,
                    data: CampaignSectionUpdatePayload(content: editedContent)
                )
                DispatchQueue.main.async {
                    self.section = updatedSection
                    self.isEditing = false
                }
            } catch {
                // Handle error
                print("Failed to save section: \(error)")
            }
        }
    }

    func cancel() {
        editedContent = section.content
        isEditing = false
    }

    func regenerate() {
        Task {
            do {
                let updatedSection = try await llmService.apiService.regenerateCampaignSection(
                    campaignId: section.campaign_id,
                    sectionId: section.id,
                    payload: SectionRegeneratePayload(new_prompt: "Regenerate this section.")
                )
                DispatchQueue.main.async {
                    self.section = updatedSection
                    self.editedContent = updatedSection.content
                }
            } catch {
                // Handle error
                print("Failed to regenerate section: \(error)")
            }
        }
    }

    func delete() {
        Task {
            do {
                try await llmService.apiService.deleteCampaignSection(
                    campaignId: section.campaign_id,
                    sectionId: section.id
                )
                DispatchQueue.main.async {
                    self.onDelete?()
                }
            } catch {
                // Handle error
                print("Failed to delete section: \(error)")
            }
        }
    }
}

struct CampaignSectionUpdatePayload: Codable {
    let content: String
}
