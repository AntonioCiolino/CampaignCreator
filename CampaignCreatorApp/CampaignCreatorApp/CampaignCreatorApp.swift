import SwiftUI
import CampaignCreatorLib

@main
struct CampaignCreatorApp: App {
    @StateObject private var campaignCreator = CampaignCreator()
    @StateObject private var themeManager = CampaignThemeManager()
    @StateObject private var imageUploadService = ImageUploadService(apiService: CampaignCreatorLib.APIService())

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(campaignCreator)
                .environmentObject(themeManager)
                .environmentObject(imageUploadService)
        }
    }
}