import SwiftUI
import CampaignCreatorLib

struct SettingsView: View {
    // Pass CampaignCreator to access logout and potentially user info
    @ObservedObject var campaignCreator: CampaignCreator

    @State private var openAIApiKey = "" // This will be masked for display
    @State private var geminiApiKey = "" // This will be masked for display
    @State private var stableDiffusionApiKey = "" // New state for Stable Diffusion key display


    // For editing, use separate @State vars that are not masked
    @State private var editOpenAIApiKey = ""
    @State private var editGeminiApiKey = ""
    @State private var editStableDiffusionApiKey = "" // New state for Stable Diffusion key

    @State private var showingAPIKeyAlert = false
    @State private var alertMessage = ""
    @State private var showingForgetLoginAlert = false // New alert for forgetting login

    // Stable Diffusion Engine Preference
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
    @State private var selectedSdEngine: StableDiffusionEngine = .systemDefault
    private let sdEnginePreferenceKey = "StableDiffusionEnginePreference"

    @State private var serviceStatusMessage: String = "Tap Refresh to check."
    @State private var isRefreshingServiceStatus: Bool = false


    private let lastUsernameKey = "LastUsername" // From LoginView, for consistency
    
    var body: some View {
        NavigationView {
            Form {
                // User Info Section (if user is logged in)
                if let user = campaignCreator.currentUser {
                    Section(header: Text("Account")) {
                        HStack {
                            VStack(alignment: .leading) {
                                Text("Logged in as:")
                                Text(user.email) // Or user.username if preferred
                                    .font(.footnote)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            // Profile Icon Display
                            AsyncImage(url: URL(string: user.avatar_url ?? "")) { phase in
                                if let image = phase.image {
                                    image.resizable()
                                        .aspectRatio(contentMode: .fill)
                                        .frame(width: 50, height: 50)
                                        .clipShape(Circle())
                                } else if phase.error != nil {
                                    Image(systemName: "person.circle.fill") // Error placeholder
                                        .resizable()
                                        .aspectRatio(contentMode: .fit)
                                        .frame(width: 50, height: 50)
                                        .foregroundColor(.gray)
                                } else {
                                    Image(systemName: "person.circle") // Default placeholder
                                        .resizable()
                                        .aspectRatio(contentMode: .fit)
                                        .frame(width: 50, height: 50)
                                        .foregroundColor(.gray)
                                }
                            }
                        }

                        Button("Change Profile Icon (Coming Soon)") {
                            // Placeholder action for now
                            alertMessage = "Profile icon customization will be available in a future update."
                            showingAPIKeyAlert = true // Re-use this alert for simplicity
                        }

                        Button("Change Password (Coming Soon)") {
                            // Placeholder action for now
                            alertMessage = "Password change functionality will be available in a future update."
                            showingAPIKeyAlert = true // Re-use this alert for simplicity
                        }

                        Button(action: {
                            campaignCreator.logout()
                            // The ContentView will react to isAuthenticated changing and show LoginView
                        }) {
                            Text("Logout")
                                .foregroundColor(.red)
                        }
                        // The "Profile Details" DisclosureGroup has been removed.
                    }
                }

                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Campaign Creator")
                            .font(.title2).fontWeight(.semibold)
                        Text("A powerful tool for creating and managing tabletop RPG campaigns with AI assistance.")
                            .font(.subheadline).foregroundColor(.secondary)
                    }
                    .padding(.vertical, 8)
                }
                
                Section(header: Text("AI Service Configuration")) {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("To use AI text generation features, you'll need to provide API keys for supported services:")
                            .font(.subheadline).foregroundColor(.secondary)
                        VStack(alignment: .leading, spacing: 8) {
                            Text("• Visit the respective AI service provider's website (e.g., OpenAI, Google AI Studio).")
                            Text("• Create an account or sign in.")
                            Text("• Navigate to the API key section and generate a new API key.")
                            Text("• Copy the generated key and paste it into the appropriate field below.")
                        }
                        .font(.caption).foregroundColor(.secondary)
                    }
                }
                
                Section(header: Text("API Keys"), footer: Text("API keys are stored securely on your device.").font(.caption)) {
                    apiKeyField(label: "OpenAI API Key", placeholder: "sk-...", apiKeyDisplay: openAIApiKey, apiKeyEdit: $editOpenAIApiKey, keyName: "OPENAI_API_KEY")
                    apiKeyField(label: "Gemini API Key", placeholder: "AIza...", apiKeyDisplay: geminiApiKey, apiKeyEdit: $editGeminiApiKey, keyName: "GEMINI_API_KEY")
                    apiKeyField(label: "Stable Diffusion API Key", placeholder: "sd-...", apiKeyDisplay: stableDiffusionApiKey, apiKeyEdit: $editStableDiffusionApiKey, keyName: "STABLE_DIFFUSION_API_KEY")
                }

                Section(header: Text("Preferences")) {
                    Picker("Preferred Stable Diffusion Engine", selection: $selectedSdEngine) {
                        ForEach(StableDiffusionEngine.allCases) { engine in
                            Text(engine.displayName).tag(engine)
                        }
                    }
                    .onChange(of: selectedSdEngine) { newEngine in
                        saveSdEnginePreference(engine: newEngine)
                    }
                    Text("Select your preferred engine for Stable Diffusion image generation. \"System Default\" will use the server's configured default.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Section(header: Text("Security")) {
                    Button(action: forgetSavedLogin) {
                        Text("Forget Saved Login Credentials")
                            .foregroundColor(.orange) // Use a distinct color
                    }
                }
                
                Section(header: Text("Service Status")) {
                    HStack {
                        VStack(alignment: .leading) {
                            Text("Available Services")
                                .font(.subheadline).fontWeight(.medium)
                            if isRefreshingServiceStatus {
                                ProgressView()
                                    .progressViewStyle(.circular)
                                    .scaleEffect(0.8)
                                Text("Checking...")
                                    .font(.caption).foregroundColor(.orange)
                            } else {
                                Text(serviceStatusMessage)
                                    .font(.caption).foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                        Button(action: { refreshServiceStatus() }) { // Wrapped in a closure
                            if isRefreshingServiceStatus {
                                ProgressView() // Show spinner inside button if preferred
                            } else {
                                Text("Refresh")
                            }
                        }
                        .buttonStyle(.bordered)
                        .disabled(isRefreshingServiceStatus)
                    }
                }
                
                DisclosureGroup("About") {
                    VStack(alignment: .leading) { // Use VStack for proper layout within DisclosureGroup
                        Link(destination: URL(string: "https://github.com/AntonioCiolino/CampaignCreator")!) {
                            HStack {
                                Image(systemName: "link")
                                Text("View on GitHub")
                                Spacer()
                                Image(systemName: "arrow.up.right.square")
                            }
                        }
                        // Add a divider for better visual separation if needed, or just rely on VStack spacing
                        // Divider()
                        HStack {
                            Text("Version")
                            Spacer()
                            Text("1.0.1") // Example version
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.top, 4) // Add a little padding at the top of the content
                }
            }
            .navigationTitle("Settings")
            .onAppear {
                loadAPIKeys() // Load current keys for display
                // Initialize edit fields with actual stored values, not the masked ones
                editOpenAIApiKey = UserDefaults.standard.string(forKey: "OPENAI_API_KEY") ?? ""
                editGeminiApiKey = UserDefaults.standard.string(forKey: "GEMINI_API_KEY") ?? ""
                editStableDiffusionApiKey = UserDefaults.standard.string(forKey: "STABLE_DIFFUSION_API_KEY") ?? ""
                loadSdEnginePreference()
                refreshServiceStatus(isInitialLoad: true) // Load initial status without delay
            }
            .alert("Login Credentials", isPresented: $showingForgetLoginAlert) { // Alert for forgetting login
                Button("OK") { }
            } message: {
                Text(alertMessage) // Re-use alertMessage for this too
            }
            .alert("API Key Saved", isPresented: $showingAPIKeyAlert) { // Specific title for API Key save
                Button("OK") { }
            } message: {
                Text(alertMessage)
            }
        }
    }
    
    private func forgetSavedLogin() {
        if let username = UserDefaults.standard.string(forKey: lastUsernameKey) {
            do {
                try KeychainHelper.delete(username: username)
                UserDefaults.standard.removeObject(forKey: lastUsernameKey)
                alertMessage = "Saved login credentials for '\(username)' have been forgotten."
                print("SettingsView: Forgotten login for \(username)")
            } catch {
                alertMessage = "Could not forget login credentials for '\(username)': \(error.localizedDescription)"
                print("SettingsView: Error forgetting login for \(username): \(error.localizedDescription)")
            }
        } else {
            alertMessage = "No saved login credentials to forget."
            print("SettingsView: No saved login to forget.")
        }
        showingForgetLoginAlert = true
    }

    private func loadSdEnginePreference() {
        if let rawValue = UserDefaults.standard.string(forKey: sdEnginePreferenceKey) {
            selectedSdEngine = StableDiffusionEngine(rawValue: rawValue) ?? .systemDefault
        } else {
            selectedSdEngine = .systemDefault
        }
    }

    private func saveSdEnginePreference(engine: StableDiffusionEngine) {
        UserDefaults.standard.set(engine.rawValue, forKey: sdEnginePreferenceKey)
        print("SettingsView: Saved Stable Diffusion Engine Preference: \(engine.displayName)")
        // Optionally, show an alert or confirmation
        // alertMessage = "Stable Diffusion engine preference saved."
        // showingAPIKeyAlert = true // Can reuse this alert if desired, or create a new one
    }

    @ViewBuilder
    private func apiKeyField(label: String, placeholder: String, apiKeyDisplay: String, apiKeyEdit: Binding<String>, keyName: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(label).font(.subheadline).fontWeight(.medium)
                Spacer()
                Text(apiKeyDisplay.isEmpty ? "Not Set" : "Set")
                    .font(.caption)
                    .foregroundColor(apiKeyDisplay.isEmpty ? .red : .green)
                    .fontWeight(.medium)
            }
            SecureField(placeholder, text: apiKeyEdit)
                .textFieldStyle(.roundedBorder)
                .onSubmit { // Save when user submits (e.g., presses return)
                    saveAPIKey(keyName, value: apiKeyEdit.wrappedValue)
                }
        }
    }

