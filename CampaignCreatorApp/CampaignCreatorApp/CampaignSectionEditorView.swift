import SwiftUI
import SwiftData

struct CampaignSectionEditorView: View {
    @StateObject var viewModel: CampaignSectionViewModel
    @Binding var isPresented: Bool
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        NavigationView {
            VStack {
                RichTextEditorView(text: $viewModel.attributedString, onSnippetEdit: { editType in
                    if let feature = self.viewModel.features.first(where: { $0.name == editType }) {
                        self.viewModel.snippetEdit(editType: editType, featureId: feature.id)
                    }
                }, onSelectionChange: { range in
                    self.viewModel.selectedText = (viewModel.attributedString.string as NSString).substring(with: range)
                }, featureService: {
                    let featureService = FeatureService()
                    featureService.setModelContext(modelContext)
                    return featureService
                }())
                .environmentObject(ImageUploadService(apiService: CampaignCreatorLib.APIService()))
            }
            .navigationTitle("Edit Section")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        isPresented = false
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        viewModel.save()
                        isPresented = false
                    }
                }
            }
        }
    }
}
