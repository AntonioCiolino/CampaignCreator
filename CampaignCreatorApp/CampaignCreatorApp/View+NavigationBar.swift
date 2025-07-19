import SwiftUI

extension View {
    func navigationBarColor(backgroundColor: Color, tintColor: Color, titleColor: Color) -> some View {
        self.modifier(NavigationBarColor(backgroundColor: backgroundColor, tintColor: tintColor, titleColor: titleColor))
    }
}

struct NavigationBarColor: ViewModifier {
    var backgroundColor: Color
    var tintColor: Color
    var titleColor: Color

    init(backgroundColor: Color, tintColor: Color, titleColor: Color) {
        self.backgroundColor = backgroundColor
        self.tintColor = tintColor
        self.titleColor = titleColor

        let coloredAppearance = UINavigationBarAppearance()
        coloredAppearance.configureWithOpaqueBackground()
        coloredAppearance.backgroundColor = UIColor(backgroundColor)
        coloredAppearance.titleTextAttributes = [.foregroundColor: UIColor(titleColor)]
        coloredAppearance.largeTitleTextAttributes = [.foregroundColor: UIColor(titleColor)]

        UINavigationBar.appearance().standardAppearance = coloredAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = coloredAppearance
        UINavigationBar.appearance().compactAppearance = coloredAppearance
        UINavigationBar.appearance().tintColor = UIColor(tintColor)
    }

    func body(content: Content) -> some View {
        content
    }
}
