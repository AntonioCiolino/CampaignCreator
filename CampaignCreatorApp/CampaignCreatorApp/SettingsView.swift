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

    // State for new user fields
    @State private var userDescription: String = ""
    @State private var userAppearance: String = ""
    @State private var isProfileEditing: Bool = false // To toggle edit mode for profile section

    @State private var showingAPIKeyAlert = false
    @State private var alertMessage = ""
    @State private var showingForgetLoginAlert = false // New alert for forgetting login

    private let lastUsernameKey = "LastUsername" // From LoginView, for consistency
    
    var body: some View {
        NavigationView {
            Form {
                // User Info Section (if user is logged in)
                if let user = campaignCreator.currentUser {
                    Section(header: Text("Account")) {
                        HStack {
                            Text("Logged in as:")
                            Spacer()
                            Text(user.email) // Or user.username if preferred
                                .foregroundColor(.secondary)
                        }
                        Button(action: {
                            campaignCreator.logout()
                            // The ContentView will react to isAuthenticated changing and show LoginView
                        }) {
                            Text("Logout")
                                .foregroundColor(.red)
                        }

                        // Description Field
                        DisclosureGroup("Profile Details", isExpanded: $isProfileEditing) {
                            VStack(alignment: .leading, spacing: 10) {
                                HStack {
                                    Text("Description")
                                        .font(.headline)
                                    Spacer()
                                    Button(isProfileEditing ? "Done" : "Edit") {
                                        isProfileEditing.toggle()
                                        if !isProfileEditing {
                                            // TODO: Add save logic here if needed immediately
                                            // For now, changes are local or rely on a broader save mechanism
                                            print("User description: \(userDescription)")
                                            print("User appearance: \(userAppearance)")
                                            // Potentially call a method on campaignCreator to update user
                                            // campaignCreator.updateUserDetails(description: userDescription, appearance: userAppearance)
                                        }
                                    }
                                }
                                if isProfileEditing {
                                    TextEditor(text: $userDescription)
                                        .frame(height: 100)
                                        .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                                    Divider()
                                    Text("Appearance")
                                        .font(.headline)
                                    TextField("e.g., Prefers dark themes, compact UI", text: $userAppearance)
                                        .textFieldStyle(RoundedBorderTextFieldStyle())
                                } else {
                                    Text(userDescription.isEmpty ? "No description set." : userDescription)
                                        .foregroundColor(userDescription.isEmpty ? .secondary : .primary)
                                    Divider()
                                    Text("Appearance:")
                                        .font(.headline)
                                    Text(userAppearance.isEmpty ? "No appearance preferences set." : userAppearance)
                                        .foregroundColor(userAppearance.isEmpty ? .secondary : .primary)
                                }
                            }
                            .padding(.vertical, 5)
                        }
                        .onAppear {
                            // Initialize from currentUser when the view appears or user changes
                            if let currentUser = campaignCreator.currentUser {
                                userDescription = currentUser.description ?? ""
                                userAppearance = currentUser.appearance ?? ""
                            }
                        }
                        // Add a way to save these details if needed, e.g., a Save button or auto-save logic.
                        // For now, editing is local to the @State variables.
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
                            Text(getAvailableServices())
                                .font(.caption).foregroundColor(.secondary)
                        }
                        Spacer()
                        Button("Refresh") { loadAPIKeys() }.buttonStyle(.bordered)
                    }
                }
                
                Section(header: Text("About")) {
                    Link(destination: URL(string: "https://github.com/AntonioCiolino/CampaignCreator")!) {
                        HStack { Image(systemName: "link"); Text("View on GitHub"); Spacer(); Image(systemName: "arrow.up.right.square") }
                    }
                    HStack { Text("Version"); Spacer(); Text("1.0.1").foregroundColor(.secondary) } // Example version
                }
            }
            .navigationTitle("Settings")
            .onAppear {
                loadAPIKeys() // Load current keys for display
                // Initialize edit fields with actual stored values, not the masked ones
                editOpenAIApiKey = UserDefaults.standard.string(forKey: "OPENAI_API_KEY") ?? ""
                editGeminiApiKey = UserDefaults.standard.string(forKey: "GEMINI_API_KEY") ?? ""
                editStableDiffusionApiKey = UserDefaults.standard.string(forKey: "STABLE_DIFFUSION_API_KEY") ?? ""
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
    }
    
    private func getAvailableServices() -> String {
        let services = SecretsManager.shared.availableServices
        return services.isEmpty ? "No services configured" : services.joined(separator: ", ")
    }
}

#Preview {
    // Pass a CampaignCreator instance for the preview
    SettingsView(campaignCreator: CampaignCreator())
}