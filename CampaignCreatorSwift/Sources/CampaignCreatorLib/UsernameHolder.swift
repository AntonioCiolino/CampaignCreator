import Foundation

actor UsernameHolder {
    private var username: String?

    func set(_ username: String?) {
        self.username = username
    }

    func get() -> String? {
        return username
    }
}
