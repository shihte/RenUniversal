import Foundation
import MediaPipeTasksVision
import CoreMedia
import AVFoundation

class PipelineManager: MediaPipeServiceDelegate, CameraManagerDelegate {
    
    private let cameraManager: CameraManager
    private let mediaPipeService: MediaPipeService
    private let actionEngine: ActionEngine
    private let sharedState: SharedState
    
    // Calibration properties
    private var calibrationFramesCollected = 0
    private let calibrationFramesNeeded = 30
    private var tempEyeDistances: [Float] = []
    private var tempNoseChinDistances: [Float] = []
    private var tempShoulderWidths: [Float] = []
    private var tempShoulderMidX: [Float] = []
    private var tempShoulderMidY: [Float] = []
    
    var captureSession: AVCaptureSession {
        return cameraManager.captureSession
    }
    
    init(sharedState: SharedState) {
        self.sharedState = sharedState
        self.cameraManager = CameraManager()
        self.mediaPipeService = MediaPipeService()
        self.actionEngine = ActionEngine()
        
        self.cameraManager.delegate = self
        self.mediaPipeService.delegate = self
    }
    
    func start() {
        cameraManager.startSession()
    }
    
    func stop() {
        cameraManager.stopSession()
    }
    
    func startCalibration() {
        sharedState.updateStatus(calibrating: true, calibrationProgress: 0.0)
        calibrationFramesCollected = 0
        tempEyeDistances.removeAll()
        tempNoseChinDistances.removeAll()
        tempShoulderWidths.removeAll()
        tempShoulderMidX.removeAll()
        tempShoulderMidY.removeAll()
    }
    
    // MARK: - CameraManagerDelegate
    func cameraManager(_ manager: CameraManager, didCapture sampleBuffer: CMSampleBuffer) {
        // Pass to MediaPipe for inference
        mediaPipeService.processVideoFrame(sampleBuffer)
    }
    
    // MARK: - MediaPipeServiceDelegate
    func mediaPipeService(_ service: MediaPipeService, didDetectFace faceLandmarks: [NormalizedLandmark]?, pose poseLandmarks: [NormalizedLandmark]?, in image: MPImage) {
        
        // --- 1. Calibration Phase ---
        if sharedState.calibrating {
            processCalibration(faceLandmarks: faceLandmarks, poseLandmarks: poseLandmarks)
            return
        }
        
        // --- 2. Action Engine Phase (Monitoring) ---
        guard sharedState.isCalibrated else { return }
        
        let start = DispatchTime.now()
        
        let results = actionEngine.evaluateAll(faceLandmarks: faceLandmarks, poseLandmarks: poseLandmarks, state: sharedState)
        
        var anyTriggered = false
        var activeTriggers: [String: Bool] = [:]
        var newTriggerCounts = sharedState.triggerCounts
        
        for (name, result) in results {
            let wasActive = sharedState.activeTriggers[name] ?? false
            if result && !wasActive {
                newTriggerCounts[name] = (newTriggerCounts[name] ?? 0) + 1
            }
            
            activeTriggers[name] = result
            if result {
                anyTriggered = true
            }
        }
        
        let end = DispatchTime.now()
        let nanoTime = end.uptimeNanoseconds - start.uptimeNanoseconds
        let latencyMs = Int(nanoTime / 1_000_000)
        
        // Update shared state to reflect on UI
        sharedState.updateStatus(
            latencyMs: latencyMs,
            activeTriggers: activeTriggers,
            triggerCounts: newTriggerCounts,
            faceLandmarks: faceLandmarks,
            poseLandmarks: poseLandmarks
        )
    }
    
    private func processCalibration(faceLandmarks: [NormalizedLandmark]?, poseLandmarks: [NormalizedLandmark]?) {
        guard let face = faceLandmarks, face.count > 152 else { return }
        
        let leftEye = face[33]
        let rightEye = face[263]
        let eyeDistance = sqrt(pow(rightEye.x - leftEye.x, 2) + pow(rightEye.y - leftEye.y, 2))
        
        let nose = face[1]
        let chin = face[152]
        let ncDistance = sqrt(pow(chin.x - nose.x, 2) + pow(chin.y - nose.y, 2))
        
        tempEyeDistances.append(eyeDistance)
        tempNoseChinDistances.append(ncDistance)
        
        if let pose = poseLandmarks, pose.count > 12 {
            let leftShoulder = pose[11]
            let rightShoulder = pose[12]
            
            let shoulderWidth = sqrt(pow(rightShoulder.x - leftShoulder.x, 2) + pow(rightShoulder.y - leftShoulder.y, 2))
            let midX = (leftShoulder.x + rightShoulder.x) / 2.0
            let midY = (leftShoulder.y + rightShoulder.y) / 2.0
            
            tempShoulderWidths.append(shoulderWidth)
            tempShoulderMidX.append(midX)
            tempShoulderMidY.append(midY)
        }
        
        calibrationFramesCollected += 1
        
        let progress = Double(calibrationFramesCollected) / Double(calibrationFramesNeeded) * 100.0
        sharedState.updateStatus(calibrationProgress: progress)
        
        if calibrationFramesCollected >= calibrationFramesNeeded {
            // Finish calibration
            let avgEyeDist = tempEyeDistances.reduce(0, +) / Float(tempEyeDistances.count)
            let avgNCDist = tempNoseChinDistances.reduce(0, +) / Float(tempNoseChinDistances.count)
            
            DispatchQueue.main.async {
                self.sharedState.baselineEyeDistance = avgEyeDist
                self.sharedState.baselineNoseChinDistance = avgNCDist
                
                if !self.tempShoulderWidths.isEmpty {
                    self.sharedState.baselineShoulderWidth = self.tempShoulderWidths.reduce(0, +) / Float(self.tempShoulderWidths.count)
                    self.sharedState.baselineShoulderMidpointX = self.tempShoulderMidX.reduce(0, +) / Float(self.tempShoulderMidX.count)
                    self.sharedState.baselineShoulderMidpointY = self.tempShoulderMidY.reduce(0, +) / Float(self.tempShoulderMidY.count)
                }
                
                self.sharedState.baselineFaceLandmarks = faceLandmarks
                self.sharedState.baselinePoseLandmarks = poseLandmarks
                
                self.sharedState.isCalibrated = true
                self.sharedState.updateStatus(calibrating: false)
            }
        }
    }
}
