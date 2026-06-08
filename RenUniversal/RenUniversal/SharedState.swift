import Foundation
import Combine
import MediaPipeTasksVision

class SharedState: ObservableObject {
    @Published var isCalibrated: Bool = false
    @Published var calibrating: Bool = false
    @Published var calibrationProgress: Double = 0.0
    
    // Global Settings
    @Published var language: String = "zh-TW" // "zh-TW" or "en"
    @Published var isCameraEnabled: Bool = false
    @Published var isFaceBlurEnabled: Bool = false
    
    // Triggers (Unified Skills and Events)
    @Published var triggers: [TriggerConfig] = [] {
        didSet {
            if let data = try? JSONEncoder().encode(triggers) {
                UserDefaults.standard.set(data, forKey: "ren_universal_triggers")
            }
        }
    }
    
    // Live Landmarks for Rendering
    @Published var currentFaceLandmarks: [NormalizedLandmark]? = nil
    @Published var currentPoseLandmarks: [NormalizedLandmark]? = nil
    
    @Published var activeTriggers: [String: Bool] = [:]
    @Published var activeRatios: [String: Double] = [:]
    
    @Published var latencyMs: Int = 0
    @Published var viewSize: CGSize = CGSize(width: 400, height: 800)
    
    // Baseline metrics
    @Published var baselineEyeDistance: Float = 0.0
    @Published var baselineNoseChinDistance: Float = 0.0
    @Published var baselineShoulderWidth: Float = 0.0
    @Published var baselineShoulderMidpointX: Float = 0.0
    @Published var baselineShoulderMidpointY: Float = 0.0
    @Published var baselineFaceLandmarks: [NormalizedLandmark]? = nil
    @Published var baselinePoseLandmarks: [NormalizedLandmark]? = nil
    
    // Core Managers
    var pipelineManager: PipelineManager? = nil
    
    init() {
        if let data = UserDefaults.standard.data(forKey: "ren_universal_triggers"),
           let saved = try? JSONDecoder().decode([TriggerConfig].self, from: data) {
            self.triggers = saved
        } else {
            self.triggers = [
                TriggerConfig(id: "slouch", description: "鼻子、下巴檢測縮短（低頭）", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "f1", pt2: "f152", op: "><", value: 20.0, isPercentage: true)),
                TriggerConfig(id: "turn", description: "兩眼檢測縮短（轉頭）", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "f33", pt2: "f263", op: "><", value: 15.0, isPercentage: true)),
                TriggerConfig(id: "lean", description: "肩膀檢測前傾 (寬度放大)", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "p11", pt2: "p12", op: "<>", value: 15.0, isPercentage: true)),
                TriggerConfig(id: "bad_posture", description: "錯誤代償動作 (前傾或轉頭)", enabled: true, type: .logic, logicRule: LogicRule(conditions: [LogicCondition(isNot: false, triggerId: "lean"), LogicCondition(isNot: false, triggerId: "turn")], joinOperator: "OR")),
                TriggerConfig(id: "ctar_tuck", description: "有效下巴內收 (低頭且未轉頭、未前傾)", enabled: true, type: .logic, logicRule: LogicRule(conditions: [LogicCondition(isNot: false, triggerId: "slouch"), LogicCondition(isNot: true, triggerId: "turn"), LogicCondition(isNot: true, triggerId: "lean")], joinOperator: "AND"))
            ]
        }
    }
    
    func setupPipeline() {
        if pipelineManager == nil {
            pipelineManager = PipelineManager(sharedState: self)
        }
        pipelineManager?.start()
    }
    
    func updateStatus(
        latencyMs: Int? = nil,
        calibrating: Bool? = nil,
        calibrationProgress: Double? = nil,
        activeTriggers: [String: Bool]? = nil,
        faceLandmarks: [NormalizedLandmark]? = nil,
        poseLandmarks: [NormalizedLandmark]? = nil
    ) {
        DispatchQueue.main.async {
            if let latencyMs = latencyMs { self.latencyMs = latencyMs }
            if let calibrating = calibrating { self.calibrating = calibrating }
            if let calibrationProgress = calibrationProgress { self.calibrationProgress = calibrationProgress }
            if let activeTriggers = activeTriggers { self.activeTriggers = activeTriggers }
            if let face = faceLandmarks { self.currentFaceLandmarks = face }
            if let pose = poseLandmarks { self.currentPoseLandmarks = pose }
        }
    }
}
