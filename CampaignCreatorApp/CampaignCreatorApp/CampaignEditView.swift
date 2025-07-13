import SwiftUI
import CampaignCreatorLib

struct CampaignEditView: View {
    @StateObject private var viewModel: CampaignEditViewModel
    @Binding var isPresented: Bool
    var onCampaignUpdated: ((Campaign) -> Void)?

    init(campaign: Campaign, isPresented: Binding<Bool>, onCampaignUpdated: ((Campaign) -> Void)? = nil) {
        _viewModel = StateObject(wrappedValue: CampaignEditViewModel(campaign: campaign))
        _isPresented = isPresented
        self.onCampaignUpdated = onCampaignUpdated
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Campaign Details")) {
                    TextField("Title", text: $viewModel.title)
                    VStack(alignment: .leading) {
                        Text("Initial User Prompt").font(.caption)
                        TextEditor(text: $viewModel.initialUserPrompt).frame(height: 100)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                    VStack(alignment: .leading) {
                        Text("Concept").font(.caption)
                        TextEditor(text: $viewModel.concept).frame(height: 150)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                }

                Section(header: Text("Theme Colors")) {
                    ColorPicker("Primary Color", selection: $viewModel.primaryColor, supportsOpacity: false)
                    ColorPicker("Secondary Color", selection: $viewModel.secondaryColor, supportsOpacity: false)
                    ColorPicker("Background Color", selection: $viewModel.backgroundColor, supportsOpacity: false)
                    ColorPicker("Text Color", selection: $viewModel.textColor, supportsOpacity: false)
                }

                Section(header: Text("Font")) {
                    TextField("Font Family (e.g., Arial)", text: $viewModel.fontFamily)
                }

                Section(header: Text("Background Image")) {
                    TextField("Image URL", text: $viewModel.backgroundImageUrl)
                        .keyboardType(.URL)
                        .autocapitalization(.none)

                    if !viewModel.backgroundImageUrl.isEmpty {
                        Button("Remove Background Image") {
                            viewModel.backgroundImageUrl = ""
                        }
                        .foregroundColor(.red)
                    }

                    HStack {
                        Text("Opacity")
                        Slider(value: $viewModel.backgroundImageOpacity, in: 0...1, step: 0.05)
                        Text(String(format: "%.2f", viewModel.backgroundImageOpacity))
                    }
                    .disabled(viewModel.backgroundImageUrl.isEmpty)
                }

                Section {
                    Button("Reset Theme to Defaults") {
                        viewModel.resetThemeToDefaults()
                    }
                    .foregroundColor(.orange)
                }
            }
            .navigationTitle("Edit Campaign")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        isPresented = false
                    }
                    .disabled(viewModel.isSaving)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if viewModel.isSaving {
                        ProgressView()
                    } else {
                        Button("Done") {
                            Task {
                                if let updatedCampaign = await viewModel.saveChanges() {
                                    onCampaignUpdated?(updatedCampaign)
                                    isPresented = false
                                }
                            }
                        }
                        .disabled(viewModel.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }
            }
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "An unknown error occurred.")
            }
        }
    }
}

struct CampaignEditView_Previews: PreviewProvider {
    static var previews: some View {
        let libCampaign = CampaignCreatorLib.Campaign(
            id: 1,
            title: "Preview Campaign",
            initialUserPrompt: "Initial prompt for preview.",
            concept: "A campaign for previewing.",
            badgeImageURL: nil,
            thematicImageURL: nil,
            thematicImagePrompt: nil,
            selectedLLMId: nil,
            temperature: 0.7,
            moodBoardImageURLs: [],
            themePrimaryColor: "#FF0000",
            themeSecondaryColor: "#00FF00",
            themeBackgroundColor: "#0000FF",
            themeTextColor: "#FFFFFF",
            themeFontFamily: "Arial",
            themeBackgroundImageURL: nil,
            themeBackgroundImageOpacity: 1.0,
            linkedCharacterIDs: [],
            customSections: []
        )

        // Now, create the app-level Campaign object using the failable initializer.
        // We'll force unwrap here for the preview, assuming it will always succeed with our mock data.
        let previewCampaign = Campaign(from: libCampaign)!

        return CampaignEditView(
            campaign: previewCampaign,
            isPresented: .constant(true)
        )
    }
}
