import Foundation
import SwiftUI
import SwiftData

@MainActor
class CharacterDetailViewModel: ObservableObject {
    @Published var character: Character
    private var modelContext: ModelContext?

    init(character: Character) {
        self.character = character
    }

    func setModelContext(_ context: ModelContext) {
        self.modelContext = context
    }

    // Use this context in your async logic, e.g.
    func refreshCharacter() async {
        guard let context = modelContext else { return }
        // Fetch or update with context.fetch(...) etc.
    }
}
