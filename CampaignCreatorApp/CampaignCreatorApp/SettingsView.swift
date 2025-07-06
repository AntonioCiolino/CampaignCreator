import SwiftUI
import CampaignCreatorLib

struct SettingsView: View {
    // Pass CampaignCreator to access logout and potentially user info
    @ObservedObject var campaignCreator: CampaignCreator

    @State private var openAIApiKey = "" // This will be masked for display
    @State private var geminiApiKey = "" // This will be masked for display

    // For editing, use separate @State vars that are not masked
    @State private var editOpenAIApiKey = ""
    @State private var editGeminiApiKey = ""

    @State private var showingAPIKeyAlert = false
    @State private var alertMessage = ""
    
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
                            Text("• Create an OpenAI account at openai.com")
                            Text("• Generate an API key")
                            Text("• Add the key below")
                        }
                        .font(.caption).foregroundColor(.secondary)
                    }
                }
                
                Section(header: Text("API Keys"), footer: Text("API keys are stored securely on your device.").font(.caption)) {
                    apiKeyField(label: "OpenAI API Key", placeholder: "sk-...", apiKeyDisplay: openAIApiKey, apiKeyEdit: $editOpenAIApiKey, keyName: "OPENAI_API_KEY")
                    apiKeyField(label: "Gemini API Key", placeholder: "AIza...", apiKeyDisplay: geminiApiKey, apiKeyEdit: $editGeminiApiKey, keyName: "GEMINI_API_KEY")
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
            }
            .alert("API Key", isPresented: $showingAPIKeyAlert) { // Changed title
                Button("OK") { }
            } message: {
                Text(alertMessage)
            }
        }
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
        
        openAIApiKey = storedOpenAIKey.isEmpty ? "" : "••••••••••••••••"
        geminiApiKey = storedGeminiKey.isEmpty ? "" : "••••••••••••••••"

        // editOpenAIApiKey = storedOpenAIKey // Already done in onAppear
        // editGeminiApiKey = storedGeminiKey
    }
    
    private func saveAPIKey(_ key: String, value: String) {
        let trimmedValue = value.trimmingCharacters(in: .whitespacesAndNewlines)
        UserDefaults.standard.set(trimmedValue, forKey: key)
        setenv(key, trimmedValue, 1) // For current session if library uses getenv
        
        // Update display state
        if key == "OPENAI_API_KEY" {
            openAIApiKey = trimmedValue.isEmpty ? "" : "••••••••••••••••"
            editOpenAIApiKey = trimmedValue // Keep edit field synced
        } else if key == "GEMINI_API_KEY" {
            geminiApiKey = trimmedValue.isEmpty ? "" : "••••••••••••••••"
            editGeminiApiKey = trimmedValue // Keep edit field synced
        }
        
        alertMessage = "\(key.replacingOccurrences(of: "_API_KEY", with: "")) API Key has been saved."
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