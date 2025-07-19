import SwiftUI
import CampaignCreatorLib

@main
struct CampaignCreatorApp: App {
    @StateObject private var contentViewModel: ContentViewModel
    @StateObject private var networkMonitor = NetworkMonitor()
    @StateObject private var imageUploadService = ImageUploadService(apiService: CampaignCreatorLib.APIService())

    init() {
        let modelContainer = PersistenceController.shared.container
        _contentViewModel = StateObject(wrappedValue: ContentViewModel(modelContext: modelContainer.mainContext))
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(contentViewModel)
                .environmentObject(networkMonitor)
                .environmentObject(imageUploadService)
                .modelContainer(PersistenceController.shared.container)
        }
    }
}