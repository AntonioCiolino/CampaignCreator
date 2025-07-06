import SwiftUI
import CampaignCreatorLib

struct ContentView: View {
    @StateObject private var campaignCreator = CampaignCreator()
    @State private var selectedTab = 0 // Default to Campaigns tab

    var body: some View {
        Group {
            if campaignCreator.isAuthenticated {
                MainTabView(campaignCreator: campaignCreator, selectedTab: $selectedTab)
            } else {
                // Show LoginView as a full screen cover
                // It will be dismissed internally when campaignCreator.isAuthenticated becomes true
                // by LoginView calling campaignCreator.login() which updates isAuthenticated.
                // No explicit isPresented binding needed here if LoginView handles its own presentation logic correctly.
                // However, to ensure it *covers* everything until auth, .fullScreenCover is good.
                // We need a dummy view to attach .fullScreenCover if there's nothing else.
                Color.clear // Dummy view
                    .fullScreenCover(isPresented: .constant(!campaignCreator.isAuthenticated)) {
                        LoginView(campaignCreator: campaignCreator)
                    }
            }
        }
        // Initial check or on scene phase change could also trigger login presentation
        // For simplicity, relying on @StateObject and initial isAuthenticated value.
    }
}

// Extracted TabView to a separate struct for clarity
struct MainTabView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @Binding var selectedTab: Int

    var body: some View {
        TabView(selection: $selectedTab) {
            CampaignListView(campaignCreator: campaignCreator)
                .tabItem {
                    Image(systemName: "doc.text.fill")
                    Text("Campaigns")
                }
                .tag(0)
            
            CharacterListView(campaignCreator: campaignCreator)
                .tabItem {
                    Image(systemName: "person.3.fill")
                    Text("Characters")
                }
                .tag(1)

            SettingsView(campaignCreator: campaignCreator) // Pass campaignCreator for logout
                .tabItem {
                    Image(systemName: "gear")
                    Text("Settings")
                }
                .tag(2)
        }
        .accentColor(.blue)
    }
}

#Preview {
    // For previewing, you might want to simulate both authenticated and non-authenticated states.
    // Example: Non-authenticated
    let nonAuthCreator = CampaignCreator()
    // nonAuthCreator.isAuthenticated = false // Default

    // Example: Authenticated
    // let authCreator = CampaignCreator()
    // authCreator.isAuthenticated = true
    // authCreator.campaigns = [Campaign(title: "Preview Campaign")] // Add some data

    return ContentView() // Uses default nonAuthCreator for preview
        // .environmentObject(authCreator) // If using .environmentObject for CampaignCreator
}