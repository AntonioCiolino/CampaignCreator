import SwiftUI
import Combine
import CampaignCreatorLib // For Color(hex:) and potentially Font utilities later

@MainActor
class CampaignThemeManager: ObservableObject {
    @Published var primaryColor: Color = .accentColor
    @Published var secondaryColor: Color = .secondary
    @Published var backgroundColor: Color = Color(.systemBackground)
    @Published var textColor: Color = Color(.label)
    @Published var fontFamily: String? = nil // Store as String, convert to Font where needed
    @Published var backgroundImageUrl: URL? = nil
    @Published var backgroundImageOpacity: Double = 1.0

    func updateTheme(from campaign: CampaignModel) {
        primaryColor = campaign.theme_primary_color.flatMap { Color(hex: $0) } ?? .accentColor
        secondaryColor = campaign.theme_secondary_color.flatMap { Color(hex: $0) } ?? .secondary
        backgroundColor = campaign.theme_background_color.flatMap { Color(hex: $0) } ?? Color(.systemBackground)
        textColor = campaign.theme_text_color.flatMap { Color(hex: $0) } ?? Color(.label)
        fontFamily = campaign.theme_font_family
        backgroundImageUrl = campaign.theme_background_image_url.flatMap { URL(string: $0) }
        backgroundImageOpacity = Double(campaign.theme_background_image_opacity ?? 1.0)

        print("ThemeManager updated for campaign: \(campaign.title)")
        print("  Primary: \(primaryColor), BG: \(backgroundColor), Text: \(textColor)")
        print("  Font: \(fontFamily ?? "Default"), BG Image: \(backgroundImageUrl?.absoluteString ?? "None"), Opacity: \(backgroundImageOpacity)")
    }

    func resetTheme() {
        primaryColor = .accentColor
        secondaryColor = .secondary
        backgroundColor = Color(.systemBackground)
        textColor = Color(.label)
        fontFamily = nil
        backgroundImageUrl = nil
        backgroundImageOpacity = 1.0
        print("ThemeManager reset to defaults.")
    }

    // Helper to get Font object, more sophisticated logic can be added
    var bodyFont: Font {
        if let fontFamilyName = fontFamily, !fontFamilyName.isEmpty {
            return .custom(fontFamilyName, size: 16) // Default size, can be parameterized
        }
        return .body
    }

    var titleFont: Font {
        if let fontFamilyName = fontFamily, !fontFamilyName.isEmpty {
            return .custom(fontFamilyName, size: 24) // Default size, can be parameterized
        }
        return .title
    }
}

// Make sure Color+Hex.swift contains the Color(hex:) initializer.
// If not, it needs to be added or moved to a shared location.
// Example:
// extension Color {
//     init?(hex: String) {
//         // Implementation for hex to Color
//     }
// }
