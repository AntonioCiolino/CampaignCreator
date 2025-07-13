import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class ContentViewModel: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var isLoggingIn: Bool = false
    @Published var authError: String?

    private var apiService = CampaignCreatorLib.APIService()
    private var tokenManager = CampaignCreatorLib.UserDefaultsTokenManager()

    init() {
        self.isAuthenticated = tokenManager.hasToken()
    }

    func login(usernameOrEmail: String, password: String) async {
        isLoggingIn = true
        authError = nil

        do {
            let requestBody = "username=\(usernameOrEmail)&password=\(password)"
            let bodyData = requestBody.data(using: .utf8)
            let headers = ["Content-Type": "application/x-www-form-urlencoded"]
            let response: Token = try await apiService.performRequest(endpoint: "/auth/token", method: "POST", body: bodyData, headers: headers, requiresAuth: false)
            tokenManager.setToken(response.access_token)
            self.isAuthenticated = true
        } catch {
            self.authError = error.localizedDescription
            self.isAuthenticated = false
        }

        isLoggingIn = false
    }

    func logout() {
        tokenManager.clearToken()
        self.isAuthenticated = false
    }
}
