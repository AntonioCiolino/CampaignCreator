import Foundation
import SwiftUI
import CampaignCreatorLib
import SwiftData

class CampaignSectionViewModel: ObservableObject {
    @Published var section: CampaignSection
    @Published var isEditing = false
    @Published var editedContent: String
    @Published var selectedText: String?
    @Published var features: [Feature] = []

    private var llmService: LLMService
    private var featureService: FeatureService

    // Add a closure to inform the parent view of deletion
    var onDelete: (() -> Void)?

    init(section: CampaignSection, llmService: LLMService, featureService: FeatureService, onDelete: (() -> Void)? = nil) {
        self.section = section
        self.editedContent = section.content
        self.llmService = llmService
        self.featureService = featureService
        self.onDelete = onDelete
        fetchFeatures()
    }

    private func fetchFeatures() {
        Task {
            do {
                self.features = try await self.featureService.fetchFeatures().filter { $0.feature_category == "Snippet" }
            } catch {
                // Handle error
                print("Failed to fetch features: \(error)")
            }
        }
    }

    func save() {
        Task {
            do {
                let updatedSectionData = try await llmService.apiService.updateCampaignSection(
                    campaignId: section.campaign_id!,
                    sectionId: section.id,
                    data: CampaignSectionUpdatePayload(content: editedContent)
                )
                DispatchQueue.main.async {
                    self.section.title = updatedSectionData.title
                    self.section.content = updatedSectionData.content
                    self.section.order = updatedSectionData.order
                    self.section.type = updatedSectionData.type
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
                let updatedSectionData = try await llmService.apiService.regenerateCampaignSection(
                    campaignId: section.campaign_id!,
                    sectionId: section.id,
                    payload: SectionRegeneratePayload(newPrompt: "Regenerate this section.")
                )
                DispatchQueue.main.async {
                    self.section.title = updatedSectionData.title
                    self.section.content = updatedSectionData.content
                    self.section.order = updatedSectionData.order
                    self.section.type = updatedSectionData.type
                    self.editedContent = updatedSectionData.content
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
                    campaignId: section.campaign_id!,
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

    func snippetEdit(editType: String, featureId: Int) {
        Task {
            do {
                guard let selectedText = selectedText else { return }
                let updatedSectionData = try await llmService.apiService.regenerateCampaignSection(
                    campaignId: section.campaign_id!,
                    sectionId: section.id,
                    payload: SectionRegeneratePayload(
                        newPrompt: selectedText,
                        featureId: featureId
                    )
                )
                DispatchQueue.main.async {
                    if let range = self.editedContent.range(of: selectedText) {
                        self.editedContent.replaceSubrange(range, with: updatedSectionData.content)
                    }
                }
            } catch {
                // Handle error
                print("Failed to perform snippet edit: \(error)")
            }
        }
    }
}
