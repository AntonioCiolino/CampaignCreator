import Foundation

struct ImportedDocument: Codable {
    let title: String
    let content: String
}

// Example JSON structure this maps to:
// [
//   {
//     "title": "My First Note",
//     "content": "This is the content of my first note."
//   },
//   {
//     "title": "Another Note",
//     "content": "Some more interesting text here."
//   }
// ]
