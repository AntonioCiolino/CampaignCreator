import Foundation
import CampaignCreatorLib

class SSEManager: NSObject, URLSessionDataDelegate {
    private var urlSession: URLSession!
    private var dataTask: URLSessionDataTask!
    private var buffer = Data()

    var onOpen: (() -> Void)?
    var onMessage: ((String) -> Void)?
    var onError: ((Error) -> Void)?
    var onComplete: (() -> Void)?

    override init() {
        super.init()
        let configuration = URLSessionConfiguration.default
        self.urlSession = URLSession(configuration: configuration, delegate: self, delegateQueue: nil)
    }

    func connect(to url: URL) {
        print("SSEManager: Connecting to URL: \(url)")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Retrieve the token from the APIService's tokenManager
        let tokenManager = CampaignCreatorLib.TokenManager()
        if let token = tokenManager.getAccessToken() {
            print("SSEManager: Adding token to request")
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else {
            print("SSEManager: No token found")
        }

        dataTask = urlSession.dataTask(with: request)
        dataTask.resume()
    }

    func disconnect() {
        dataTask.cancel()
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse, completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        print("SSEManager: Received response: \(response)")
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            print("SSEManager: Connection opened")
            DispatchQueue.main.async {
                self.onOpen?()
            }
            completionHandler(.allow)
        } else {
            print("SSEManager: Failed to open connection. Status code: \((response as? HTTPURLResponse)?.statusCode ?? -1)")
            DispatchQueue.main.async {
                self.onError?(NSError(domain: "SSEError", code: (response as? HTTPURLResponse)?.statusCode ?? -1, userInfo: [NSLocalizedDescriptionKey: "Failed to open SSE connection"]))
            }
            completionHandler(.cancel)
        }
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        print("SSEManager: Received data: \(String(data: data, encoding: .utf8) ?? "Unable to decode data")")
        buffer.append(data)
        processBuffer()
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            print("SSEManager: Connection completed with error: \(error)")
            DispatchQueue.main.async {
                self.onError?(error)
            }
        } else {
            print("SSEManager: Connection completed successfully")
            DispatchQueue.main.async {
                self.onComplete?()
            }
        }
    }

    private func processBuffer() {
        let delimiter = "\n\n".data(using: .utf8)!
        while let range = buffer.range(of: delimiter) {
            let messageData = buffer.subdata(in: 0..<range.lowerBound)
            if let message = String(data: messageData, encoding: .utf8) {
                DispatchQueue.main.async {
                    self.onMessage?(message)
                }
            }
            buffer.removeSubrange(0..<range.upperBound)
        }
    }
}
