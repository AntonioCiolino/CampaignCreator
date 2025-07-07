import SwiftUI
import CampaignCreatorLib
import AVKit // Import for VideoPlayer

struct LoginView: View {
    @ObservedObject var campaignCreator: CampaignCreator

    @State private var usernameOrEmail = ""
    @State private var password = ""
    @State private var rememberMe = false // New state for Remember Me
    @State private var loginAttemptError: String? = nil
    @State private var isAttemptingLogin: Bool = false

    private let lastUsernameKey = "LastUsername" // UserDefaults key for username

    // Video player state
    @State private var player: AVPlayer?
    private let videoURLs = [
        "https://campaigncreator.onrender.com/assets/videos/Dnd5e_realistic_high_202506282155_3836j.mp4",
        "https://campaigncreator.onrender.com/assets/videos/The_goblin.mp4",
        "https://campaigncreator.onrender.com/assets/videos/Dandelions_in_the_wind.mp4"
    ]
    @State private var currentVideoIndex = 0

    var body: some View {
        ZStack {
            // Background Video Player
            if let player = player {
                VideoPlayer(player: player)
                    .disabled(true) // Make it non-interactive
                    .aspectRatio(contentMode: .fill)
                    .edgesIgnoringSafeArea(.all)
                    .opacity(0.3) // Adjust opacity to make it a background
                    .aspectRatio(contentMode: .fill)
                    .edgesIgnoringSafeArea(.all)
                    .opacity(0.3) // Adjust opacity to make it a background
                    // .onAppear { player.play() } // player.play() is now called reliably in setupVideoPlayer
                    .onDisappear {
                        player.pause()
                        // Remove observer when the view disappears
                        NotificationCenter.default.removeObserver(self, name: .AVPlayerItemDidPlayToEndTime, object: nil)
                    }
            }

            // Overlay with a semi-transparent color to make text more readable
            Color.black.opacity(0.4).edgesIgnoringSafeArea(.all)

            // Login Form
            VStack(spacing: 20) {
                Spacer()

                Text("Campaign Creator")
                    .font(.system(size: 40, weight: .bold, design: .serif)) // Thematic font
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.5), radius: 2, x: 1, y: 1)

                Image(systemName: "shield.lefthalf.fill") // Corrected SF Symbol
                    .font(.system(size: 60))
                    .foregroundColor(.white)
                    .padding(.bottom, 20)
                    .shadow(color: .black.opacity(0.5), radius: 2, x: 1, y: 1)

                VStack(spacing: 15) {
                    TextField("Username or Email", text: $usernameOrEmail)
                        .keyboardType(.emailAddress)
                        .textContentType(.username)
                        .autocapitalization(.none)
                        .padding()
                        .background(Color.white.opacity(0.8))
                        .cornerRadius(8)
                        .shadow(radius: 3)

                    SecureField("Password", text: $password)
                        .textContentType(.password)
                        .padding()
                        .background(Color.white.opacity(0.8))
                        .cornerRadius(8)
                        .shadow(radius: 3)

                    Toggle("Remember Me", isOn: $rememberMe)
                        .foregroundColor(.white)
                        .padding(.horizontal, 5) // Slight padding for the toggle text
                }
                .padding(.horizontal, 40)

                if let error = loginAttemptError {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.red.opacity(0.9))
                        .padding(8)
                        .background(Color.white.opacity(0.7))
                        .cornerRadius(5)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 40)
                }

                if isAttemptingLogin {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(1.5)
                        .padding(.top, 10)
                } else {
                    Button(action: performLogin) {
                        Text("Login")
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .foregroundColor(.white)
                            .background(Color.blue.opacity(0.9))
                            .cornerRadius(8)
                            .shadow(radius: 5)
                    }
                    .padding(.horizontal, 40)
                    .padding(.top, 10)
                    .disabled(usernameOrEmail.isEmpty || password.isEmpty)
                }

                Spacer()
                Spacer()
            }
            .padding()
        }
        .onAppear {
            setupVideoPlayer()
            loadSavedCredentials()
        }
        .onChange(of: campaignCreator.authError) { newError in
            loginAttemptError = newError?.localizedDescription
        }
        .onChange(of: campaignCreator.isLoggingIn) { loggingInStatus in
            isAttemptingLogin = loggingInStatus
        }
        .onChange(of: campaignCreator.isAuthenticated) { isAuthenticated in
            if isAuthenticated {
                handleLoginSuccess()
            }
        }
    }

    private func loadSavedCredentials() {
        if let lastUser = UserDefaults.standard.string(forKey: lastUsernameKey) {
            usernameOrEmail = lastUser
            do {
                password = try KeychainHelper.loadPassword(username: lastUser)
                rememberMe = true
                print("LoginView: Loaded saved credentials for \(lastUser)")
            } catch KeychainHelper.KeychainError.itemNotFound {
                print("LoginView: No saved password found for \(lastUser).")
            } catch {
                print("LoginView: Error loading password for \(lastUser): \(error.localizedDescription)")
                password = ""
            }
        } else {
            print("LoginView: No last username found in UserDefaults.")
        }
    }

    private func handleLoginSuccess() {
        let userToRemember = usernameOrEmail.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !userToRemember.isEmpty else { return }

        if rememberMe {
            UserDefaults.standard.set(userToRemember, forKey: lastUsernameKey)
            do {
                try KeychainHelper.savePassword(username: userToRemember, password: password)
                print("LoginView: Saved credentials for \(userToRemember)")
            } catch {
                print("LoginView: Failed to save password for \(userToRemember): \(error.localizedDescription)")
            }
        } else {
            UserDefaults.standard.removeObject(forKey: lastUsernameKey)
            do {
                try KeychainHelper.delete(username: userToRemember)
                print("LoginView: Cleared saved credentials for \(userToRemember)")
            } catch {
                print("LoginView: Failed to delete password for \(userToRemember): \(error.localizedDescription)")
            }
        }
    }

    private func setupVideoPlayer() {
        guard !videoURLs.isEmpty else { return }
        let urlString = videoURLs[currentVideoIndex % videoURLs.count]
        guard let videoURL = URL(string: urlString) else {
            print("Error: Invalid video URL: \(urlString)")
            return
        }
        let newPlayerItem = AVPlayerItem(url: videoURL)
        if player == nil {
            player = AVPlayer(playerItem: newPlayerItem)
        } else {
            player?.replaceCurrentItem(with: newPlayerItem)
        }

        player?.isMuted = true
        player?.actionAtItemEnd = .none

        NotificationCenter.default.removeObserver(self, name: .AVPlayerItemDidPlayToEndTime, object: nil)
        NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: player?.currentItem, queue: .main) { _ in
            print("LoginView: Video item did play to end. Current index: \(self.currentVideoIndex). Setting up next video.")
            self.currentVideoIndex += 1
            self.setupVideoPlayer()
        }

        DispatchQueue.main.async {
            self.player?.play()
            if self.player?.rate == 0.0 && self.player?.error == nil {
                 print("LoginView: player.play() called, but rate is 0 and no immediate error.")
            } else if let error = self.player?.error {
                print("LoginView: Player error on attempting play: \(error.localizedDescription)")
            } else {
                print("LoginView: player.play() called, current rate: \(self.player?.rate ?? 0).")
            }
        }
    }

    private func performLogin() {
        loginAttemptError = nil
        // isAttemptingLogin state is now driven by observing campaignCreator.isLoggingIn
        Task {
            await campaignCreator.login(usernameOrEmail: usernameOrEmail, password: password)
        }
    }
}

struct LoginView_Previews: PreviewProvider {
    static var previews: some View {
        LoginView(campaignCreator: CampaignCreator())
    }
}
