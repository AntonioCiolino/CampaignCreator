import Foundation

class RandomTableService {
    private var tables: [String: [String]] = [:]

    init() {
        loadTables()
    }

    private func loadTables() {
        guard let fileURL = Bundle.main.url(forResource: "tables1e", withExtension: "csv", subdirectory: "csv") else {
            print("Error: tables1e.csv not found in bundle.")
            return
        }

        do {
            let fileContent = try String(contentsOf: fileURL, encoding: .utf8)
            let lines = fileContent.components(separatedBy: .newlines)
            var currentTableName: String? = nil

            for line in lines {
                let components = line.components(separatedBy: "\t") // Tab-separated

                if components.count >= 2 {
                    let firstComponent = components[0].trimmingCharacters(in: .whitespacesAndNewlines)
                    let secondComponent = components[1].trimmingCharacters(in: .whitespacesAndNewlines)

                    if firstComponent == "d100" {
                        currentTableName = secondComponent
                        if let name = currentTableName {
                            self.tables[name] = []
                        }
                    } else if let name = currentTableName, !secondComponent.isEmpty {
                        self.tables[name]?.append(secondComponent)
                    }
                }
            }
        } catch {
            print("Error loading or parsing tables1e.csv: \(error)")
        }
    }

    func getAllTableNames() -> [String] {
        return Array(self.tables.keys).sorted()
    }

    func getRandomItem(fromTableNamed tableName: String) -> String? {
        guard let table = self.tables[tableName], !table.isEmpty else {
            return nil
        }
        return table.randomElement()
    }
}
