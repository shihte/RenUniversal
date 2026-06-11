import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject private var sharedState = SharedState()
    @State private var isHUDExpanded: Bool = true
    
    private var captureSession: AVCaptureSession? {
        return sharedState.pipelineManager?.captureSession
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Top Navigation Bar
            HStack {
                Text(t("monitor_dashboard"))
                    .font(.headline)
                    .foregroundColor(.white)
                Spacer()
            }
            .padding()
            .background(Color(white: 0.12))
            
            TabView {
                cameraTab
                    .tabItem { Label(t("live_monitor"), systemImage: "camera.viewfinder") }
                
                metricsTab
                    .tabItem { Label(t("metrics"), systemImage: "chart.bar.xaxis") }
                
                TriggersView(state: sharedState)
                    .tabItem {
                        Image(systemName: "bolt.horizontal")
                        Text("Triggers")
                    }
                
                AppsView(state: sharedState)
                    .tabItem { Label(t("apps_launcher"), systemImage: "gamecontroller.fill") }
            }
        }
        .onDisappear {
            sharedState.pipelineManager?.stop()
        }
        .preferredColorScheme(.dark)
    }
    
    // Helper to translate strings
    private func t(_ key: String) -> String {
        return I18nManager.shared.t(key, lang: sharedState.language)
    }
    
    // MARK: - Tab 1: Camera
    private var cameraTab: some View {
        ZStack {
            if sharedState.isCameraEnabled {
                if let session = captureSession {
                    CameraPreviewView(session: session)
                        .edgesIgnoringSafeArea(.top)
                } else {
                    Color.black.edgesIgnoringSafeArea(.top)
                    Text(t("camera_loading"))
                        .foregroundColor(.gray)
                }
                
                OverlayView(state: sharedState)
                
                VStack {
                    cameraHUD
                    Spacer()
                }
            } else {
                Color(white: 0.1).edgesIgnoringSafeArea(.top)
                VStack {
                    Image(systemName: "camera.slash")
                        .font(.system(size: 60))
                        .foregroundColor(.gray)
                    Text("Camera Disabled")
                        .foregroundColor(.gray)
                        .padding()
                }
            }
            
        }
        .background(Color.black)
        .safeAreaInset(edge: .bottom) {
            HStack(spacing: 20) {
                if sharedState.isCameraEnabled {
                    Button(action: {
                        sharedState.pipelineManager?.startCalibration()
                    }) {
                        HStack {
                            Image(systemName: "viewfinder")
                            Text(t("recalibrate_workspace"))
                        }
                        .font(.headline)
                        .foregroundColor(sharedState.calibrating ? .gray : .black)
                        .padding()
                        .background(sharedState.calibrating ? Color.white.opacity(0.5) : Color.white)
                        .cornerRadius(30)
                        .shadow(radius: 10)
                    }
                    .disabled(sharedState.calibrating)
                }
                
                Toggle("", isOn: Binding(
                    get: { sharedState.isCameraEnabled },
                    set: { newValue in
                        sharedState.isCameraEnabled = newValue
                        if newValue {
                            sharedState.setupPipeline()
                            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                                sharedState.pipelineManager?.startCalibration()
                            }
                        } else {
                            sharedState.pipelineManager?.stop()
                        }
                    }
                ))
                .labelsHidden()
                .toggleStyle(SwitchToggleStyle(tint: .blue))
                .scaleEffect(1.2)
                .padding()
                .background(Color.black.opacity(0.6))
                .cornerRadius(30)
            }
            .padding(.bottom, 20)
            .padding(.trailing, 20)
            .frame(maxWidth: .infinity, alignment: .bottomTrailing)
        }
    }
    
    // MARK: - Camera HUD
    private var cameraHUD: some View {
        VStack(alignment: .leading, spacing: 8) {
            Button(action: { withAnimation { isHUDExpanded.toggle() } }) {
                HStack {
                    Text("Live Status")
                        .font(.subheadline).bold()
                        .foregroundColor(.white)
                    Spacer()
                    Image(systemName: isHUDExpanded ? "chevron.up" : "chevron.down")
                        .foregroundColor(.white)
                }
            }
            
            if isHUDExpanded {
                Divider().background(Color.gray)
                ScrollView {
                    VStack(alignment: .leading, spacing: 10) {
                        ForEach(sharedState.triggers, id: \.id) { trigger in
                            if trigger.enabled {
                                HStack {
                                    Image(systemName: sharedState.activeTriggers[trigger.id] == true ? "circle.fill" : "circle")
                                        .foregroundColor(sharedState.activeTriggers[trigger.id] == true ? .red : .green)
                                    
                                    VStack(alignment: .leading) {
                                        Text(trigger.id)
                                            .font(.caption).bold()
                                            .foregroundColor(.white)
                                        if let ratio = sharedState.activeRatios[trigger.id] {
                                            Text(String(format: "%.1f%%", ratio))
                                                .font(.caption2)
                                                .foregroundColor(.gray)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                .frame(maxHeight: 150)
            }
        }
        .padding()
        .background(Color.black.opacity(0.6))
        .cornerRadius(12)
        .padding()
        .padding(.horizontal, 20)
    }
    
    @State private var showingProfileManager = false

    // MARK: - Tab 2: Metrics
    private var metricsTab: some View {
        NavigationView {
            ZStack {
                Color(white: 0.1).edgesIgnoringSafeArea(.all)
                
                VStack(spacing: 20) {
                    HStack {
                        Text(t("system_status"))
                            .font(.headline)
                        Spacer()
                        Circle()
                            .fill(sharedState.isCalibrated ? Color.green : Color.red)
                            .frame(width: 12, height: 12)
                    }
                    .padding()
                    .background(Color(white: 0.15))
                    .cornerRadius(10)
                    .padding(.horizontal)
                    
                    ScrollView {
                        VStack(spacing: 16) {
                            // Face Blur Toggle
                            HStack {
                                Image(systemName: "eye.slash")
                                    .font(.title2)
                                    .foregroundColor(.gray)
                                    .frame(width: 40)
                                Toggle(t("face_blur"), isOn: $sharedState.isFaceBlurEnabled)
                                    .font(.subheadline)
                                    .foregroundColor(.white)
                            }
                            .padding()
                            .background(Color(white: 0.15))
                            .cornerRadius(12)
                            
                            // Language Toggle
                            HStack {
                                Image(systemName: "globe")
                                    .font(.title2)
                                    .foregroundColor(.gray)
                                    .frame(width: 40)
                                HStack {
                                    Text("Language / 語言")
                                        .font(.subheadline)
                                        .foregroundColor(.white)
                                    Spacer()
                                    Picker("", selection: $sharedState.language) {
                                        Text("English").tag("en")
                                        Text("繁體中文").tag("zh-TW")
                                        Text("日本語").tag("ja")
                                        Text("한국어").tag("ko")
                                        Text("Español").tag("es")
                                        Text("Français").tag("fr")
                                    }
                                    .pickerStyle(MenuPickerStyle())
                                    .tint(.blue)
                                }.foregroundColor(.blue)
                            }
                            .padding()
                            .background(Color(white: 0.15))
                            .cornerRadius(12)
                            
                            // Point Reference Guide Link
                            NavigationLink(destination: PointReferenceView(state: sharedState)) {
                                HStack {
                                    Image(systemName: "map")
                                        .font(.title2)
                                        .foregroundColor(.gray)
                                        .frame(width: 40)
                                    Text(t("point_reference"))
                                        .font(.subheadline)
                                        .foregroundColor(.white)
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .foregroundColor(.gray)
                                }
                                .padding()
                                .background(Color(white: 0.15))
                                .cornerRadius(12)
                            }
                            
                            // Profile Import/Export Button
                            Button(action: {
                                showingProfileManager = true
                            }) {
                                HStack {
                                    Image(systemName: "square.and.arrow.up.on.square")
                                        .font(.title2)
                                        .foregroundColor(.gray)
                                        .frame(width: 40)
                                    Text("Profile Import/Export")
                                        .font(.subheadline)
                                        .foregroundColor(.white)
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .foregroundColor(.gray)
                                }
                                .padding()
                                .background(Color(white: 0.15))
                                .cornerRadius(12)
                            }
                            .sheet(isPresented: $showingProfileManager) {
                                ProfileImportExportView(state: sharedState, isPresented: $showingProfileManager)
                            }
                        }
                        .padding(.horizontal)
                    }
                    Spacer()
                }
                .padding(.top)
            }
            .navigationTitle(t("metrics"))
        }
    }
    
    private func metricCard(title: String, value: String, valueColor: Color = .white, icon: String) -> some View {
        HStack {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.gray)
                .frame(width: 40)
            
            Text(title.uppercased())
                .font(.subheadline)
                .foregroundColor(.gray)
            
            Spacer()
            
            Text(value)
                .font(.title3)
                .fontWeight(.bold)
                .foregroundColor(valueColor)
        }
        .padding()
        .background(Color(white: 0.15))
        .cornerRadius(12)
    }
    
    // Removed skillsTab as it's replaced by TriggersView
}

#Preview {
    ContentView()
}
