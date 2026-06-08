import AVFoundation
import CoreImage

protocol CameraManagerDelegate: AnyObject {
    func cameraManager(_ manager: CameraManager, didCapture sampleBuffer: CMSampleBuffer)
}

class CameraManager: NSObject {
    weak var delegate: CameraManagerDelegate?
    
    let captureSession = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private var isSessionRunning = false
    private let videoQueue = DispatchQueue(label: "com.renuniversal.cameraQueue", qos: .userInteractive)
    
    override init() {
        super.init()
        setupCamera()
    }
    
    private func setupCamera() {
        captureSession.beginConfiguration()
        captureSession.sessionPreset = .vga640x480 // MediaPipe typically works well with smaller inputs
        
        // Setup Input (Front Camera)
        guard let videoDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front),
              let videoDeviceInput = try? AVCaptureDeviceInput(device: videoDevice),
              captureSession.canAddInput(videoDeviceInput) else {
            print("Failed to setup camera input")
            captureSession.commitConfiguration()
            return
        }
        captureSession.addInput(videoDeviceInput)
        
        // Setup Output
        videoOutput.setSampleBufferDelegate(self, queue: videoQueue)
        videoOutput.alwaysDiscardsLateVideoFrames = true
        videoOutput.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32BGRA)]
        
        guard captureSession.canAddOutput(videoOutput) else {
            print("Failed to add video output")
            captureSession.commitConfiguration()
            return
        }
        captureSession.addOutput(videoOutput)
        
        // Fix Orientation to Portrait
        if let connection = videoOutput.connection(with: .video) {
            if connection.isVideoOrientationSupported {
                connection.videoOrientation = .portrait
            }
            if connection.isVideoMirroringSupported {
                connection.isVideoMirrored = true // Mirror front camera
            }
        }
        
        captureSession.commitConfiguration()
    }
    
    func startSession() {
        if !isSessionRunning {
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                guard let self = self, granted else {
                    print("Camera access denied")
                    return
                }
                DispatchQueue.global(qos: .background).async {
                    self.captureSession.startRunning()
                    self.isSessionRunning = true
                }
            }
        }
    }
    
    func stopSession() {
        if isSessionRunning {
            DispatchQueue.global(qos: .background).async {
                self.captureSession.stopRunning()
                self.isSessionRunning = false
            }
        }
    }
}

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        delegate?.cameraManager(self, didCapture: sampleBuffer)
    }
}
