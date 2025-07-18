import SwiftUI

struct ContentView: View {
    @EnvironmentObject var viewModel: ContentViewModel

    var body: some View {
        Group {
            if viewModel.isAuthenticated {
                MainTabView()
            } else {
                Color.clear
                    .fullScreenCover(isPresented: .constant(!viewModel.isAuthenticated)) {
                        LoginView(viewModel: viewModel)
                    }
            }
        }
    }
}

struct MainTabView: View {
    @EnvironmentObject var contentViewModel: ContentViewModel
    @StateObject private var viewModel = MainTabViewModel()

    var body: some View {
        TabView(selection: $viewModel.selectedTab) {
            CampaignListView()
                .tabItem {
                    Image(systemName: "doc.text.fill")
                    Text("Campaigns")
                }
                .tag(0)
            
            CharacterListView()
                .tabItem {
                    Image(systemName: "person.3.fill")
                    Text("Characters")
                }
                .tag(1)

            SettingsView()
                .tabItem {
                    Image(systemName: "gear")
                    Text("Settings")
                }
                .tag(2)
        }
        .accentColor(.blue)
        .environmentObject(contentViewModel)
    }
}

#Preview {
    ContentView()
        .environmentObject(ContentViewModel(modelContext: PersistenceController.shared.container.mainContext))
}
