import SwiftUI

extension Binding {
    /// Creates a binding by mapping an optional value to a `Bool` that is `true` if the value is non-`nil` and `false`
    /// if the value is `nil`.
    ///
    /// This is useful for bindings that control presentation, such as `sheet(isPresented:)`,
    /// when you want to base the presentation on the presence of some optional state.
    ///
    /// - Example:
    ///
    /// ```swift
    /// struct MyView: View {
    ///     @State var Payer: String?
    ///
    ///     var body: some View {
    ///         VStack {
    ///             Button("Edit Payer") {
    ///                 self.Payer = "" // Initialize with a non-nil value to present the sheet
    ///             }
    ///         }
    ///         .sheet(isPresented: $Payer.isNotNil()) {
    ///             PayerEditView(Payer: $Payer.withDefault(""))
    ///         }
    ///     }
    /// }
    /// ```
    public func isNotNil<Wrapped>() -> Binding<Bool> where Value == Wrapped? {
        Binding<Bool>(
            get: { self.wrappedValue != nil },
            set: { isNotNil in
                if !isNotNil {
                    self.wrappedValue = nil
                }
                // If you need to set to a default non-nil value when `isNotNil` becomes true,
                // you would need more context or a different approach, as this setter
                // primarily handles unsetting the value. Often, the presentation trigger
                // itself (like a button tap) will set the optional to a non-nil state.
            }
        )
    }

    /// Provides a binding to a non-optional value from an optional binding, using a default value
    /// if the optional binding's wrapped value is `nil`.
    ///
    /// This is particularly useful for controls like `TextField` or `Picker` that require a non-optional binding,
    /// but the underlying model property is optional.
    ///
    /// - Parameter defaultValue: The value to use if the `wrappedValue` of the optional binding is `nil`.
    /// - Returns: A `Binding` to a non-optional value.
    public func withDefault<Wrapped>(_ defaultValue: Wrapped) -> Binding<Wrapped> where Value == Wrapped? {
        Binding<Wrapped>(
            get: { self.wrappedValue ?? defaultValue },
            set: { newValue in
                // Check against defaultValue to decide if we should set to nil or the new value.
                // This behavior might need adjustment based on specific needs.
                // For example, if editing a TextField and it becomes empty,
                // should the optional be set to nil or an empty string?
                // Current: if newValue is the defaultValue, it could mean "reset" or "no value", so set to nil.
                // This might be too aggressive for some use cases.
                // A common alternative is to always set to `newValue`, and let `nil` be handled explicitly.
                // For a Picker, if `newValue` equals `defaultValue`, it might mean the user selected the "default" state.
                // If the default value represents a "none" or "placeholder" state that should map to `nil` in the model:
                // if newValue == defaultValue { // This requires Wrapped to be Equatable.
                // self.wrappedValue = nil
                // } else {
                // self.wrappedValue = newValue
                // }
                // Simpler approach: always set the new value. If the default value has special meaning
                // (like representing nil), the UI logic or model should handle that.
                self.wrappedValue = newValue
            }
        )
    }
}

// For the specific Picker case where `String?` needs a default for `String` binding:
// (also used for TextFields now with more robust logic)
extension Binding where Value == String? {
    func withDefault(_ defaultValue: String) -> Binding<String> {
        Binding<String>(
            get: { self.wrappedValue ?? defaultValue },
            set: {
                let trimmedValue = $0.trimmingCharacters(in: .whitespacesAndNewlines)
                // Store nil if empty, OR if it matches a non-empty default placeholder.
                if trimmedValue.isEmpty || (defaultValue.isNotEmpty && trimmedValue == defaultValue) {
                    self.wrappedValue = nil
                } else {
                    self.wrappedValue = trimmedValue
                }
            }
        )
    }
}

// Helper for non-empty string check, used by withDefault for String?
internal extension String { // Make internal if only used within this module's extensions
    var isNotEmpty: Bool { !self.isEmpty }
}
