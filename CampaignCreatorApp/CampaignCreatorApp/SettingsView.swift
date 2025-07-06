import SwiftUI
import CampaignCreatorLib

struct SettingsView: View {
    @State private var openAIApiKey = ""
    @State private var geminiApiKey = ""
    @State private var showingAPIKeyAlert = false
    @State private var alertMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Campaign Creator")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("A powerful tool for creating and managing tabletop RPG campaigns with AI assistance.")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 8)
                }
                
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("To use AI text generation features, you'll need to provide API keys for supported services:")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Text("• Create an OpenAI account at openai.com")
                            Text("• Generate an API key in your account settings")
                            Text("• Add the key below to enable AI features")
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                    }
                } header: {
                    Text("AI Service Configuration")
                }
                
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("OpenAI API Key")
                                .font(.subheadline)
                                .fontWeight(.medium)
                            
                            Spacer()
                            
                            Text(openAIApiKey.isEmpty ? "Not Set" : "Set")
                                .font(.caption)
                                .foregroundColor(openAIApiKey.isEmpty ? .red : .green)
                                .fontWeight(.medium)
                        }
                        
                        SecureField("sk-...", text: $openAIApiKey)
                            .textFieldStyle(.roundedBorder)
                            .onSubmit {
                                saveAPIKey("OPENAI_API_KEY", value: openAIApiKey)
                            }
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Gemini API Key")
                                .font(.subheadline)
                                .fontWeight(.medium)
                            
                            Spacer()
                            
                            Text(geminiApiKey.isEmpty ? "Not Set" : "Set")
                                .font(.caption)
                                .foregroundColor(geminiApiKey.isEmpty ? .red : .green)
                                .fontWeight(.medium)
                        }
                        
                        SecureField("AIza...", text: $geminiApiKey)
                            .textFieldStyle(.roundedBorder)
                            .onSubmit {
                                saveAPIKey("GEMINI_API_KEY", value: geminiApiKey)
                            }
                    }
                } header: {
                    Text("API Keys")
                } footer: {
                    Text("API keys are stored securely on your device and are only used to authenticate with the respective AI services.")
                        .font(.caption)
                }
                
                Section {
                    HStack {
                        VStack(alignment: .leading) {
                            Text("Available Services")
                                .font(.subheadline)
                                .fontWeight(.medium)
                            
                            Text(getAvailableServices())
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Button("Refresh") {
                            loadAPIKeys()
                        }
                        .buttonStyle(.bordered)
                    }
                } header: {
                    Text("Service Status")
                }
                
                Section {
                    Link(destination: URL(string: "https://github.com/AntonioCiolino/CampaignCreator")!) {
                        HStack {
                            Image(systemName: "link")
                            Text("View on GitHub")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                        }
                    }
                    
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                } header: {
                    Text("About")
                }
            }
            .navigationTitle("Settings")
            .onAppear {
                loadAPIKeys()
            }
            .alert("API Key Updated", isPresented: $showingAPIKeyAlert) {
                Button("OK") { }
            } message: {
                Text(alertMessage)
            }
        }
    }
    
    private func loadAPIKeys() {
        // Check for existing environment variables or stored keys
        // For security, we don't actually display the keys, just their status
        openAIApiKey = UserDefaults.standard.string(forKey: "OPENAI_API_KEY") ?? ""
        geminiApiKey = UserDefaults.standard.string(forKey: "GEMINI_API_KEY") ?? ""
        
        // For display purposes, we'll just show if they're set or not
        if !openAIApiKey.isEmpty {
            openAIApiKey = "••••••••••••••••" // Masked for security
        }
        if !geminiApiKey.isEmpty {
            geminiApiKey = "••••••••••••••••" // Masked for security
        }
    }
    
    private func saveAPIKey(_ key: String, value: String) {
        UserDefaults.standard.set(value, forKey: key)
        
        // Set environment variable for the current session
        setenv(key, value, 1)
        
        alertMessage = "API key for \(key.replacingOccurrences(of: "_API_KEY", with: "")) has been saved."
        showingAPIKeyAlert = true
    }
    
    private func getAvailableServices() -> String {
        let services = SecretsManager.shared.availableServices
        return services.isEmpty ? "No services configured" : services.joined(separator: ", ")
    }
}

#Preview {
    SettingsView()
}