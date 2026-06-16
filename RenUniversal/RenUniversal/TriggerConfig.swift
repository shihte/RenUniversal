import Foundation

struct TriggerConfig: Codable, Identifiable, Equatable {
    var id: String
    var description: String
    var enabled: Bool
    var type: TriggerType
    
    // Payload for Geometric Skill
    var geometricRule: GeometricRule?
    
    // Payload for Logic Event
    var logicRule: LogicRule?
    
    var isGeometric: Bool {
        return type == .geometric
    }
}

enum TriggerType: String, Codable, Equatable {
    case geometric
    case logic
}

struct GeometricRule: Codable, Equatable {
    var pt1: String
    var pt2: String
    var op: String // "><", "<>", ">><<", "~~"
    var value: Double
    var isPercentage: Bool
}

struct LogicCondition: Codable, Equatable, Identifiable {
    var id = UUID()
    var isNot: Bool = false
    var triggerId: String = ""
}

struct LogicRule: Codable, Equatable {
    var conditions: [LogicCondition]
    var joinOperator: String // "AND", "OR"
}
