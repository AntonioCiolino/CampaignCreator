import SwiftUI
import CampaignCreatorLib

struct ContentView: View {
    @StateObject private var campaignCreator = CampaignCreator() // Use @StateObject for ObservableObjects
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            CampaignListView(campaignCreator: campaignCreator)
                .tabItem {
                    Image(systemName: "doc.text.fill")
                    Text("Campaigns")
                }
                .tag(0)
            
            CharacterListView(campaignCreator: campaignCreator) // Added CharacterListView
                .tabItem {
                    Image(systemName: "person.3.fill")
                    Text("Characters")
                }
                .tag(1)

            SettingsView() // SettingsView will now be tag 2
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
    ContentView()
}