import SwiftUI
import CampaignCreatorLib

@main
struct CampaignCreatorApp: App {
    @StateObject private var campaignCreator = CampaignCreator()
    @StateObject private var themeManager = CampaignThemeManager()
    @StateObject private var imageUploadService = ImageUploadService(apiService: CampaignCreatorLib.APIService())

    init() {
        StringArrayTransformer.register()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(campaignCreator)
                .environmentObject(themeManager)
                .environmentObject(imageUploadService)
        }
    }
}