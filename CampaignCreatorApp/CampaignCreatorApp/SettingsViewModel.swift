import Foundation
import SwiftUI
import CampaignCreatorLib
import CampaignCreatorLib

@MainActor
class SettingsViewModel: ObservableObject {
    @Published var openAIApiKey = ""
    @Published var geminiApiKey = ""
    @Published var stableDiffusionApiKey = ""

    @Published var editOpenAIApiKey = ""
    @Published var editGeminiApiKey = ""
    @Published var editStableDiffusionApiKey = ""

    @Published var showingAPIKeyAlert = false
    @Published var alertMessage = ""
    @Published var showingForgetLoginAlert = false

    enum StableDiffusionEngine: String, CaseIterable, Identifiable {
        case systemDefault = ""
        case core = "core"
        case ultra = "ultra"
        case sd3 = "sd3"

        var id: String { self.rawValue }

        var displayName: String {
            switch self {
            case .systemDefault: return "System Default"
            case .core: return "Core"
            case .ultra: return "Ultra (Experimental)"
            case .sd3: return "SD3 (Experimental)"
            }
        }
    }
    @Published var selectedSdEngine: StableDiffusionEngine = .systemDefault
    private let sdEnginePreferenceKey = "StableDiffusionEnginePreference"

    @Published var serviceStatusMessage: String = "Tap Refresh to check."
    @Published var isRefreshingServiceStatus: Bool = false

    @Published var currentUser: User?

    private let lastUsernameKey = "LastUsername"
    private var apiService = CampaignCreatorLib.APIService()
    private var tokenManager = CampaignCreatorLib.UserDefaultsTokenManager()

    init() {
        loadAPIKeys()
        editOpenAIApiKey = UserDefaults.standard.string(forKey: "OPENAI_API_KEY") ?? ""
        editGeminiApiKey = UserDefaults.standard.string(forKey: "GEMINI_API_KEY") ?? ""
        editStableDiffusionApiKey = UserDefaults.standard.string(forKey: "STABLE_DIFFUSION_API_KEY") ?? ""
        loadSdEnginePreference()
        refreshServiceStatus(isInitialLoad: true)
        Task {
            await fetchCurrentUser()
        }
    }

    func fetchCurrentUser() async {
        do {
            self.currentUser = try await apiService.performRequest(endpoint: "/users/me")
        } catch {
            print("Failed to fetch current user: \(error.localizedDescription)")
        }
    }

    func forgetSavedLogin() {
        if let username = UserDefaults.standard.string(forKey: lastUsernameKey) {
            do {
                try KeychainHelper.delete(username: username)
                UserDefaults.standard.removeObject(forKey: lastUsernameKey)
                alertMessage = "Saved login credentials for '\(username)' have been forgotten."
            } catch {
                alertMessage = "Could not forget login credentials for '\(username)': \(error.localizedDescription)"
            }
        } else {
            alertMessage = "No saved login credentials to forget."
        }
        showingForgetLoginAlert = true
    }

    func loadSdEnginePreference() {
        if let rawValue = UserDefaults.standard.string(forKey: sdEnginePreferenceKey) {
            selectedSdEngine = StableDiffusionEngine(rawValue: rawValue) ?? .systemDefault
        } else {
            selectedSdEngine = .systemDefault
        }
    }

    func saveSdEnginePreference(engine: StableDiffusionEngine) {
        UserDefaults.standard.set(engine.rawValue, forKey: sdEnginePreferenceKey)
    }

    func loadAPIKeys() {
        let storedOpenAIKey = UserDefaults.standard.string(forKey: "OPENAI_API_KEY") ?? ""
        let storedGeminiKey = UserDefaults.standard.string(forKey: "GEMINI_API_KEY") ?? ""
        let storedStableDiffusionKey = UserDefaults.standard.string(forKey: "STABLE_DIFFUSION_API_KEY") ?? ""

        openAIApiKey = storedOpenAIKey.isEmpty ? "" : "••••••••••••••••"
        geminiApiKey = storedGeminiKey.isEmpty ? "" : "••••••••••••••••"
        stableDiffusionApiKey = storedStableDiffusionKey.isEmpty ? "" : "••••••••••••••••"
    }

    func saveAPIKey(_ key: String, value: String) {
        let trimmedValue = value.trimmingCharacters(in: .whitespacesAndNewlines)
        UserDefaults.standard.set(trimmedValue, forKey: key)

        var keyLabel = key.replacingOccurrences(of: "_API_KEY", with: "")
                           .replacingOccurrences(of: "_", with: " ")
                           .capitalized

        if key == "OPENAI_API_KEY" {
            openAIApiKey = trimmedValue.isEmpty ? "" : "••••••••••••••••"
            editOpenAIApiKey = trimmedValue
        } else if key == "GEMINI_API_KEY" {
            geminiApiKey = trimmedValue.isEmpty ? "" : "••••••••••••••••"
            editGeminiApiKey = trimmedValue
        } else if key == "STABLE_DIFFUSION_API_KEY" {
            stableDiffusionApiKey = trimmedValue.isEmpty ? "" : "••••••••••••••••"
            editStableDiffusionApiKey = trimmedValue
            keyLabel = "Stable Diffusion"
        }

        alertMessage = "\(keyLabel) API Key has been saved."
        showingAPIKeyAlert = true
        refreshServiceStatus()
    }

    func refreshServiceStatus(isInitialLoad: Bool = false) {
        if isInitialLoad {
            self.serviceStatusMessage = getServiceStatusString()
            return
        }

        isRefreshingServiceStatus = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.75) {
            self.serviceStatusMessage = self.getServiceStatusString()
            self.isRefreshingServiceStatus = false
            self.loadAPIKeys()
        }
    }

    private func getServiceStatusString() -> String {
        var services: [String] = []
        if !(UserDefaults.standard.string(forKey: "OPENAI_API_KEY") ?? "").isEmpty {
            services.append("OpenAI")
        }
        if !(UserDefaults.standard.string(forKey: "GEMINI_API_KEY") ?? "").isEmpty {
            services.append("Gemini")
        }
        if !(UserDefaults.standard.string(forKey: "STABLE_DIFFUSION_API_KEY") ?? "").isEmpty {
            services.append("Stable Diffusion")
        }
        return services.isEmpty ? "No AI services configured with API keys." : "Available: \(services.joined(separator: ", "))"
    }

    func logout() {
        tokenManager.clearToken()
    }
}
