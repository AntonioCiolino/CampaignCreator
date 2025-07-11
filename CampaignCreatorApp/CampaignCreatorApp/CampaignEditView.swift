import SwiftUI
import CampaignCreatorLib

struct CampaignEditView: View { // Renamed struct
    @ObservedObject var campaignCreator: CampaignCreator // Added campaignCreator
    @Binding var campaign: Campaign
    @Binding var isPresented: Bool // Added for sheet presentation

    @Environment(\.dismiss) var dismiss

    // Campaign basic details
    @State private var title: String
    @State private var initialUserPrompt: String
    @State private var concept: String

    // Local state for color pickers
    @State private var primaryColor: Color
    @State private var secondaryColor: Color
    @State private var backgroundColor: Color
    @State private var textColor: Color

    // Temporary state for font family and background image URL editing
    @State private var fontFamily: String
    @State private var backgroundImageUrl: String
    @State private var backgroundImageOpacity: Double

    // State for linked characters
    @State private var selectedCharacterIDs: Set<Int>

    // Error handling
    @State private var showErrorAlert = false
    @State private var errorMessage = ""
    @State private var isSaving = false

    init(campaign: Binding<Campaign>, campaignCreator: CampaignCreator, isPresented: Binding<Bool>) {
        self._campaign = campaign
        self._campaignCreator = ObservedObject(wrappedValue: campaignCreator)
        self._isPresented = isPresented

        // Initialize campaign basic details
        _title = State(initialValue: campaign.wrappedValue.title)
        _initialUserPrompt = State(initialValue: campaign.wrappedValue.initialUserPrompt ?? "")
        _concept = State(initialValue: campaign.wrappedValue.concept ?? "")

        // Initialize theme properties
        _primaryColor = State(initialValue: campaign.wrappedValue.themePrimaryColor.map { Color(hex: $0) } ?? .accentColor)
        _secondaryColor = State(initialValue: campaign.wrappedValue.themeSecondaryColor.map { Color(hex: $0) } ?? .secondary)
        _backgroundColor = State(initialValue: campaign.wrappedValue.themeBackgroundColor.map { Color(hex: $0) } ?? Color(.systemBackground))
        _textColor = State(initialValue: campaign.wrappedValue.themeTextColor.map { Color(hex: $0) } ?? Color(.label))
        _fontFamily = State(initialValue: campaign.wrappedValue.themeFontFamily ?? "")
        _backgroundImageUrl = State(initialValue: campaign.wrappedValue.themeBackgroundImageURL ?? "")
        _backgroundImageOpacity = State(initialValue: campaign.wrappedValue.themeBackgroundImageOpacity ?? 1.0)

        // Initialize linked characters
        _selectedCharacterIDs = State(initialValue: Set(campaign.wrappedValue.linkedCharacterIDs ?? []))
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Campaign Details")) {
                    TextField("Title", text: $title)
                    // Using TextEditor for potentially longer prompts/concepts
                    VStack(alignment: .leading) {
                        Text("Initial User Prompt").font(.caption)
                        TextEditor(text: $initialUserPrompt).frame(height: 100)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                    VStack(alignment: .leading) {
                        Text("Concept").font(.caption)
                        TextEditor(text: $concept).frame(height: 150)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                }

                Section(header: Text("Theme Colors")) {
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

                    if !backgroundImageUrl.isEmpty {
                        Button("Remove Background Image") {
                            backgroundImageUrl = ""
                        }
                        .foregroundColor(.red)
                    }

                    HStack {
                        Text("Opacity")
                        Slider(value: $backgroundImageOpacity, in: 0...1, step: 0.05)
                        Text(String(format: "%.2f", backgroundImageOpacity))
                    }
                    .disabled(backgroundImageUrl.isEmpty)
                }

                Section(header: Text("Linked Characters")) {
                    if campaignCreator.characters.isEmpty {
                        Text("No characters available to link. Create characters first.")
                            .foregroundColor(.secondary)
                    } else {
                        List {
                            ForEach(campaignCreator.characters) { character in
                                HStack {
                                    Text(character.name)
                                    Spacer()
                                    if selectedCharacterIDs.contains(character.id) {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(.blue)
                                    } else {
                                        Image(systemName: "circle")
                                            .foregroundColor(.gray)
                                    }
                                }
                                .contentShape(Rectangle()) // Make the whole row tappable
                                .onTapGesture {
                                    if selectedCharacterIDs.contains(character.id) {
                                        selectedCharacterIDs.remove(character.id)
                                    } else {
                                        selectedCharacterIDs.insert(character.id)
                                    }
                                }
                            }
                        }
                        // .frame(height: CGFloat(campaignCreator.characters.count) * 44.0) // Adjust height dynamically or use fixed
                    }
                }


                Section {
                    Button("Reset Theme to Defaults") {
                        resetThemeToDefaults()
                    }
                    .foregroundColor(.orange)
                }
            }
            .navigationTitle("Edit Campaign") // Updated Title
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        isPresented = false // Use binding to dismiss
                    }
                    .disabled(isSaving)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if isSaving {
                        ProgressView()
                    } else {
                        Button("Done") {
                            Task {
                                await saveChanges()
                                // isPresented will be set to false by caller on successful save if needed
                            }
                        }
                        .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }
            }
        }
    }

    private func saveChanges() async {
        guard !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Campaign title cannot be empty."
            showErrorAlert = true
            return
        }

        isSaving = true
        var campaignToUpdate = campaign // Make a mutable copy to update

        // Update basic details
        campaignToUpdate.title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        campaignToUpdate.initialUserPrompt = initialUserPrompt.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        campaignToUpdate.concept = concept.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()

        // Update theme properties
        campaignToUpdate.themePrimaryColor = primaryColor.toHex()
        campaignToUpdate.themeSecondaryColor = secondaryColor.toHex()
        campaignToUpdate.themeBackgroundColor = backgroundColor.toHex()
        campaignToUpdate.themeTextColor = textColor.toHex()
        campaignToUpdate.themeFontFamily = fontFamily.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        campaignToUpdate.themeBackgroundImageURL = backgroundImageUrl.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        campaignToUpdate.themeBackgroundImageOpacity = (campaignToUpdate.themeBackgroundImageURL == nil) ? nil : backgroundImageOpacity

        // Update linked characters
        campaignToUpdate.linkedCharacterIDs = Array(selectedCharacterIDs)

        campaignToUpdate.markAsModified()

        do {
            try await campaignCreator.updateCampaign(campaignToUpdate)
            // After successful save, update the original binding to reflect changes if needed,
            // though CampaignCreator should update its published array which should flow down.
            // self.campaign = campaignToUpdate // This might be needed if direct binding update is preferred
            isPresented = false // Dismiss the sheet
        } catch let error as APIError {
            errorMessage = "Failed to update campaign: \(error.localizedDescription)"
            showErrorAlert = true
        } catch {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
            showErrorAlert = true
        }
        isSaving = false
    }

    private func resetThemeToDefaults() { // Renamed
        // Reset @State vars for theme to default Color values
        primaryColor = .accentColor
        secondaryColor = .secondary
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

// String extension nilIfEmpty (ensure it's available or define it)
// extension String {
//     func nilIfEmpty() -> String? {
//         self.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : self
//     }
// }

// Preview
struct CampaignEditView_Previews: PreviewProvider { // Renamed
    static var previews: some View {
        let creator = CampaignCreator() // Create a CampaignCreator instance
        // Populate with some characters for the preview
        creator.characters = [
            Character(id: 1, name: "Elara"),
            Character(id: 2, name: "Grom"),
            Character(id: 3, name: "Seraphina")
        ]
        // Create a dummy campaign for preview
        @State var previewCampaign = Campaign(id: 1, title: "Preview Campaign", linkedCharacterIDs: [1,3])
        @State var isPresented = true // For sheet presentation

        return CampaignEditView(campaign: $previewCampaign, campaignCreator: creator, isPresented: $isPresented) // Pass CampaignCreator
    }
}
