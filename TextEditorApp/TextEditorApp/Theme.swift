import UIKit

struct Theme {

    // MARK: - Color Palette
    static let parchmentBackground = UIColor(red: 0.96, green: 0.94, blue: 0.88, alpha: 1.00) // Off-white/light beige
    static let editorBackground = UIColor(red: 0.98, green: 0.97, blue: 0.92, alpha: 1.00) // Slightly lighter for editor
    static let sepiaText = UIColor(red: 0.30, green: 0.25, blue: 0.20, alpha: 1.00)         // Dark, desaturated brown/sepia
    static let mutedGoldAccent = UIColor(red: 0.70, green: 0.50, blue: 0.20, alpha: 1.00)   // Muted gold/bronze
    
    static let navigationBarBackground = UIColor(red: 0.20, green: 0.40, blue: 0.40, alpha: 1.00) // Muted Teal
    static let navigationBarText = UIColor.white // For titles and button icons on the nav bar

    // MARK: - Fonts
    enum FontName {
        static let heading = "Georgia"
        static let body = "Helvetica Neue"
        static let editor = "Georgia"
        static let editorExportView = "Georgia" // Consistent with editor for markdown display
        // Monospaced alternative for ExportView if needed: "Courier New"
    }

    static func font(name: String, size: CGFloat) -> UIFont {
        return UIFont(name: name, size: size) ?? UIFont.systemFont(ofSize: size)
    }
    
    static func boldFont(name: String, size: CGFloat) -> UIFont {
        guard let regularFont = UIFont(name: name, size: size) else {
            return UIFont.boldSystemFont(ofSize: size)
        }
        
        var symbolicTraits = regularFont.fontDescriptor.symbolicTraits
        symbolicTraits.insert(.traitBold)
        
        guard let boldFontDescriptor = regularFont.fontDescriptor.withSymbolicTraits(symbolicTraits) else {
            return UIFont.boldSystemFont(ofSize: size)
        }
        return UIFont(descriptor: boldFontDescriptor, size: size)
    }

    // MARK: - Apply Global Appearance
    static func applyGlobalAppearance() {
        // Navigation Bar
        let navBarAppearance = UINavigationBarAppearance()
        navBarAppearance.configureWithOpaqueBackground() // Essential for solid color
        navBarAppearance.backgroundColor = Theme.navigationBarBackground
        navBarAppearance.titleTextAttributes = [
            .foregroundColor: Theme.navigationBarText,
            .font: Theme.font(name: FontName.heading, size: 18) // Standard title size
        ]
        // For large titles, if used
        navBarAppearance.largeTitleTextAttributes = [
            .foregroundColor: Theme.navigationBarText,
            .font: Theme.font(name: FontName.heading, size: 34) // Standard large title size
        ]
        
        // Bar button item appearance (icons and text)
        let barButtonItemAppearance = UIBarButtonItem.appearance(whenContainedInInstancesOf: [UINavigationBar.self])
        barButtonItemAppearance.tintColor = Theme.navigationBarText // For SF Symbols / template images

        // For text-based bar button items, if any are not using images
        let barButtonTextAttributes: [NSAttributedString.Key: Any] = [
            .foregroundColor: Theme.navigationBarText,
            .font: Theme.font(name: FontName.body, size: 17) // Standard bar button text size
        ]
        barButtonItemAppearance.setTitleTextAttributes(barButtonTextAttributes, for: .normal)
        barButtonItemAppearance.setTitleTextAttributes(barButtonTextAttributes, for: .highlighted)


        UINavigationBar.appearance().standardAppearance = navBarAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navBarAppearance // For consistency when scrolling
        UINavigationBar.appearance().compactAppearance = navBarAppearance // For compact nav bars

        // General tint for other UI elements if needed (e.g., UISwitch, UISlider)
        // UIView.appearance().tintColor = Theme.mutedGoldAccent // Be careful with this, can be too broad.
    }
}
