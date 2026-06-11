import Foundation

struct AppConfig: Codable, Identifiable, Equatable {
    var id: String
    var name: String
    var description: String
    var url: String
    var enabled: Bool
    var html: String?
}