    private func loadAPIKeys() {
        let storedOpenAIKey = UserDefaults.standard.string(forKey: "OPENAI_API_KEY") ?? ""
        let storedGeminiKey = UserDefaults.standard.string(forKey: "GEMINI_API_KEY") ?? ""
        let storedStableDiffusionKey = UserDefaults.standard.string(forKey: "STABLE_DIFFUSION_API_KEY") ?? ""
        
        openAIApiKey = storedOpenAIKey.isEmpty ? "" : "••••••••••••••••"
        geminiApiKey = storedGeminiKey.isEmpty ? "" : "••••••••••••••••"
        stableDiffusionApiKey = storedStableDiffusionKey.isEmpty ? "" : "••••••••••••••••"

        // Edit fields are initialized in .onAppear directly
    }
    
    private func saveAPIKey(_ key: String, value: String) {
        let trimmedValue = value.trimmingCharacters(in: .whitespacesAndNewlines)
        UserDefaults.standard.set(trimmedValue, forKey: key)
        // setenv(key, trimmedValue, 1) // No longer needed as SecretsManager reads from UserDefaults

        // Update display state
        var keyLabel = key.replacingOccurrences(of: "_API_KEY", with: "")
                           .replacingOccurrences(of: "_", with: " ") // Make it more readable
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
            keyLabel = "Stable Diffusion" // Custom label for alert
        }
        
