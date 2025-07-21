import SwiftUI
import SwiftData

struct CampaignSectionView: View {
    @StateObject var viewModel: CampaignSectionViewModel
    @State private var attributedString: NSAttributedString = NSAttributedString(string: "")
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // TODO: Add character linking UI here
            if let title = viewModel.section.title {
                Text(title)
                    .font(.title)
                    .fontWeight(.bold)
            }

            if viewModel.isEditing {
                RichTextEditorView(text: $attributedString, onSnippetEdit: { editType in
                    if let feature = self.viewModel.features.first(where: { $0.name == editType }) {
                        self.viewModel.snippetEdit(editType: editType, featureId: feature.id)
                    }
                }, onSelectionChange: { range in
                    self.viewModel.selectedText = (self.attributedString.string as NSString).substring(with: range)
                })
                .onAppear {
                    attributedString = NSAttributedString(string: viewModel.editedContent)
                }
                .onChange(of: attributedString) { _, newValue in
                    viewModel.editedContent = newValue.string
                }

                HStack {
                    Button("Save") {
                        viewModel.save()
                    }
                    Button("Cancel") {
                        viewModel.cancel()
                    }
                    Button("Regenerate") {
                        viewModel.regenerate()
                    }
                }
            } else {
                Text(viewModel.section.content)
                    .font(.body)

                HStack {
                    Button("Edit") {
                        viewModel.isEditing = true
                    }
                    Button("Delete") {
                        viewModel.delete()
                    }
                }
            }
        }
        .padding()
    }
}
