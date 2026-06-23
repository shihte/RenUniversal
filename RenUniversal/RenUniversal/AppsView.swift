import SwiftUI

struct AppsView: View {
    @ObservedObject var state: SharedState
    
    @State private var selectedGameUrl: String? = nil
    @State private var showingImportExport: Bool = false
    
    var body: some View {
        NavigationView {
            ZStack {
                Color(white: 0.1).edgesIgnoringSafeArea(.all)
                
                if state.apps.isEmpty {
                    VStack {
                        Image(systemName: "app.badge")
                            .font(.system(size: 60))
                            .foregroundColor(.gray)
                        Text("No Apps Installed")
                            .foregroundColor(.gray)
                    }
                } else {
                    ScrollView {
                        LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 20) {
                            ForEach(state.apps) { app in
                                if app.enabled {
                                    Button(action: {
                                        selectedGameUrl = app.url
                                    }) {
                                        VStack {
                                            Image(systemName: "gamecontroller.fill")
                                                .font(.system(size: 40))
                                                .foregroundColor(.blue)
                                                .padding()
                                            
                                            Text(app.name)
                                                .font(.headline)
                                                .foregroundColor(.white)
                                            
                                            Text(app.description)
                                                .font(.caption2)
                                                .foregroundColor(.gray)
                                                .multilineTextAlignment(.center)
                                                .padding(.horizontal)
                                        }
                                        .frame(height: 180)
                                        .frame(maxWidth: .infinity)
                                        .background(Color(white: 0.15))
                                        .cornerRadius(16)
                                    }
                                }
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle(t("apps_launcher"))
            .navigationBarItems(trailing: Button(action: {
                showingImportExport = true
            }) {
                Image(systemName: "square.and.arrow.up.on.square")
            })
            .sheet(isPresented: $showingImportExport) {
                SingleEntityImportExportView(state: state, isPresented: $showingImportExport, type: .app)
            }
            .sheet(item: Binding<String?>(
                get: { selectedGameUrl },
                set: { selectedGameUrl = $0 }
            )) { url in
                GameWebView(state: state, htmlFileName: url)
            }
        }
        .navigationViewStyle(.stack)
    }
    
    private func t(_ key: String) -> String {
        return I18nManager.shared.t(key, lang: state.language)
    }
}

extension String: Identifiable {
    public var id: String { self }
}
