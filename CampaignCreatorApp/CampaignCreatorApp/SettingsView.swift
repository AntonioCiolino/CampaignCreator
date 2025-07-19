import SwiftUI

struct SettingsView: View {
    @StateObject private var viewModel = SettingsViewModel()
    @EnvironmentObject var contentViewModel: ContentViewModel
    
    var body: some View {
        NavigationView {
            Form {
                if let user = viewModel.currentUser {
                    Section(header: Text("Account")) {
                        HStack {
                            VStack(alignment: .leading) {
                                Text("Logged in as:")
                                Text(user.email ?? "No Email")
                                    .font(.footnote)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            AsyncImage(url: URL(string: user.avatarUrl ?? "")) { phase in
                                if let image = phase.image {
                                    image.resizable()
                                        .aspectRatio(contentMode: .fill)
                                        .frame(width: 50, height: 50)
                                        .clipShape(Circle())
                                } else if phase.error != nil {
                                    Image(systemName: "person.circle.fill")
                                        .resizable()
                                        .aspectRatio(contentMode: .fit)
                                        .frame(width: 50, height: 50)
                                        .foregroundColor(.gray)
                                } else {
                                    Image(systemName: "person.circle")
                                        .resizable()
                                        .aspectRatio(contentMode: .fit)
                                        .frame(width: 50, height: 50)
                                        .foregroundColor(.gray)
                                }
                            }
                        }

                        Button("Change Profile Icon (Coming Soon)") {
                            viewModel.alertMessage = "Profile icon customization will be available in a future update."
                            viewModel.showingAPIKeyAlert = true
                        }

                        Button("Change Password (Coming Soon)") {
                            viewModel.alertMessage = "Password change functionality will be available in a future update."
                            viewModel.showingAPIKeyAlert = true
                        }

                        Button(action: {
                            viewModel.logout()
                            contentViewModel.isAuthenticated = false
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
                            Text("• Visit the respective AI service provider's website (e.g., OpenAI, Google AI Studio).")
                            Text("• Create an account or sign in.")
                            Text("• Navigate to the API key section and generate a new API key.")
                            Text("• Copy the generated key and paste it into the appropriate field below.")
                        }
                        .font(.caption).foregroundColor(.secondary)
                    }
                }
                
                Section(header: Text("API Keys"), footer: Text("API keys are stored securely on your device.").font(.caption)) {
                    apiKeyField(label: "OpenAI API Key", placeholder: "sk-...", apiKeyDisplay: viewModel.openAIApiKey, apiKeyEdit: $viewModel.editOpenAIApiKey, keyName: "OPENAI_API_KEY")
                    apiKeyField(label: "Gemini API Key", placeholder: "AIza...", apiKeyDisplay: viewModel.geminiApiKey, apiKeyEdit: $viewModel.editGeminiApiKey, keyName: "GEMINI_API_KEY")
                    apiKeyField(label: "Stable Diffusion API Key", placeholder: "sd-...", apiKeyDisplay: viewModel.stableDiffusionApiKey, apiKeyEdit: $viewModel.editStableDiffusionApiKey, keyName: "STABLE_DIFFUSION_API_KEY")
                }

                Section(header: Text("Preferences")) {
                    Picker("Preferred Stable Diffusion Engine", selection: $viewModel.selectedSdEngine) {
                        ForEach(SettingsViewModel.StableDiffusionEngine.allCases) { engine in
                            Text(engine.displayName).tag(engine)
                        }
                    }
                    .onChange(of: viewModel.selectedSdEngine) {
                        viewModel.saveSdEnginePreference(engine: viewModel.selectedSdEngine)
                    }
                    Text("Select your preferred engine for Stable Diffusion image generation. \"System Default\" will use the server's configured default.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Section(header: Text("Security")) {
                    Button(action: viewModel.forgetSavedLogin) {
                        Text("Forget Saved Login Credentials")
                            .foregroundColor(.orange)
                    }
                }
                
                Section(header: Text("Service Status")) {
                    HStack {
                        VStack(alignment: .leading) {
                            Text("Available Services")
                                .font(.subheadline).fontWeight(.medium)
                            if viewModel.isRefreshingServiceStatus {
                                ProgressView()
                                    .progressViewStyle(.circular)
                                    .scaleEffect(0.8)
                                Text("Checking...")
                                    .font(.caption).foregroundColor(.orange)
                            } else {
                                Text(viewModel.serviceStatusMessage)
                                    .font(.caption).foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                        Button(action: { viewModel.refreshServiceStatus() }) {
                            if viewModel.isRefreshingServiceStatus {
                                ProgressView()
                            } else {
                                Text("Refresh")
                            }
                        }
                        .buttonStyle(.bordered)
                        .disabled(viewModel.isRefreshingServiceStatus)
                    }
                }

                Section(header: Text("Data Management")) {
                    Button("Import/Export Data (Coming Soon)") {
                        // Placeholder action
                    }
                    .disabled(true)
                }
                
                DisclosureGroup("About") {
                    VStack(alignment: .leading) {
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
                            Text("1.0.1")
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.top, 4)
                }
            }
            .navigationTitle("Settings")
            .alert("Login Credentials", isPresented: $viewModel.showingForgetLoginAlert) {
                Button("OK") { }
            } message: {
                Text(viewModel.alertMessage)
            }
            .alert("API Key Saved", isPresented: $viewModel.showingAPIKeyAlert) {
                Button("OK") { }
            } message: {
                Text(viewModel.alertMessage)
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
                .onSubmit {
                    viewModel.saveAPIKey(keyName, value: apiKeyEdit.wrappedValue)
                }
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(ContentViewModel(modelContext: PersistenceController.shared.container.mainContext))
}
