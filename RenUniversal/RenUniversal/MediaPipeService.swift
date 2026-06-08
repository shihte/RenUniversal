import Foundation
import CoreVideo
import AVFoundation
import MediaPipeTasksVision

protocol MediaPipeServiceDelegate: AnyObject {
    func mediaPipeService(_ service: MediaPipeService, didDetectFace faceLandmarks: [NormalizedLandmark]?, pose poseLandmarks: [NormalizedLandmark]?, in image: MPImage)
}

class MediaPipeService {
    weak var delegate: MediaPipeServiceDelegate?
    
    private var faceLandmarker: FaceLandmarker?
    private var poseLandmarker: PoseLandmarker?
    
    init() {
        setupFaceLandmarker()
        setupPoseLandmarker()
    }
    
    private func setupFaceLandmarker() {
        guard let modelPath = Bundle.main.path(forResource: "face_landmarker", ofType: "task") else {
            print("Failed to find face_landmarker.task in bundle. Please ensure it is added to the Xcode target.")
            return
        }
        
        do {
            let baseOptions = BaseOptions()
            baseOptions.modelAssetPath = modelPath
            
            // Using video mode for continuous stream
            let options = FaceLandmarkerOptions()
            options.baseOptions = baseOptions
            options.runningMode = .video
            options.numFaces = 1
            options.minFaceDetectionConfidence = 0.5
            options.minFacePresenceConfidence = 0.5
            options.minTrackingConfidence = 0.5
            
            faceLandmarker = try FaceLandmarker(options: options)
        } catch {
            print("Failed to create FaceLandmarker: \(error)")
        }
    }
    
    private func setupPoseLandmarker() {
        guard let modelPath = Bundle.main.path(forResource: "pose_landmarker_lite", ofType: "task") else {
            print("Failed to find pose_landmarker_lite.task in bundle. Please ensure it is added to the Xcode target.")
            return
        }
        
        do {
            let baseOptions = BaseOptions()
            baseOptions.modelAssetPath = modelPath
            
            let options = PoseLandmarkerOptions()
            options.baseOptions = baseOptions
            options.runningMode = .video
            options.minPoseDetectionConfidence = 0.5
            options.minPosePresenceConfidence = 0.5
            options.minTrackingConfidence = 0.5
            
            poseLandmarker = try PoseLandmarker(options: options)
        } catch {
            print("Failed to create PoseLandmarker: \(error)")
        }
    }
    
    func processVideoFrame(_ sampleBuffer: CMSampleBuffer) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        // Convert to MPImage
        guard let mpImage = try? MPImage(sampleBuffer: sampleBuffer) else { return }
        
        // Use presentation time stamp in milliseconds
        let timestampMs = Int(CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sampleBuffer)) * 1000)
        
        var detectedFace: [NormalizedLandmark]? = nil
        var detectedPose: [NormalizedLandmark]? = nil
        
        do {
            if let faceResult = try faceLandmarker?.detect(videoFrame: mpImage, timestampInMilliseconds: timestampMs) {
                detectedFace = faceResult.faceLandmarks.first
            }
            
            if let poseResult = try poseLandmarker?.detect(videoFrame: mpImage, timestampInMilliseconds: timestampMs) {
                detectedPose = poseResult.landmarks.first
            }
            
            DispatchQueue.main.async { [weak self] in
                guard let self = self else { return }
                self.delegate?.mediaPipeService(self, didDetectFace: detectedFace, pose: detectedPose, in: mpImage)
            }
            
        } catch {
            print("MediaPipe Detection error: \(error)")
        }
    }
}
