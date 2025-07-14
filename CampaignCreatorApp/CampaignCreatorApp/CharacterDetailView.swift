import SwiftUI
import Kingfisher
import SwiftData

struct CharacterDetailView: View {
    @StateObject private var viewModel: CharacterDetailViewModel
    @Environment(\.modelContext) private var modelContext

    init(character: Character) {
        _viewModel = StateObject(wrappedValue: CharacterDetailViewModel(character: character))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // your UI...
            }
            .padding()
            .onAppear {
                viewModel.setModelContext(modelContext)
            }
        }
        .navigationTitle(viewModel.character.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                Button("Edit") {
                    // ...
                }
            }
        }
    }
}
