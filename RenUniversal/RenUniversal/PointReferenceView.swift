import SwiftUI

struct PointReferenceView: View {
    @ObservedObject var state: SharedState
    
    private func t(_ key: String) -> String { I18nManager.shared.t(key, lang: state.language) }
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text(t("point_reference"))
                    .font(.title2)
                    .bold()
                    .padding(.top)
                
                NavigationLink(destination: InteractiveTopologyView(title: t("face_mesh"), isFace: true, vertices: TopologyData.faceVertices, edges: TopologyData.faceEdges)) {
                    HStack {
                        Image(systemName: "face.dashed")
                            .font(.title)
                        Text(t("face_mesh"))
                            .font(.headline)
                        Spacer()
                        Image(systemName: "chevron.right")
                    }
                    .padding()
                    .background(Color(white: 0.15))
                    .cornerRadius(12)
                    .foregroundColor(.white)
                }
                
                NavigationLink(destination: InteractiveTopologyView(title: t("pose_mesh"), isFace: false, vertices: TopologyData.poseVertices, edges: TopologyData.poseEdges)) {
                    HStack {
                        Image(systemName: "figure.walk")
                            .font(.title)
                        Text(t("pose_mesh"))
                            .font(.headline)
                        Spacer()
                        Image(systemName: "chevron.right")
                    }
                    .padding()
                    .background(Color(white: 0.15))
                    .cornerRadius(12)
                    .foregroundColor(.white)
                }
            }
            .padding()
        }
        .navigationTitle(t("point_reference"))
    }
}

struct InteractiveTopologyView: View {
    let title: String
    let isFace: Bool
    let vertices: [CGPoint]
    let edges: [(Int, Int)]
    
    @State private var selectedPoint: Int? = nil
    
    var body: some View {
        GeometryReader { geo in
            let bounds = computeBounds(w: geo.size.width, h: geo.size.height)
            
            ZStack {
                Color(white: 0.1).edgesIgnoringSafeArea(.all)
                
                ZoomableScrollView(onTapped: { tapLoc in
                    var minDist: CGFloat = .infinity
                    var closestIdx: Int? = nil
                    
                    for i in 0..<vertices.count {
                        let pt = project(vertices[i], bounds: bounds)
                        let dist = hypot(pt.x - tapLoc.x, pt.y - tapLoc.y)
                        if dist < minDist {
                            minDist = dist
                            closestIdx = i
                        }
                    }
                    
                    // Always select the closest point if within a reasonable local distance
                    if minDist < 40 {
                        selectedPoint = closestIdx
                    } else {
                        selectedPoint = nil
                    }
                }) {
                    ZStack {
                        // Draw Edges
                        Path { path in
                            for edge in edges {
                                if edge.0 < vertices.count && edge.1 < vertices.count {
                                    let p1 = project(vertices[edge.0], bounds: bounds)
                                    let p2 = project(vertices[edge.1], bounds: bounds)
                                    path.move(to: p1)
                                    path.addLine(to: p2)
                                }
                            }
                        }
                        .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                        
                        // Draw Vertices
                        ForEach(0..<vertices.count, id: \.self) { i in
                            let pt = project(vertices[i], bounds: bounds)
                            Circle()
                                .fill(selectedPoint == i ? Color.red : Color.blue)
                                .frame(width: 3, height: 3)
                                .position(pt)
                        }
                    }
                    .frame(width: geo.size.width, height: geo.size.height)
                }
            }
        }
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
        .overlay(
            VStack {
                Spacer()
                if let idx = selectedPoint {
                    Text("\(isFace ? "f" : "p")\(idx)")
                        .font(.title)
                        .bold()
                        .padding()
                        .background(Color.black.opacity(0.7))
                        .cornerRadius(10)
                        .foregroundColor(.white)
                        .padding(.bottom, 40)
                } else {
                    Text("Tap a node to view ID, Pinch to Zoom")
                        .font(.caption)
                        .padding()
                        .background(Color.black.opacity(0.5))
                        .cornerRadius(10)
                        .foregroundColor(.white)
                        .padding(.bottom, 40)
                }
            }
        )
    }
    
