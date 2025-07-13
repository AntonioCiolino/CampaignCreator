import Foundation
import SwiftUI

@MainActor
class MainTabViewModel: ObservableObject {
    @Published var selectedTab = 0
}
