import SwiftUI
import CampaignCreatorLib

@main
struct CampaignCreatorApp: App {
    let persistenceController = PersistenceController.shared

    @StateObject private var imageUploadService = ImageUploadService()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .modelContainer(persistenceController.container)
                .environmentObject(imageUploadService)
        }
    }
}