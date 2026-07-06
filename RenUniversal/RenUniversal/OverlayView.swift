import SwiftUI
import MediaPipeTasksVision

struct OverlayView: View {
    @ObservedObject var state: SharedState
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Face Blur Overlay
                if state.isFaceBlurEnabled, let face = state.currentFaceLandmarks, !face.isEmpty {
                    let minX = face.map { CGFloat($0.x) }.min() ?? 0
                    let maxX = face.map { CGFloat($0.x) }.max() ?? 0
                    let minY = face.map { CGFloat($0.y) }.min() ?? 0
                    let maxY = face.map { CGFloat($0.y) }.max() ?? 0
                    
                    let rect = CGRect(
                        x: minX * geometry.size.width,
                        y: minY * geometry.size.height,
                        width: (maxX - minX) * geometry.size.width,
                        height: (maxY - minY) * geometry.size.height
                    )
                    let expanded = rect.insetBy(dx: -30, dy: -30)
                    
                    Rectangle()
                        .fill(.ultraThinMaterial)
                        .frame(width: expanded.width, height: expanded.height)
                        .position(x: expanded.midX, y: expanded.midY)
                        .cornerRadius(expanded.width / 2)
                }
                
                // Draw Face & Pose Core Features
                drawFeatures(in: geometry.size)
                
