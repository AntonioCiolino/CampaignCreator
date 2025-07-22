import SwiftUI
import SwiftData

struct CampaignEditView: View {
    @Bindable var campaign: CampaignModel
    @Binding var isPresented: Bool
    @State private var showingImageManager = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Section(header: Text("Campaign Details")) {
                    TextField("Title", text: $campaign.title)
                    VStack(alignment: .leading) {
                        Text("Initial User Prompt").font(.caption)
                        TextEditor(text: .init(get: { campaign.initial_user_prompt ?? "" }, set: { campaign.initial_user_prompt = $0 })).frame(height: 100)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                    VStack(alignment: .leading) {
                        Text("Concept").font(.caption)
                        TextEditor(text: .init(get: { campaign.concept ?? "" }, set: { campaign.concept = $0 })).frame(height: 150)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                }
                .padding()

                Section(header: Text("Theme Colors")) {
                    ColorPicker("Primary Color", selection: .init(get: { Color(hex: campaign.theme_primary_color ?? "") }, set: { campaign.theme_primary_color = $0.toHex() }), supportsOpacity: false)
                    ColorPicker("Secondary Color", selection: .init(get: { Color(hex: campaign.theme_secondary_color ?? "") }, set: { campaign.theme_secondary_color = $0.toHex() }), supportsOpacity: false)
                    ColorPicker("Background Color", selection: .init(get: { Color(hex: campaign.theme_background_color ?? "") }, set: { campaign.theme_background_color = $0.toHex() }), supportsOpacity: false)
                    ColorPicker("Text Color", selection: .init(get: { Color(hex: campaign.theme_text_color ?? "") }, set: { campaign.theme_text_color = $0.toHex() }), supportsOpacity: false)
                }

                Section(header: Text("Font")) {
                    TextField("Font Family (e.g., Arial)", text: .init(get: { campaign.theme_font_family ?? "" }, set: { campaign.theme_font_family = $0 }))
                }

                Section(header: Text("Background Image")) {
                    TextField("Image URL", text: .init(get: { campaign.theme_background_image_url ?? "" }, set: { campaign.theme_background_image_url = $0 }))
                        .keyboardType(.URL)
                        .autocapitalization(.none)

                    if !(campaign.theme_background_image_url?.isEmpty ?? true) {
                        Button("Remove Background Image") {
                            campaign.theme_background_image_url = ""
                        }
                        .foregroundColor(.red)
                    }

                    HStack {
                        Text("Opacity")
                        Slider(value: .init(get: { campaign.theme_background_image_opacity ?? 1.0 }, set: { campaign.theme_background_image_opacity = $0 }), in: 0...1, step: 0.05)
                        Text(String(format: "%.2f", campaign.theme_background_image_opacity ?? 1.0))
                    }
                    .disabled(campaign.theme_background_image_url?.isEmpty ?? true)
                }

                Section {
                    Button("Reset Theme to Defaults") {
                        campaign.theme_primary_color = nil
                        campaign.theme_secondary_color = nil
                        campaign.theme_background_color = nil
                        campaign.theme_text_color = nil
                        campaign.theme_font_family = nil
                        campaign.theme_background_image_url = nil
                        campaign.theme_background_image_opacity = nil
                    }
                    .foregroundColor(.orange)
                }

                Section(header: Text("Campaign Images")) {
                    Button(action: {
                        showingImageManager = true
                    }) {
                        Label("Manage Images", systemImage: "photo.on.rectangle.angled")
                    }
                }
            }
            .sheet(isPresented: $showingImageManager) {
                CampaignImageManagerView(imageURLs: .init(get: { campaign.mood_board_image_urls ?? [] }, set: { campaign.mood_board_image_urls = $0 }), campaignID: campaign.id)
            }
        }
        .navigationTitle("Edit Campaign")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button("Cancel") {
                    isPresented = false
                }
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Done") {
                    isPresented = false
                }
                .disabled(campaign.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
    }
}
