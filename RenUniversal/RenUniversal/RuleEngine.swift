import Foundation
import MediaPipeTasksVision
import CoreGraphics

class RuleEngine {
    static let shared = RuleEngine()
    
    func evaluateGeometric(rule: GeometricRule, face: [NormalizedLandmark]?, pose: [NormalizedLandmark]?, baselineFace: [NormalizedLandmark]?, baselinePose: [NormalizedLandmark]?, viewSize: CGSize) -> (Bool, Double?) {
        let threshold = Float(rule.value)
        let isPct = rule.isPercentage
        let op = rule.op
        
        let scaledThreshold = isPct ? threshold / 100.0 : threshold
        let w = viewSize.width
        let h = viewSize.height
        
        var baseOp = op
        var axis: String? = nil
        if op.hasPrefix("x") {
            axis = "x"
            baseOp = String(op.dropFirst())
        } else if op.hasPrefix("y") {
            axis = "y"
            baseOp = String(op.dropFirst())
        }
        
        let c1 = getCoord(id: rule.pt1, face: face, pose: pose)
        let c2 = getCoord(id: rule.pt2, face: face, pose: pose)
        let b1 = getCoord(id: rule.pt1, face: baselineFace, pose: baselinePose)
        let b2 = getCoord(id: rule.pt2, face: baselineFace, pose: baselinePose)
        
        guard let c1 = c1, let c2 = c2, let b1 = b1, let b2 = b2 else { return (false, nil) }
        
        let d_curr = distanceInScreen(c1, c2, w: w, h: h, axis: axis)
        let d_base = distanceInScreen(b1, b2, w: w, h: h, axis: axis)
        
        if d_base == 0 { return (false, nil) }
        
        if baseOp == "~~" {
            let scaled_radius = isPct ? (scaledThreshold * d_base) : scaledThreshold
            let dist1 = distanceInScreen(c1, b1, w: w, h: h, axis: axis)
            let dist2 = distanceInScreen(c2, b2, w: w, h: h, axis: axis)
            let max_dist = max(dist1, dist2)
            let ratio = scaled_radius > 0 ? Double(max_dist / scaled_radius) * 100.0 : 0
            return (dist1 > scaled_radius || dist2 > scaled_radius, ratio)
        } else {
            let absoluteChange = d_curr - d_base
            let pctChange = Double(absoluteChange / d_base) * 100.0
            
            if isPct {
                if baseOp == "><" { return (pctChange <= -Double(threshold), pctChange) }
                if baseOp == "<>" { return (pctChange >= Double(threshold), pctChange) }
                if baseOp == ">><<" { return (abs(pctChange) >= Double(threshold), pctChange) }
            } else {
                if baseOp == "><" { return (Double(absoluteChange) <= -Double(threshold), pctChange) }
                if baseOp == "<>" { return (Double(absoluteChange) >= Double(threshold), pctChange) }
                if baseOp == ">><<" { return (abs(Double(absoluteChange)) >= Double(threshold), pctChange) }
            }
        }
        
        return (false, nil)
    }
    
    func evaluateLogic(rule: LogicRule, activeTriggers: [String: Bool]) -> Bool {
        guard !rule.conditions.isEmpty else { return false }
        
        let results = rule.conditions.map { cond -> Bool in
            let baseResult = activeTriggers[cond.triggerId] ?? false
            return cond.isNot ? !baseResult : baseResult
        }
        
        if rule.joinOperator == "OR" {
            return results.contains(true)
        } else {
            return !results.contains(false) // AND
        }
    }
    
    // MARK: - Coordinate Helpers
    
    private func getCoord(id: String, face: [NormalizedLandmark]?, pose: [NormalizedLandmark]?) -> CGPoint? {
        let firstPart = id.components(separatedBy: " ").first ?? id
        let lower = firstPart.lowercased()
        let isPose = lower.hasPrefix("p")
        let isFace = lower.hasPrefix("f")
        let idxStr = lower.replacingOccurrences(of: "p", with: "").replacingOccurrences(of: "f", with: "").trimmingCharacters(in: .whitespacesAndNewlines)
        guard let idx = Int(idxStr) else { return nil }
        
        if isPose {
            if let p = pose, idx < p.count {
                return CGPoint(x: CGFloat(p[idx].x), y: CGFloat(p[idx].y))
            }
        } else if isFace {
            if let f = face, idx < f.count {
                return CGPoint(x: CGFloat(f[idx].x), y: CGFloat(f[idx].y))
            }
        } else {
            if let p = pose, idx < p.count {
                return CGPoint(x: CGFloat(p[idx].x), y: CGFloat(p[idx].y))
            }
        }
        return nil
    }
    
    func getUsedPoints(from trigger: TriggerConfig) -> [String] {
        guard trigger.type == .geometric, let rule = trigger.geometricRule else { return [] }
        return [rule.pt1, rule.pt2]
    }
    
    private func distance(_ p1: CGPoint, _ p2: CGPoint) -> Float {
        return Float(hypot(p1.x - p2.x, p1.y - p2.y))
    }
    
    private func distanceInScreen(_ p1: CGPoint, _ p2: CGPoint, w: CGFloat, h: CGFloat, axis: String? = nil) -> Float {
        let dx = (p1.x - p2.x) * w
        let dy = (p1.y - p2.y) * h
        if axis == "x" {
            return Float(abs(dx))
        } else if axis == "y" {
            return Float(abs(dy))
        }
        return Float(hypot(dx, dy))
    }
    
    private func distanceToSegment(p: CGPoint, v: CGPoint, w: CGPoint) -> Float {
        let l2 = distance(v, w) * distance(v, w)
        if l2 == 0 { return distance(p, v) }
        
        var t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / CGFloat(l2)
        t = max(0, min(1, t))
        
        let projection = CGPoint(x: v.x + t * (w.x - v.x), y: v.y + t * (w.y - v.y))
        return distance(p, projection)
    }
}