                // Calibration overlay
                if state.calibrating {
                    VStack {
                        Spacer()
                        Text("Calibrating... Please look straight and sit properly.")
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.black.opacity(0.7))
                            .cornerRadius(10)
                        
                        ProgressView(value: state.calibrationProgress, total: 100.0)
                            .progressViewStyle(LinearProgressViewStyle(tint: .green))
                            .padding(.horizontal, 50)
                            .padding(.bottom, 50)
                    }
                }
            }
        }
    }
    
    @ViewBuilder
    func drawFeatures(in size: CGSize) -> some View {
        ZStack {
            // Draw Custom Points
            ForEach(Array(computeCustomPoints()), id: \.self) { ptId in
                if let pt = getPt(ptId) {
                    circle(at: pt, size: size, color: .yellow)
                }
            }
            
            // Draw Custom Point Pairs and Capsules
            ForEach(computeGeometricDrawInfo()) { info in
                if info.isCapsule {
                    // Two Independent Spheres (Out of Bounds Zone)
                    if let b1 = getBaselinePt(info.pt1Id), let b2 = getBaselinePt(info.pt2Id) {
                        let cx1 = CGFloat(b1.x) * size.width
                        let cy1 = CGFloat(b1.y) * size.height
                        let cx2 = CGFloat(b2.x) * size.width
                        let cy2 = CGFloat(b2.y) * size.height
                        
                        // Match the exact math of RuleEngine (Screen Space Euclidean distance)
                        let d_base_screen = hypot(cx2 - cx1, cy2 - cy1)
                        
                        let r_screen = info.isPercentage ? CGFloat(info.value / 100.0) * d_base_screen : CGFloat(info.value)
                        
                        let color = info.triggered ? Color.red : Color.green
                        
                        Path { path in
                            path.addEllipse(in: CGRect(x: cx1 - r_screen, y: cy1 - r_screen, width: r_screen * 2, height: r_screen * 2))
                            path.addEllipse(in: CGRect(x: cx2 - r_screen, y: cy2 - r_screen, width: r_screen * 2, height: r_screen * 2))
                        }
                        .stroke(color, lineWidth: 2)
                    }
                } else {
                    // Connecting Lines
                    if let c1 = getPt(info.pt1Id), let c2 = getPt(info.pt2Id) {
                        let cx1 = CGFloat(c1.x) * size.width
                        let cy1 = CGFloat(c1.y) * size.height
                        let cx2 = CGFloat(c2.x) * size.width
                        let cy2 = CGFloat(c2.y) * size.height
                        
                        let color = info.triggered ? Color.red : Color.green
                        
                        Path { path in
                            if info.op.hasPrefix("x") {
                                // x 軸水平距離：畫一條水平線，兩點的 y 座標取平均
                                let midY = (cy1 + cy2) / 2
                                path.move(to: CGPoint(x: cx1, y: midY))
                                path.addLine(to: CGPoint(x: cx2, y: midY))
                            } else if info.op.hasPrefix("y") {
                                // y 軸垂直距離：畫一條垂直線，兩點的 x 座標取平均
                                let midX = (cx1 + cx2) / 2
                                path.move(to: CGPoint(x: midX, y: cy1))
                                path.addLine(to: CGPoint(x: midX, y: cy2))
                            } else {
                                path.move(to: CGPoint(x: cx1, y: cy1))
                                path.addLine(to: CGPoint(x: cx2, y: cy2))
                            }
                        }
                        .stroke(color, lineWidth: 3)
                    }
                }
            }
        }
    }
    
    struct GeometricDrawInfo: Identifiable {
        let id = UUID()
        let pt1Id: String
        let pt2Id: String
        let isCapsule: Bool
        let op: String
        let value: Double
        let isPercentage: Bool
        let triggered: Bool
    }
    
    private func computeGeometricDrawInfo() -> [GeometricDrawInfo] {
        var result = [GeometricDrawInfo]()
        let geometricTriggers = state.triggers.filter { $0.enabled && $0.isGeometric }
        
        for trigger in geometricTriggers {
            guard let cond = trigger.geometricRule else { continue }
            let triggered = state.activeTriggers[trigger.id] == true
            
            result.append(GeometricDrawInfo(
                pt1Id: cond.pt1,
                pt2Id: cond.pt2,
                isCapsule: cond.op == "~~",
                op: cond.op,
                value: cond.value,
                isPercentage: cond.isPercentage,
                triggered: triggered
            ))
        }
        return result
    }
    
    private func getPt(_ id: String) -> NormalizedLandmark? {
        if id.hasPrefix("p"), let pose = state.currentPoseLandmarks {
            let idxStr = id.replacingOccurrences(of: "p", with: "")
            if let idx = Int(idxStr), idx < pose.count { return pose[idx] }
        } else if id.hasPrefix("f"), let face = state.currentFaceLandmarks {
            let idxStr = id.replacingOccurrences(of: "f", with: "")
            if let idx = Int(idxStr), idx < face.count { return face[idx] }
        } else if let idx = Int(id) {
            if idx <= 32, let pose = state.currentPoseLandmarks, idx < pose.count { return pose[idx] }
        }
        return nil
    }
    
    private func getBaselinePt(_ id: String) -> NormalizedLandmark? {
        if id.hasPrefix("p"), let pose = state.baselinePoseLandmarks {
            let idxStr = id.replacingOccurrences(of: "p", with: "")
            if let idx = Int(idxStr), idx < pose.count { return pose[idx] }
        } else if id.hasPrefix("f"), let face = state.baselineFaceLandmarks {
            let idxStr = id.replacingOccurrences(of: "f", with: "")
            if let idx = Int(idxStr), idx < face.count { return face[idx] }
        } else if let idx = Int(id) {
            if idx <= 32, let pose = state.baselinePoseLandmarks, idx < pose.count { return pose[idx] }
        }
        return nil
    }
    
    private func computeCustomPoints() -> Set<String> {
        var customPoints = Set<String>()
        for trigger in state.triggers where trigger.enabled && trigger.isGeometric {
            let pts = RuleEngine.shared.getUsedPoints(from: trigger)
            customPoints.formUnion(pts)
        }
        return customPoints
    }
    
    @ViewBuilder
    private func circle(at landmark: NormalizedLandmark, size: CGSize, color: Color) -> some View {
        let x = CGFloat(landmark.x) * size.width
        let y = CGFloat(landmark.y) * size.height
        
        Circle()
            .fill(color)
            .frame(width: 10, height: 10)
            .position(x: x, y: y)
            .overlay(
                Circle()
                    .stroke(Color.white, lineWidth: 1.5)
                    .frame(width: 14, height: 14)
                    .position(x: x, y: y)
            )
    }
}
