import SwiftUI
import SwiftData

struct MemoriesListView: View {
    @Bindable var character: CharacterModel
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        List {
            ForEach(character.memories ?? []) { memory in
                NavigationLink(destination: MemoryView(viewModel: MemoryViewModel(memory: memory, modelContext: modelContext))) {
                    VStack(alignment: .leading) {
                        Text(memory.summary)
                        Text("Last updated: \(memory.timestamp, style: .date)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Memories")
    }
}
