import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = ContentViewModel()
    let persistenceController = PersistenceController.shared

    var body: some View {
        Group {
            if viewModel.isAuthenticated {
                MainTabView()
                    .environmentObject(viewModel)
                    .modelContainer(persistenceController.container)
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
        CustomTabView(selection: $viewModel.selectedTab) {
            if viewModel.selectedTab == 0 {
                CampaignListView()
            } else if viewModel.selectedTab == 1 {
                CharacterListView()
            } else {
                SettingsView()
            }
        }
        .environmentObject(contentViewModel)
    }
}

#Preview {
    ContentView()
}
