import Foundation
import SwiftData

@MainActor
class PersistenceController {
    static let shared = PersistenceController()

    let container: ModelContainer

    init(inMemory: Bool = false) {
        let schema = Schema([
            CampaignModel.self,
            CharacterModel.self,
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: inMemory)

        container = try! ModelContainer(for: schema, configurations: [modelConfiguration])

        ValueTransformer.setValueTransformer(CharacterStatsTransformer(), forName: NSValueTransformerName("CharacterStatsTransformer"))
    }

    func save() {
        do {
            try container.mainContext.save()
        } catch {
            let nsError = error as NSError
            fatalError("Unresolved error \(nsError), \(nsError.userInfo)")
        }
    }
}
