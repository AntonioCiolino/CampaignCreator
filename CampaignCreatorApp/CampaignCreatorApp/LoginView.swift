import SwiftUI
import CampaignCreatorLib
import AVKit // Import for VideoPlayer

struct LoginView: View {
    @ObservedObject var campaignCreator: CampaignCreator

    @State private var usernameOrEmail = ""
    @State private var password = ""
    @State private var loginAttemptError: String? = nil
    @State private var isAttemptingLogin: Bool = false

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
                    .onAppear {
                        player.play()
                    }
                    .onDisappear {
                        player.pause()
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

                Image(systemName: "shield.lefthalf.filled.dice")
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
        .onAppear(perform: setupVideoPlayer)
        .onChange(of: campaignCreator.authError) { newError in
            // This logic might need refinement based on how authError is used globally vs locally
            loginAttemptError = newError?.localizedDescription
        }
        .onChange(of: campaignCreator.isLoggingIn) { loggingInStatus in
            isAttemptingLogin = loggingInStatus
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
        player?.actionAtItemEnd = .none // Loop

        // Notification to restart video when it ends
        NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: player?.currentItem, queue: .main) { _ in
            self.player?.seek(to: .zero)
            self.player?.play()

            // Cycle to next video
            self.currentVideoIndex += 1
            let nextUrlString = self.videoURLs[self.currentVideoIndex % self.videoURLs.count]
            if let nextVideoURL = URL(string: nextUrlString) {
                self.player?.replaceCurrentItem(with: AVPlayerItem(url: nextVideoURL))
                self.player?.play() // Ensure it starts playing the new item
            }
        }
        player?.play()
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