    private func computeBounds(w: CGFloat, h: CGFloat) -> (minX: CGFloat, maxX: CGFloat, minY: CGFloat, maxY: CGFloat, scale: CGFloat, offsetX: CGFloat, offsetY: CGFloat) {
        if vertices.isEmpty { return (0, 1, 0, 1, 1, 0, 0) }
        let xs = vertices.map { $0.x }
        let ys = vertices.map { $0.y }
        let minX = xs.min()!
        let maxX = xs.max()!
        let minY = ys.min()!
        let maxY = ys.max()!
        
        let width = max(maxX - minX, 0.001)
        let height = max(maxY - minY, 0.001)
        
        let scaleX = (w * 0.8) / width
        let scaleY = (h * 0.8) / height
        let scale = min(scaleX, scaleY)
        
        let offsetX = (w - width * scale) / 2
        let offsetY = (h - height * scale) / 2
        
        return (minX, maxX, minY, maxY, scale, offsetX, offsetY)
    }
    
    private func project(_ pt: CGPoint, bounds: (minX: CGFloat, maxX: CGFloat, minY: CGFloat, maxY: CGFloat, scale: CGFloat, offsetX: CGFloat, offsetY: CGFloat)) -> CGPoint {
        return CGPoint(
            x: (pt.x - bounds.minX) * bounds.scale + bounds.offsetX,
            y: (pt.y - bounds.minY) * bounds.scale + bounds.offsetY
        )
    }
}

struct ZoomableScrollView<Content: View>: UIViewRepresentable {
    private var content: Content
    var onTapped: ((CGPoint) -> Void)?
    
    init(onTapped: ((CGPoint) -> Void)? = nil, @ViewBuilder content: () -> Content) {
        self.content = content()
        self.onTapped = onTapped
    }
    
    func makeUIView(context: Context) -> UIScrollView {
        let scrollView = UIScrollView()
        scrollView.delegate = context.coordinator
        scrollView.maximumZoomScale = 20.0
        scrollView.minimumZoomScale = 1.0
        scrollView.bouncesZoom = true
        scrollView.showsHorizontalScrollIndicator = false
        scrollView.showsVerticalScrollIndicator = false
        scrollView.delaysContentTouches = false
        
        let hostedView = context.coordinator.hostingController.view!
        hostedView.translatesAutoresizingMaskIntoConstraints = true
        hostedView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        hostedView.backgroundColor = .clear
        
        let tapRecognizer = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.handleTap(_:)))
        hostedView.addGestureRecognizer(tapRecognizer)
        
        scrollView.addSubview(hostedView)
        return scrollView
    }
    
    func makeCoordinator() -> Coordinator {
        return Coordinator(hostingController: UIHostingController(rootView: self.content), onTapped: self.onTapped)
    }
    
    func updateUIView(_ uiView: UIScrollView, context: Context) {
        context.coordinator.hostingController.rootView = self.content
        context.coordinator.onTapped = self.onTapped
        if context.coordinator.hostingController.view.superview == nil {
            uiView.addSubview(context.coordinator.hostingController.view)
        }
        
        let view = context.coordinator.hostingController.view!
        if uiView.bounds.size != .zero && view.bounds.size == .zero {
            view.frame = CGRect(origin: .zero, size: uiView.bounds.size)
            uiView.contentSize = uiView.bounds.size
        }
    }
    
    class Coordinator: NSObject, UIScrollViewDelegate {
        var hostingController: UIHostingController<Content>
        var onTapped: ((CGPoint) -> Void)?
        
        init(hostingController: UIHostingController<Content>, onTapped: ((CGPoint) -> Void)?) {
            self.hostingController = hostingController
            self.onTapped = onTapped
        }
        
        @objc func handleTap(_ sender: UITapGestureRecognizer) {
            let location = sender.location(in: hostingController.view)
            onTapped?(location)
        }
        
        func viewForZooming(in scrollView: UIScrollView) -> UIView? {
            return hostingController.view
        }
    }
}
