import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class ContentViewModel: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var isLoggingIn: Bool = false
    @Published var authError: String?
    @Published var currentUser: User?

    private var apiService = CampaignCreatorLib.APIService()
    private var tokenManager = CampaignCreatorLib.UserDefaultsTokenManager()

    init() {
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
            let requestBody = "username=\(usernameOrEmail)&password=\(password)"
            let bodyData = requestBody.data(using: .utf8)
            let headers = ["Content-Type": "application/x-www-form-urlencoded"]
            let response: CampaignCreatorLib.Token = try await apiService.performRequest(endpoint: "/auth/token", method: "POST", body: bodyData, headers: headers, requiresAuth: false)
            tokenManager.setToken(response.accessToken)
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
            self.currentUser = try await apiService.performRequest(endpoint: "/users/me")
        } catch {
            print("Failed to fetch current user: \(error.localizedDescription)")
            // Handle error, e.g., by logging out the user
            logout()
        }
    }

    func logout() {
        tokenManager.clearToken()
        self.isAuthenticated = false
        self.currentUser = nil
    }
}
