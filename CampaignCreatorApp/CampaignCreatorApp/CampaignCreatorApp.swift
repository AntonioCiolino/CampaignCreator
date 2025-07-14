import SwiftUI
import CampaignCreatorLib

@main
struct CampaignCreatorApp: App {
    let persistenceController = PersistenceController.shared

    init() {
        ValueTransformer.setValueTransformer(CharacterStatsTransformer(), forName: NSValueTransformerName("CharacterStatsTransformer"))
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .modelContainer(persistenceController.container)
        }
    }
}