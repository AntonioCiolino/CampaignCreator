import Foundation
import SwiftUI
import CampaignCreatorLib
import SwiftData

class CampaignSectionViewModel: ObservableObject {
    @Published var section: CampaignSection
    @Published var isEditing = false
    @Published var isRegenerating = false
    @Published var editedContent: String
    @Published var selectedText: String?
    @Published var features: [Feature] = []
    @Published var attributedString: NSAttributedString

    private var llmService: LLMService
    private var featureService: FeatureService

    // Add a closure to inform the parent view of deletion
    var onDelete: (() -> Void)?

    init(section: CampaignSection, llmService: LLMService, featureService: @autoclosure () -> FeatureService, onDelete: (() -> Void)? = nil) {
        self.section = section
        self.editedContent = section.content
        self.attributedString = NSAttributedString(string: section.content)
        self.llmService = llmService
        self.featureService = featureService()
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
        editedContent = attributedString.string
        Task {
            do {
                let updatedSectionData = try await llmService.apiService.updateCampaignSection(
                    campaignId: section.campaign_id,
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
        isRegenerating = true
        Task {
            do {
                if let apiService = llmService.apiService as? CampaignCreatorLib.APIService, !apiService.hasToken() {
                    // Attempt to refresh token
                    // This is a simplified example. In a real app, you would have a more robust token refresh mechanism.
                    throw APIError.notAuthenticated
                }

                let updatedSectionData = try await llmService.apiService.regenerateCampaignSection(
                    campaignId: section.campaign_id,
                    sectionId: section.id,
                    payload: SectionRegeneratePayload(newPrompt: "Regenerate this section.")
                )
                DispatchQueue.main.async {
                    self.section.title = updatedSectionData.title
                    self.section.content = updatedSectionData.content
                    self.section.order = updatedSectionData.order
                    self.section.type = updatedSectionData.type
                    self.editedContent = updatedSectionData.content
                    self.attributedString = NSAttributedString(string: updatedSectionData.content)
                    self.isRegenerating = false
                    self.save()
                }
            } catch {
                // Handle error
                print("Failed to regenerate section: \(error)")
                DispatchQueue.main.async {
                    self.isRegenerating = false
                    // self.showErrorAlert = true
                    // self.errorMessage = "Failed to regenerate section. Please try again."
                }
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

    func snippetEdit(editType: String, featureId: Int) {
        Task {
            do {
                guard let selectedText = selectedText else { return }
                let updatedSectionData = try await llmService.apiService.regenerateCampaignSection(
                    campaignId: section.campaign_id,
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
