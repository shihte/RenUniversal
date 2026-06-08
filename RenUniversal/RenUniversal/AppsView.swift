import SwiftUI

struct AppsView: View {
    @ObservedObject var state: SharedState
    
    let availableApps: [(String, String, String, String)] = []
    
    @State private var selectedGameUrl: String? = nil
    
    var body: some View {
        NavigationView {
            ZStack {
                Color(white: 0.1).edgesIgnoringSafeArea(.all)
                
                ScrollView {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 20) {
                        ForEach(availableApps, id: \.0) { app in
                            Button(action: {
                                selectedGameUrl = app.3
                            }) {
                                VStack {
                                    Image(systemName: "gamecontroller.fill")
                                        .font(.system(size: 40))
                                        .foregroundColor(.blue)
                                        .padding()
                                    
                                    Text(app.1)
                                        .font(.headline)
                                        .foregroundColor(.white)
                                    
                                    Text(app.2)
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
                    .padding()
                }
            }
            .navigationTitle(t("apps_launcher"))
            .sheet(item: Binding<String?>(
                get: { selectedGameUrl },
                set: { selectedGameUrl = $0 }
            )) { url in
                // Present GameWebView for the URL
                GameWebView(state: state, htmlFileName: url)
            }
        }
    }
    
    private func t(_ key: String) -> String {
        return I18nManager.shared.t(key, lang: state.language)
    }
}

extension String: Identifiable {
    public var id: String { self }
}
