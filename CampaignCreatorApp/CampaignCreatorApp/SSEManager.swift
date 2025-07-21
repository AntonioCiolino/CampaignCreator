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
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")

        // Retrieve the token from the APIService's tokenManager
        let tokenManager = CampaignCreatorLib.TokenManager()
        if let token = tokenManager.getAccessToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        dataTask = urlSession.dataTask(with: request)
        dataTask.resume()
    }

    func disconnect() {
        dataTask.cancel()
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse, completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            onOpen?()
            completionHandler(.allow)
        } else {
            onError?(NSError(domain: "SSEError", code: (response as? HTTPURLResponse)?.statusCode ?? -1, userInfo: [NSLocalizedDescriptionKey: "Failed to open SSE connection"]))
            completionHandler(.cancel)
        }
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        buffer.append(data)
        processBuffer()
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            onError?(error)
        } else {
            onComplete?()
        }
    }

    private func processBuffer() {
        let delimiter = "\n\n".data(using: .utf8)!
        while let range = buffer.range(of: delimiter) {
            let messageData = buffer.subdata(in: 0..<range.lowerBound)
            if let message = String(data: messageData, encoding: .utf8) {
                onMessage?(message)
            }
            buffer.removeSubrange(0..<range.upperBound)
        }
    }
}
