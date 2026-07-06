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
    
    // Apps
    @Published var apps: [AppConfig] = [] {
        didSet {
            if let data = try? JSONEncoder().encode(apps) {
                UserDefaults.standard.set(data, forKey: "ren_universal_apps")
            }
        }
    }
    
    // History
    @Published var triggerCounts: [String: Int] = [:]
    
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
            // 遷移邏輯：补齊舊裝置尚未下載的新預設 Trigger
            let defaultTriggers: [TriggerConfig] = [
                TriggerConfig(id: "slouch", description: "鼻子、下巴檢測縮短（低頭）", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "f1", pt2: "f152", op: "><", value: 20.0, isPercentage: true)),
                TriggerConfig(id: "turn", description: "兩眼檢測縮短（轉頭）", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "f33", pt2: "f263", op: "><", value: 15.0, isPercentage: true)),
                TriggerConfig(id: "lean", description: "肩膀檢測前傾 (寬度放大)", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "p11", pt2: "p12", op: "<>", value: 15.0, isPercentage: true)),
                TriggerConfig(id: "tilt", description: "歪頭檢測 (兩眼 y 軸距離放大)", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "f33", pt2: "f263", op: "y<>", value: 15.0, isPercentage: false)),
                TriggerConfig(id: "bad_posture", description: "錯誤代償動作 (前傾、轉頭或歪頭)", enabled: true, type: .logic, logicRule: LogicRule(conditions: [LogicCondition(isNot: false, triggerId: "lean"), LogicCondition(isNot: false, triggerId: "turn"), LogicCondition(isNot: false, triggerId: "tilt")], joinOperator: "OR")),
                TriggerConfig(id: "ctar_tuck", description: "有效下巴內收 (低頭且未轉頭、未前傾)", enabled: true, type: .logic, logicRule: LogicRule(conditions: [LogicCondition(isNot: false, triggerId: "slouch"), LogicCondition(isNot: true, triggerId: "turn"), LogicCondition(isNot: true, triggerId: "lean")], joinOperator: "AND"))
            ]
            for def in defaultTriggers {
                if !self.triggers.contains(where: { $0.id == def.id }) {
                    self.triggers.append(def)
                }
            }
            // 更新 bad_posture 的 LogicRule 包含 tilt
            if let idx = self.triggers.firstIndex(where: { $0.id == "bad_posture" }),
               let rule = self.triggers[idx].logicRule {
                if !rule.conditions.contains(where: { $0.triggerId == "tilt" }) {
                    var updated = self.triggers[idx]
                    var conditions = rule.conditions
                    conditions.append(LogicCondition(isNot: false, triggerId: "tilt"))
                    updated.logicRule = LogicRule(conditions: conditions, joinOperator: rule.joinOperator)
                    self.triggers[idx] = updated
                }
            }
        } else {
            self.triggers = [
                TriggerConfig(id: "slouch", description: "鼻子、下巴檢測縮短（低頭）", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "f1", pt2: "f152", op: "><", value: 20.0, isPercentage: true)),
                TriggerConfig(id: "turn", description: "兩眼檢測縮短（轉頭）", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "f33", pt2: "f263", op: "><", value: 15.0, isPercentage: true)),
                TriggerConfig(id: "lean", description: "肩膀檢測前傾 (寬度放大)", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "p11", pt2: "p12", op: "<>", value: 15.0, isPercentage: true)),
                TriggerConfig(id: "tilt", description: "歪頭檢測 (兩眼 y 軸距離放大)", enabled: true, type: .geometric, geometricRule: GeometricRule(pt1: "f33", pt2: "f263", op: "y<>", value: 15.0, isPercentage: false)),
                TriggerConfig(id: "bad_posture", description: "錯誤代償動作 (前傾、轉頭或歪頭)", enabled: true, type: .logic, logicRule: LogicRule(conditions: [LogicCondition(isNot: false, triggerId: "lean"), LogicCondition(isNot: false, triggerId: "turn"), LogicCondition(isNot: false, triggerId: "tilt")], joinOperator: "OR")),
                TriggerConfig(id: "ctar_tuck", description: "有效下巴內收 (低頭且未轉頭、未前傾)", enabled: true, type: .logic, logicRule: LogicRule(conditions: [LogicCondition(isNot: false, triggerId: "slouch"), LogicCondition(isNot: true, triggerId: "turn"), LogicCondition(isNot: true, triggerId: "lean")], joinOperator: "AND"))
            ]
        }
        
        let defaultApps = [
            AppConfig(id: "ctar_counter", name: "CTAR 計數器", description: "計算下巴內收 (CTAR Tuck) 的狀態與總次數", url: "local://ctar_counter", enabled: true, iconSystemName: "chart.bar.fill"),
            AppConfig(id: "flappy_bird", name: "Flappy Ctar", description: "像素鳥！做 CTAR Tuck 讓鳥拍動翅膀飛行", url: "local://flappy_bird", enabled: true, html: BundledGames.flappyBirdHtml, iconSystemName: "paperplane.fill"),
            AppConfig(id: "dino_run", name: "Dino Run", description: "恐龍跑酷！做 CTAR Tuck 來跨越仙人掌", url: "local://dino_run", enabled: true, html: BundledGames.dinoHtml, iconSystemName: "bolt.fill")
        ]
        
        if let appsData = UserDefaults.standard.data(forKey: "ren_universal_apps"),
           let savedApps = try? JSONDecoder().decode([AppConfig].self, from: appsData) {
            self.apps = savedApps
            if self.apps.isEmpty {
                self.apps = defaultApps
            } else {
                // To help the user see the new games if they already have apps saved,
                // we'll inject them if they don't exist.
                for defApp in defaultApps {
                    if !self.apps.contains(where: { $0.id == defApp.id }) {
                        self.apps.append(defApp)
                    }
                }
            }
        } else {
            self.apps = defaultApps
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
        triggerCounts: [String: Int]? = nil,
        faceLandmarks: [NormalizedLandmark]? = nil,
        poseLandmarks: [NormalizedLandmark]? = nil
    ) {
        DispatchQueue.main.async {
            if let latencyMs = latencyMs { self.latencyMs = latencyMs }
            if let calibrating = calibrating { self.calibrating = calibrating }
            if let calibrationProgress = calibrationProgress { self.calibrationProgress = calibrationProgress }
            if let activeTriggers = activeTriggers { self.activeTriggers = activeTriggers }
            if let triggerCounts = triggerCounts { self.triggerCounts = triggerCounts }
            if let face = faceLandmarks { self.currentFaceLandmarks = face }
            if let pose = poseLandmarks { self.currentPoseLandmarks = pose }
        }
    }
}
