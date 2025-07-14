import SwiftUI
import AVKit

struct LoginView: View {
    @ObservedObject var viewModel: ContentViewModel

    @State private var usernameOrEmail = ""
    @State private var password = ""
    @State private var rememberMe = false

    private let lastUsernameKey = "LastUsername"

    @State private var player: AVPlayer?
    @State private var nextPlayer: AVPlayer?
    @State private var playerOpacity: Double = 1.0
    @State private var nextPlayerOpacity: Double = 0.0
    private let videoURLs = [
        "video1.mp4",
        "video2.mp4",
        "video3.mp4"
    ]
    @State private var currentVideoIndex = 0

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                if let player = player {
                    VideoPlayer(player: player)
                        .disabled(true)
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

                Color.black.opacity(0.4).edgesIgnoringSafeArea(.all)

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

                    Image(systemName: "shield.lefthalf.fill")
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
                            .padding(.horizontal, 5)
                    }
                    .padding(.horizontal, 60)

                    if let error = viewModel.authError {
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.red.opacity(0.9))
                            .padding(8)
                            .background(Color.white.opacity(0.7))
                            .cornerRadius(5)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 40)
                    }

                    if viewModel.isLoggingIn {
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
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .onAppear {
                setupVideoPlayer()
                loadSavedCredentials()
            }
            .onChange(of: viewModel.isAuthenticated) {
                if viewModel.isAuthenticated {
                    handleLoginSuccess()
                }
            }
        }
    }

    func crossfade() {
        nextPlayer?.play()

        withAnimation(.linear(duration: 1.0)) {
            playerOpacity = 0.0
            nextPlayerOpacity = 1.0
        }

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
            } catch {
                password = ""
            }
        }
    }

    func handleLoginSuccess() {
        let userToRemember = usernameOrEmail.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !userToRemember.isEmpty else { return }

        if rememberMe {
            UserDefaults.standard.set(userToRemember, forKey: lastUsernameKey)
            do {
                try KeychainHelper.savePassword(username: userToRemember, password: password)
            } catch {
                print("Failed to save password for \\(userToRemember): \\(error.localizedDescription)")
            }
        } else {
            UserDefaults.standard.removeObject(forKey: lastUsernameKey)
            do {
                try KeychainHelper.delete(username: userToRemember)
            } catch {
                print("Failed to delete password for \\(userToRemember): \\(error.localizedDescription)")
            }
        }
    }

    func setupVideoPlayer() {
        guard !videoURLs.isEmpty else { return }

        if player == nil {
            let fileName = videoURLs[currentVideoIndex % videoURLs.count]
            let fileUrl = URL(fileURLWithPath: fileName)
            let videoName = fileUrl.deletingPathExtension().lastPathComponent
            let videoExtension = fileUrl.pathExtension
            guard let videoURL = Bundle.main.url(forResource: videoName, withExtension: videoExtension) else {
                return
            }
            let newPlayerItem = AVPlayerItem(url: videoURL)
            player = AVPlayer(playerItem: newPlayerItem)
            player?.isMuted = true
            player?.actionAtItemEnd = .none
            player?.play()
        }

        let nextVideoIndex = (currentVideoIndex + 1) % videoURLs.count
        let nextFileName = videoURLs[nextVideoIndex]
        let nextFileUrl = URL(fileURLWithPath: nextFileName)
        let nextVideoName = nextFileUrl.deletingPathExtension().lastPathComponent
        let nextVideoExtension = nextFileUrl.pathExtension
        guard let nextVideoURL = Bundle.main.url(forResource: nextVideoName, withExtension: nextVideoExtension) else {
            return
        }
        let nextPlayerItem = AVPlayerItem(url: nextVideoURL)
        nextPlayer = AVPlayer(playerItem: nextPlayerItem)
        nextPlayer?.isMuted = true
        nextPlayer?.actionAtItemEnd = .none

        NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: player?.currentItem, queue: .main) { _ in
            self.crossfade()
        }
    }

    func performLogin() {
        Task {
            await viewModel.login(usernameOrEmail: usernameOrEmail, password: password)
        }
    }
}

struct LoginView_Previews: PreviewProvider {
    static var previews: some View {
        LoginView(viewModel: ContentViewModel())
    }
}
