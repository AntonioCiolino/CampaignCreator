import SwiftUI
import CampaignCreatorLib

struct ContentView: View {
    @State private var campaignCreator = CampaignCreator()
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            DocumentListView(campaignCreator: campaignCreator)
                .tabItem {
                    Image(systemName: "doc.text.fill")
                    Text("Documents")
                }
                .tag(0)
            
            SettingsView()
                .tabItem {
                    Image(systemName: "gear")
                    Text("Settings")
                }
                .tag(1)
        }
        .accentColor(.blue)
    }
}

#Preview {
    ContentView()
}