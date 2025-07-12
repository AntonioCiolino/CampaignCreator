import SwiftUI

struct FullCharacterImageViewWrapper: View {
    let initialDisplayURL: URL?
    @State private var imageURLForSheet: URL?

    init(initialDisplayURL: URL?) {
        self.initialDisplayURL = initialDisplayURL
        self._imageURLForSheet = State(initialValue: initialDisplayURL)
    }

    var body: some View {
        FullCharacterImageView(imageURL: $imageURLForSheet)
    }
}
