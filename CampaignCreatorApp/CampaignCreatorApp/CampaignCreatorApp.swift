import SwiftUI

@main
struct CampaignCreatorApp: App {
    @StateObject private var contentViewModel: ContentViewModel
    @StateObject private var networkMonitor = NetworkMonitor()

    init() {
        let modelContainer = PersistenceController.shared.container
        _contentViewModel = StateObject(wrappedValue: ContentViewModel(modelContext: modelContainer.mainContext))
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(contentViewModel)
                .environmentObject(networkMonitor)
                .modelContainer(PersistenceController.shared.container)
        }
    }
}