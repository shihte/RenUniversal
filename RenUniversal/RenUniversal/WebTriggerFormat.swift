import Foundation

struct WebSkillFormat: Codable, Identifiable {
    var id: String { name }
    var name: String
    var description: String
    var enabled: Bool
    var distance: [String: String]
    var compare: String
    var threshold: Double
    var is_percentage: Bool
}

struct WebEventFormat: Codable, Identifiable {
    var id: String { name }
    var name: String
    var description: String
    var enabled: Bool
    var rule_syntax: String
}

struct ProfileBundle: Codable {
    var skills: [WebSkillFormat]
    var events: [WebEventFormat]
    var apps: [AppConfig]
}

extension TriggerConfig {
    func toWebEvent() -> WebEventFormat? {
        guard self.type == .logic, let rule = self.logicRule else { return nil }
        let syntax = rule.conditions.map { cond in
            return cond.isNot ? "(!\(cond.triggerId))" : cond.triggerId
        }.joined(separator: " \(rule.joinOperator) ")
        return WebEventFormat(name: self.id, description: self.description, enabled: self.enabled, rule_syntax: syntax)
    }
    
    static func fromWebEvent(_ web: WebEventFormat) -> TriggerConfig {
        var joinOp = "AND"
        var conditionsStr = [String]()
        if web.rule_syntax.contains(" OR ") {
            joinOp = "OR"
            conditionsStr = web.rule_syntax.components(separatedBy: " OR ")
        } else {
            conditionsStr = web.rule_syntax.components(separatedBy: " AND ")
        }
        
        let conditions = conditionsStr.map { str -> LogicCondition in
            let trimmed = str.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.hasPrefix("(!") && trimmed.hasSuffix(")") {
                let id = String(trimmed.dropFirst(2).dropLast(1))
                return LogicCondition(isNot: true, triggerId: id)
            } else {
                return LogicCondition(isNot: false, triggerId: trimmed)
            }
        }
        return TriggerConfig(id: web.name, description: web.description, enabled: web.enabled, type: .logic, logicRule: LogicRule(conditions: conditions, joinOperator: joinOp))
    }
    
    func toWebSkill() -> WebSkillFormat? {
        guard self.type == .geometric, let rule = self.geometricRule else { return nil }
        return WebSkillFormat(name: self.id, description: self.description, enabled: self.enabled, distance: ["pt1": rule.pt1, "pt2": rule.pt2], compare: rule.op, threshold: rule.value, is_percentage: rule.isPercentage)
    }
    
    static func fromWebSkill(_ web: WebSkillFormat) -> TriggerConfig {
        let pt1 = web.distance["pt1"] ?? ""
        let pt2 = web.distance["pt2"] ?? ""
        return TriggerConfig(id: web.name, description: web.description, enabled: web.enabled, type: .geometric, geometricRule: GeometricRule(pt1: pt1, pt2: pt2, op: web.compare, value: web.threshold, isPercentage: web.is_percentage))
    }
}
