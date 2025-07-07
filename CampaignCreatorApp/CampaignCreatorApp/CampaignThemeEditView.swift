import SwiftUI
import CampaignCreatorLib // For Campaign model

struct CampaignThemeEditView: View {
    @Binding var campaign: Campaign
    @Environment(\.dismiss) var dismiss

    // Local state for color pickers because ColorPicker works with Color, not String?
    @State private var primaryColor: Color
    @State private var secondaryColor: Color
    @State private var backgroundColor: Color
    @State private var textColor: Color

    // Temporary state for font family and background image URL editing
    @State private var fontFamily: String
    @State private var backgroundImageUrl: String
    @State private var backgroundImageOpacity: Double

    init(campaign: Binding<Campaign>) {
        self._campaign = campaign

        // Initialize local @State vars from the campaign's theme properties
        _primaryColor = State(initialValue: campaign.wrappedValue.themePrimaryColor.map { Color(hex: $0) } ?? .accentColor)
        _secondaryColor = State(initialValue: campaign.wrappedValue.themeSecondaryColor.map { Color(hex: $0) } ?? .secondary)
        _backgroundColor = State(initialValue: campaign.wrappedValue.themeBackgroundColor.map { Color(hex: $0) } ?? Color(.systemBackground))
        _textColor = State(initialValue: campaign.wrappedValue.themeTextColor.map { Color(hex: $0) } ?? Color(.label))

        _fontFamily = State(initialValue: campaign.wrappedValue.themeFontFamily ?? "")
        _backgroundImageUrl = State(initialValue: campaign.wrappedValue.themeBackgroundImageURL ?? "")
        _backgroundImageOpacity = State(initialValue: campaign.wrappedValue.themeBackgroundImageOpacity ?? 1.0)
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Colors")) {
                    ColorPicker("Primary Color", selection: $primaryColor, supportsOpacity: false)
                    ColorPicker("Secondary Color", selection: $secondaryColor, supportsOpacity: false)
                    ColorPicker("Background Color", selection: $backgroundColor, supportsOpacity: false)
                    ColorPicker("Text Color", selection: $textColor, supportsOpacity: false)
                }

                Section(header: Text("Font")) {
                    TextField("Font Family (e.g., Arial)", text: $fontFamily)
                }

                Section(header: Text("Background Image")) {
                    TextField("Image URL", text: $backgroundImageUrl)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                    HStack {
                        Text("Opacity")
                        Slider(value: $backgroundImageOpacity, in: 0...1, step: 0.05)
                        Text(String(format: "%.2f", backgroundImageOpacity))
                    }
                    .disabled(backgroundImageUrl.isEmpty)
                }

                Section {
                    Button("Reset to Defaults") {
                        resetToDefaults()
                    }
                    .foregroundColor(.orange)
                }
            }
            .navigationTitle("Edit Campaign Theme")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        saveChanges()
                        dismiss()
                    }
                }
            }
        }
    }

    private func saveChanges() {
        campaign.themePrimaryColor = primaryColor.toHex()
        campaign.themeSecondaryColor = secondaryColor.toHex()
        campaign.themeBackgroundColor = backgroundColor.toHex()
        campaign.themeTextColor = textColor.toHex()

        campaign.themeFontFamily = fontFamily.isEmpty ? nil : fontFamily
        campaign.themeBackgroundImageURL = backgroundImageUrl.isEmpty ? nil : backgroundImageUrl
        campaign.themeBackgroundImageOpacity = backgroundImageUrl.isEmpty ? nil : backgroundImageOpacity

        campaign.markAsModified() // Ensure modifiedAt is updated
    }

    private func resetToDefaults() {
        // Reset @State vars to default Color values
        primaryColor = .accentColor // Or your app's default primary
        secondaryColor = .secondary // Or your app's default secondary
        backgroundColor = Color(.systemBackground)
        textColor = Color(.label)

        fontFamily = "" // Default font name or empty for system default
        backgroundImageUrl = ""
        backgroundImageOpacity = 1.0

        // Also update the campaign binding immediately for preview, then save
        // This effectively stages the reset. User still needs to tap "Done".
        campaign.themePrimaryColor = nil
        campaign.themeSecondaryColor = nil
        campaign.themeBackgroundColor = nil
        campaign.themeTextColor = nil
        campaign.themeFontFamily = nil
        campaign.themeBackgroundImageURL = nil
        campaign.themeBackgroundImageOpacity = nil
    }
}

// Preview
struct CampaignThemeEditView_Previews: PreviewProvider {
    static var previews: some View {
        // Create a dummy campaign for preview
        @State var previewCampaign = Campaign(id: 1, title: "Preview Campaign")
        CampaignThemeEditView(campaign: $previewCampaign)
    }
}
