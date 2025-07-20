import SwiftUI

struct CampaignSectionView: View {
    @StateObject var viewModel: CampaignSectionViewModel
    @State private var attributedString: NSAttributedString = NSAttributedString(string: "")

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // TODO: Add character linking UI here
            if let title = viewModel.section.title {
                Text(title)
                    .font(.title)
                    .fontWeight(.bold)
            }

            if viewModel.isEditing {
                RichTextEditorView(text: $attributedString)
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
