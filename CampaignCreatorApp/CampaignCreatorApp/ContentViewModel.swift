import Foundation
import SwiftUI
import SwiftData
import CampaignCreatorLib

@MainActor
class ContentViewModel: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var isLoggingIn: Bool = false
    @Published var authError: String?

    @Query private var users: [UserModel]
    var currentUser: UserModel? {
        users.first
    }

    private var apiService: CampaignCreatorLib.APIService!
    private var tokenManager = CampaignCreatorLib.TokenManager()
    private var modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
        self.apiService = CampaignCreatorLib.APIService(usernameProvider: {
            self.currentUser?.username
        })
        self.isAuthenticated = tokenManager.hasToken()
        if isAuthenticated {
            Task {
                await fetchCurrentUser()
            }
        }
    }

    func login(usernameOrEmail: String, password: String) async {
        isLoggingIn = true
        authError = nil

        do {
            let credentials = LoginRequestDTO(username: usernameOrEmail, password: password)
            let response = try await apiService.login(credentials: credentials)
            tokenManager.setAccessToken(response.accessToken)
            if let refreshToken = response.refreshToken {
                tokenManager.setRefreshToken(refreshToken, for: usernameOrEmail)
            }
            await fetchCurrentUser()
            self.isAuthenticated = true
        } catch {
            self.authError = error.localizedDescription
            self.isAuthenticated = false
        }

        isLoggingIn = false
    }

    func fetchCurrentUser() async {
        do {
            let user: User = try await apiService.performRequest(endpoint: "/users/me")
            let userModel = UserModel.from(user: user)

            // Clear out existing user to avoid duplicates
            for user in users {
                modelContext.delete(user)
            }

            modelContext.insert(userModel)
            try modelContext.save()
        } catch {
            print("Failed to fetch current user: \(error.localizedDescription)")
            // Handle error, e.g., by logging out the user
            logout()
        }
    }

    func logout() {
        if let username = currentUser?.username {
            tokenManager.clearTokens(for: username)
        }
        self.isAuthenticated = false
        for user in users {
            modelContext.delete(user)
        }
        try? modelContext.save()
    }
}
