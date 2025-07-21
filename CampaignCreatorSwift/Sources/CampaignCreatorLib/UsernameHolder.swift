import Foundation

public actor UsernameHolder {
    private var username: String?

    public func set(_ username: String?) {
        self.username = username
    }

    public func get() -> String? {
        return username
    }

    public init() {}
}
