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
    @State private var nextPlayer: AVPlayer?
    @State private var playerOpacity: Double = 1.0
    @State private var nextPlayerOpacity: Double = 0.0
    @State private var playerStatus: String = "Not started"
    private let videoURLs = [
        "video1.mp4",
        "video2.mp4",
        "video3.mp4"
    ]
    @State private var currentVideoIndex = 0

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Background Video Player
                if let player = player {
                    VideoPlayer(player: player)
                        .disabled(true) // Make it non-interactive
                        .frame(width: geometry.size.width, height: geometry.size.height)
                        .aspectRatio(contentMode: .fill)
                        .opacity(playerOpacity)
                        .clipped()
                }
                if let nextPlayer = nextPlayer {
                    VideoPlayer(player: nextPlayer)
                        .disabled(true)
                        .frame(width: geometry.size.width, height: geometry.size.height)
                        .aspectRatio(contentMode: .fill)
                        .opacity(nextPlayerOpacity)
                        .clipped()
                }

                // Overlay with a semi-transparent color to make text more readable
                Color.black.opacity(0.4).edgesIgnoringSafeArea(.all)

                // Login Form
                VStack(spacing: 20) {
                    if geometry.size.height > geometry.size.width {
                        Spacer()
                    }

                    ViewThatFits {
                        Text("Campaign Creator")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .shadow(color: .black.opacity(0.5), radius: 2, x: 1, y: 1)
                        Text("CC")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .shadow(color: .black.opacity(0.5), radius: 2, x: 1, y: 1)
                    }

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
                            .font(.headline)

                        SecureField("Password", text: $password)
                            .textContentType(.password)
                            .padding()
                            .background(Color.white.opacity(0.8))
                            .cornerRadius(8)
                            .shadow(radius: 3)
                            .font(.headline)

                        Toggle("Remember Me", isOn: $rememberMe)
                            .foregroundColor(.white)
                            .padding(.horizontal, 5) // Slight padding for the toggle text
                    }
                    .padding(.horizontal, 60)

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
                                .font(.headline)
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
                .frame(maxWidth: 500)
                .background(Color.black.opacity(0.2))
                .cornerRadius(20)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity) // Constrain ZStack to screen bounds
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
    }

    func crossfade() {
        // Start playing the next video
        nextPlayer?.play()

        // Animate the opacity of the players
        withAnimation(.linear(duration: 1.0)) {
            playerOpacity = 0.0
            nextPlayerOpacity = 1.0
        }

        // After the crossfade, swap the players and set up the next video
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.player = self.nextPlayer
            self.nextPlayer = nil
            self.playerOpacity = 1.0
            self.nextPlayerOpacity = 0.0
            self.currentVideoIndex += 1
            self.setupVideoPlayer()
        }
    }

    func loadSavedCredentials() {
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

    func handleLoginSuccess() {
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

    func setupVideoPlayer() {
        playerStatus = "Setting up video player..."
        guard !videoURLs.isEmpty else {
            playerStatus = "Error: Video URL list is empty."
            return
        }

        // Set up the first player
        if player == nil {
            let fileName = videoURLs[currentVideoIndex % videoURLs.count]
            let fileUrl = URL(fileURLWithPath: fileName)
            let videoName = fileUrl.deletingPathExtension().lastPathComponent
            let videoExtension = fileUrl.pathExtension
            guard let videoURL = Bundle.main.url(forResource: videoName, withExtension: videoExtension) else {
                print("Error: Video file not found: \(fileName)")
                playerStatus = "Error: Video file not found: \(fileName)"
                return
            }
            let newPlayerItem = AVPlayerItem(url: videoURL)
            player = AVPlayer(playerItem: newPlayerItem)
            player?.isMuted = true
            player?.actionAtItemEnd = .none
            player?.play()
        }

        // Set up the next player
        let nextVideoIndex = (currentVideoIndex + 1) % videoURLs.count
        let nextFileName = videoURLs[nextVideoIndex]
        let nextFileUrl = URL(fileURLWithPath: nextFileName)
        let nextVideoName = nextFileUrl.deletingPathExtension().lastPathComponent
        let nextVideoExtension = nextFileUrl.pathExtension
        guard let nextVideoURL = Bundle.main.url(forResource: nextVideoName, withExtension: nextVideoExtension) else {
            print("Error: Video file not found: \(nextFileName)")
            playerStatus = "Error: Video file not found: \(nextFileName)"
            return
        }
        let nextPlayerItem = AVPlayerItem(url: nextVideoURL)
        nextPlayer = AVPlayer(playerItem: nextPlayerItem)
        nextPlayer?.isMuted = true
        nextPlayer?.actionAtItemEnd = .none

        // Add observer for the current player to finish
        NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: player?.currentItem, queue: .main) { _ in
            self.crossfade()
        }
    }

    func performLogin() {
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
