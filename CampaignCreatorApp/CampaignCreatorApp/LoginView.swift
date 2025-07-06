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
                    // .onAppear { player.play() } // player.play() is now called reliably in setupVideoPlayer
                    .onDisappear {
                        player?.pause()
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
            // This logic might need refinement based on how authError is used globally vs locally
            loginAttemptError = newError?.localizedDescription
        }
        .onChange(of: campaignCreator.isLoggingIn) { loggingInStatus in
            isAttemptingLogin = loggingInStatus
        }
        // When login succeeds and isAuthenticated becomes true, this view will disappear.
        // That's a good time to save credentials if "Remember Me" is checked.
        .onChange(of: campaignCreator.isAuthenticated) { isAuthenticated in
            if isAuthenticated {
                handleLoginSuccess()
            }
        }
    }

    private func loadSavedCredentials() {
        // Load last username
        if let lastUser = UserDefaults.standard.string(forKey: lastUsernameKey) {
            usernameOrEmail = lastUser
            // Attempt to load password only if a username was saved
            do {
                password = try KeychainHelper.loadPassword(username: lastUser)
                rememberMe = true // If password loaded, assume "Remember Me" was on
                print("LoginView: Loaded saved credentials for \(lastUser)")
            } catch KeychainHelper.KeychainError.itemNotFound {
                print("LoginView: No saved password found for \(lastUser).")
                // No password, so ensure "Remember Me" is off unless user explicitly sets it
                // rememberMe = false // Let it default to false or prior state
            } catch {
                print("LoginView: Error loading password for \(lastUser): \(error.localizedDescription)")
                // Clear potentially stale password and ensure rememberMe is off
                password = ""
                // rememberMe = false
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
                // Optionally, inform the user that saving failed
            }
        } else {
            // If "Remember Me" is off, remove saved credentials for this username
            UserDefaults.standard.removeObject(forKey: lastUsernameKey) // Or just remove for current user if logic is specific
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

        player?.isMuted = true // Mute background video
        player?.actionAtItemEnd = .none // Crucial for manual looping/cycling

        // Remove ALL previous AVPlayerItemDidPlayToEndTime observers registered by this instance of LoginView
        // to prevent multiple handlers firing if setupVideoPlayer is called again (e.g., on view re-appear or error).
        NotificationCenter.default.removeObserver(self, name: .AVPlayerItemDidPlayToEndTime, object: nil)

        // Add a new observer specifically for the current player item.
        NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: player?.currentItem, queue: .main) { [weak self] _ in
            guard let self = self else { return }
            print("LoginView: Video item did play to end. Current index: \(self.currentVideoIndex). Setting up next video.")
            self.currentVideoIndex += 1
            // Call setupVideoPlayer again to load and play the next video.
            // This will also correctly set up the observer for the new player item.
            self.setupVideoPlayer()
        }

        // Ensure player starts playing on the main thread
        DispatchQueue.main.async {
            self.player?.play()
            // Simple check to see if playback started. More robust checks involve observing player.timeControlStatus or item.status.
            if self.player?.rate == 0.0 && self.player?.error == nil {
                 print("LoginView: player.play() called, but rate is 0 and no immediate error. Video might be buffering or item status not ready.")
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
