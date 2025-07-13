import Foundation
import SwiftUI

@MainActor
class CampaignEditViewModel: ObservableObject {
    @Published var campaign: Campaign

    @Published var title: String
    @Published var initialUserPrompt: String
    @Published var concept: String

    @Published var primaryColor: Color
    @Published var secondaryColor: Color
    @Published var backgroundColor: Color
    @Published var textColor: Color

    @Published var fontFamily: String
    @Published var backgroundImageUrl: String
    @Published var backgroundImageOpacity: Double

    @Published var isSaving = false
    @Published var errorMessage: String?

    private var apiService = APIService()

    init(campaign: Campaign) {
        self.campaign = campaign

        _title = Published(initialValue: campaign.title)
        _initialUserPrompt = Published(initialValue: campaign.initial_user_prompt ?? "")
        _concept = Published(initialValue: campaign.concept ?? "")

        _primaryColor = Published(initialValue: campaign.theme_primary_color.map { Color(hex: $0) } ?? .accentColor)
        _secondaryColor = Published(initialValue: campaign.theme_secondary_color.map { Color(hex: $0) } ?? .secondary)
        _backgroundColor = Published(initialValue: campaign.theme_background_color.map { Color(hex: $0) } ?? Color(.systemBackground))
        _textColor = Published(initialValue: campaign.theme_text_color.map { Color(hex: $0) } ?? Color(.label))
        _fontFamily = Published(initialValue: campaign.theme_font_family ?? "")
        _backgroundImageUrl = Published(initialValue: campaign.theme_background_image_url ?? "")
        _backgroundImageOpacity = Published(initialValue: campaign.theme_background_image_opacity ?? 1.0)
    }

    func saveChanges() async -> Campaign? {
        guard !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Campaign title cannot be empty."
            return nil
        }

        isSaving = true
        var campaignToUpdate = campaign

        campaignToUpdate.title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        campaignToUpdate.initial_user_prompt = initialUserPrompt.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        campaignToUpdate.concept = concept.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()

        campaignToUpdate.theme_primary_color = primaryColor.toHex()
        campaignToUpdate.theme_secondary_color = secondaryColor.toHex()
        campaignToUpdate.theme_background_color = backgroundColor.toHex()
        campaignToUpdate.theme_text_color = textColor.toHex()
        campaignToUpdate.theme_font_family = fontFamily.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        campaignToUpdate.theme_background_image_url = backgroundImageUrl.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        campaignToUpdate.theme_background_image_opacity = (campaignToUpdate.theme_background_image_url == nil) ? nil : backgroundImageOpacity

        do {
            let campaignUpdate = CampaignUpdate(
                title: campaignToUpdate.title,
                initial_user_prompt: campaignToUpdate.initial_user_prompt,
                concept: campaignToUpdate.concept,
                badge_image_url: campaignToUpdate.badge_image_url,
                thematic_image_url: campaignToUpdate.thematic_image_url,
                thematic_image_prompt: campaignToUpdate.thematic_image_prompt,
                selected_llm_id: campaignToUpdate.selected_llm_id,
                temperature: campaignToUpdate.temperature,
                theme_primary_color: campaignToUpdate.theme_primary_color,
                theme_secondary_color: campaignToUpdate.theme_secondary_color,
                theme_background_color: campaignToUpdate.theme_background_color,
                theme_text_color: campaignToUpdate.theme_text_color,
                theme_font_family: campaignToUpdate.theme_font_family,
                theme_background_image_url: campaignToUpdate.theme_background_image_url,
                theme_background_image_opacity: campaignToUpdate.theme_background_image_opacity,
                mood_board_image_urls: campaignToUpdate.mood_board_image_urls
            )

            let body = try JSONEncoder().encode(campaignUpdate)
            let updatedCampaign: Campaign = try await apiService.performRequest(endpoint: "/campaigns/\\(campaign.id)", method: "PUT", body: body)
            self.campaign = updatedCampaign
            isSaving = false
            return updatedCampaign
        } catch {
            errorMessage = "Failed to update campaign: \\(error.localizedDescription)"
            isSaving = false
            return nil
        }
    }

    func resetThemeToDefaults() {
        primaryColor = .accentColor
        secondaryColor = .secondary
        backgroundColor = Color(.systemBackground)
        textColor = Color(.label)
        fontFamily = ""
        backgroundImageUrl = ""
        backgroundImageOpacity = 1.0
    }
}
