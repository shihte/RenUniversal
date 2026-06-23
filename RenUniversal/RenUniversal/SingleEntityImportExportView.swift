import SwiftUI

struct SingleEntityImportExportView: View {
    @ObservedObject var state: SharedState
    @Binding var isPresented: Bool
    
    enum EntityType {
        case skill
        case event
        case app
    }
    
    let type: EntityType
    
    @State private var text: String = ""
    @State private var isShowingImport: Bool = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                TextEditor(text: $text)
                    .font(.system(.caption, design: .monospaced))
                    .padding()
                    .background(Color(white: 0.15))
                    .cornerRadius(8)
                    .padding()
                
                HStack(spacing: 20) {
                    if !isShowingImport {
                        Button(action: { UIPasteboard.general.string = text }) {
                            Text("Copy Exported JSON")
                                .bold()
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(12)
                        }
                    } else {
                        Button(action: processImport) {
                            Text("Import & Merge")
                                .bold()
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.red)
                                .foregroundColor(.white)
                                .cornerRadius(12)
                        }
                    }
                }
                .padding(.horizontal)
                .padding(.bottom)
            }
            .navigationTitle(title)
            .navigationBarItems(
                leading: Button(isShowingImport ? "Back to Export" : "Import Mode") {
                    isShowingImport.toggle()
                    if isShowingImport {
                        text = ""
                    } else {
                        generateExport()
                    }
                },
                trailing: Button("Done") { isPresented = false }
            )
        }
        .navigationViewStyle(.stack)
        .preferredColorScheme(.dark)
        .onAppear {
            generateExport()
        }
    }
    
    private var title: String {
        switch type {
        case .skill: return isShowingImport ? "Import Skills" : "Export Skills"
        case .event: return isShowingImport ? "Import Events" : "Export Events"
        case .app: return isShowingImport ? "Import Apps" : "Export Apps"
        }
    }
    
    private func generateExport() {
        switch type {
        case .skill:
            let skills = state.triggers.filter { $0.type == .geometric }.compactMap { $0.toWebSkill() }
            if let data = try? JSONEncoder().encode(skills) {
                text = String(data: data, encoding: .utf8) ?? ""
            }
        case .event:
            let events = state.triggers.filter { $0.type == .logic }.compactMap { $0.toWebEvent() }
            if let data = try? JSONEncoder().encode(events) {
                text = String(data: data, encoding: .utf8) ?? ""
            }
        case .app:
            if let data = try? JSONEncoder().encode(state.apps) {
                text = String(data: data, encoding: .utf8) ?? ""
            }
        }
    }
    
    private func processImport() {
        guard let data = text.data(using: .utf8) else { return }
        switch type {
        case .skill:
            if let newSkills = try? JSONDecoder().decode([WebSkillFormat].self, from: data) {
                let triggers = newSkills.map { TriggerConfig.fromWebSkill($0) }
                for t in triggers {
                    if let idx = state.triggers.firstIndex(where: { $0.id == t.id }) { state.triggers[idx] = t }
                    else { state.triggers.append(t) }
                }
                isPresented = false
            }
        case .event:
            if let newEvents = try? JSONDecoder().decode([WebEventFormat].self, from: data) {
                let triggers = newEvents.map { TriggerConfig.fromWebEvent($0) }
                for t in triggers {
                    if let idx = state.triggers.firstIndex(where: { $0.id == t.id }) { state.triggers[idx] = t }
                    else { state.triggers.append(t) }
                }
                isPresented = false
            }
        case .app:
            if let newApps = try? JSONDecoder().decode([AppConfig].self, from: data) {
                for app in newApps {
                    if let idx = state.apps.firstIndex(where: { $0.id == app.id }) { state.apps[idx] = app }
                    else { state.apps.append(app) }
                }
                isPresented = false
            }
        }
    }
}
