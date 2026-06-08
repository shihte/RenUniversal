import Foundation
import MediaPipeTasksVision

class ActionEngine {
    
    init() {
    }
    
    func evaluateAll(faceLandmarks: [NormalizedLandmark]?, poseLandmarks: [NormalizedLandmark]?, state: SharedState) -> [String: Bool] {
        var results: [String: Bool] = [:]
        var ratios: [String: Double] = [:]
        
        // Pass 1: Evaluate Geometric Triggers
        for trigger in state.triggers where trigger.enabled && trigger.type == .geometric {
            guard let rule = trigger.geometricRule else { continue }
            let (triggered, ratio) = RuleEngine.shared.evaluateGeometric(
                rule: rule,
                face: faceLandmarks,
                pose: poseLandmarks,
                baselineFace: state.baselineFaceLandmarks,
                baselinePose: state.baselinePoseLandmarks,
                viewSize: state.viewSize
            )
            results[trigger.id] = triggered
            if let r = ratio {
                ratios[trigger.id] = r
            }
        }
        
        // Pass 2: Evaluate Composite (Logic) Triggers
        for trigger in state.triggers where trigger.enabled && trigger.type == .logic {
            guard let rule = trigger.logicRule else { continue }
            let triggered = RuleEngine.shared.evaluateLogic(
                rule: rule,
                activeTriggers: results
            )
            results[trigger.id] = triggered
        }
        
        DispatchQueue.main.async {
            state.activeTriggers = results
            state.activeRatios = ratios
        }
        
        return results
    }
}
