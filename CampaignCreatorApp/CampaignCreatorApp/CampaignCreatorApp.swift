import SwiftUI
import CampaignCreatorLib

@main
struct CampaignCreatorApp: App {
    @StateObject private var campaignCreator = CampaignCreator()
    @StateObject private var themeManager = CampaignThemeManager()
    @StateObject private var imageUploadService = ImageUploadService(apiService: APIService())

    var body: some Scene {
        WindowGroup {
            // ContentView will determine whether to show LoginView or main content
            // based on campaignCreator.isAuthenticated and campaignCreator.isUserSessionValid
            ContentView()
                .environmentObject(campaignCreator)
                .environmentObject(themeManager)
                .environmentObject(imageUploadService)
        }
    }
}