        alertMessage = "\(keyLabel) API Key has been saved."
        showingAPIKeyAlert = true
        refreshServiceStatus() // Refresh status after saving a key
    }
    
    private func refreshServiceStatus(isInitialLoad: Bool = false) {
        if isInitialLoad {
            // For initial load, directly update the status without delay or "checking" state
            self.serviceStatusMessage = getServiceStatusString()
            return
        }

        isRefreshingServiceStatus = true
        // Simulate a short delay to make the refresh feel more tangible
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.75) {
            self.serviceStatusMessage = getServiceStatusString()
            self.isRefreshingServiceStatus = false
            // The loadAPIKeys() call here ensures that the masked display of keys
            // also updates if a key was just entered and saved via onSubmit of a SecureField.
            // If a key is saved, the onSubmit calls saveAPIKey which updates UserDefaults.
            // Then, this refreshServiceStatus is called. loadAPIKeys() will then read the
            // new state from UserDefaults and update the "Set"/"Not Set" display.
            loadAPIKeys()
        }
    }

    private func getServiceStatusString() -> String {
        let services = SecretsManager.shared.availableServices
        return services.isEmpty ? "No AI services configured with API keys." : "Available: \(services.joined(separator: ", "))"
    }
}

#Preview {
    // Pass a CampaignCreator instance for the preview
    SettingsView(campaignCreator: CampaignCreator())
}