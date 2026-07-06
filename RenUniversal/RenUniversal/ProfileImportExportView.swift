import SwiftUI

struct ProfileImportExportView: View {
    @ObservedObject var state: SharedState
    @Binding var isPresented: Bool
    
    @State private var selectedSkills: Set<String> = []
    @State private var selectedEvents: Set<String> = []
    @State private var selectedApps: Set<String> = []
    
    @State private var exportJsonText: String = ""
    @State private var isShowingExportResult: Bool = false
    
    @State private var importText: String = ""
    @State private var isShowingImportMode: Bool = false
    
    var body: some View {
        NavigationView {
            if isShowingExportResult || isShowingImportMode {
                rawTextView
            } else {
                selectionView
            }
        }
        .navigationViewStyle(.stack)
        .preferredColorScheme(.dark)
        .onAppear {
            // Select all by default
            selectedSkills = Set(state.triggers.filter { $0.type == .geometric }.map { $0.id })
            selectedEvents = Set(state.triggers.filter { $0.type == .logic }.map { $0.id })
            selectedApps = Set(state.apps.map { $0.id })
        }
    }
    
    private var selectionView: some View {
        Form {
            Section(header: Text("Skills (Geometric)")) {
                let skills = state.triggers.filter { $0.type == .geometric }
                if skills.isEmpty {
                    Text("No Skills available")
                }
                ForEach(skills) { trigger in
                    Toggle(trigger.id, isOn: Binding(
                        get: { selectedSkills.contains(trigger.id) },
                        set: { isSelected in
                            if isSelected { selectedSkills.insert(trigger.id) }
                            else { selectedSkills.remove(trigger.id) }
                        }
                    ))
                }
            }
            
            Section(header: Text("Events (Logic)")) {
                let events = state.triggers.filter { $0.type == .logic }
                if events.isEmpty {
                    Text("No Events available")
                }
                ForEach(events) { trigger in
                    Toggle(trigger.id, isOn: Binding(
                        get: { selectedEvents.contains(trigger.id) },
                        set: { isSelected in
                            if isSelected { selectedEvents.insert(trigger.id) }
                            else { selectedEvents.remove(trigger.id) }
                        }
                    ))
                }
            }
            
            Section(header: Text("Applications")) {
                if state.apps.isEmpty {
                    Text("No Apps available")
                }
                ForEach(state.apps) { app in
                    Toggle(app.name, isOn: Binding(
                        get: { selectedApps.contains(app.id) },
                        set: { isSelected in
                            if isSelected { selectedApps.insert(app.id) }
                            else { selectedApps.remove(app.id) }
                        }
                    ))
                }
            }
            
            Section {
                Button(action: generateExport) {
                    HStack {
                        Spacer()
                        Text("Generate Export")
                            .bold()
                        Spacer()
                    }
                }
                .disabled(selectedSkills.isEmpty && selectedEvents.isEmpty && selectedApps.isEmpty)
                
                Button(action: { isShowingImportMode = true }) {
                    HStack {
                        Spacer()
                        Text("Import Profile")
                            .foregroundColor(.orange)
                        Spacer()
                    }
                }
            }
        }
        .navigationTitle("Profile Packages")
        .navigationBarItems(trailing: Button("Cancel") { isPresented = false })
    }
    
    private var rawTextView: some View {
        VStack(spacing: 0) {
            TextEditor(text: isShowingImportMode ? $importText : $exportJsonText)
                .font(.system(.caption, design: .monospaced))
                .padding()
                .background(Color(white: 0.15))
                .cornerRadius(8)
                .padding()
            
            HStack(spacing: 20) {
                if isShowingExportResult {
                    Button(action: {
                        UIPasteboard.general.string = exportJsonText
                    }) {
                        Text("Copy to Clipboard")
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
        .navigationTitle(isShowingImportMode ? "Import JSON" : "Export JSON")
        .navigationBarItems(
            leading: Button("Back") {
                isShowingExportResult = false
                isShowingImportMode = false
            },
            trailing: Button("Done") { isPresented = false }
        )
    }
    
    private func generateExport() {
        let skills = state.triggers.filter { selectedSkills.contains($0.id) && $0.type == .geometric }.compactMap { $0.toWebSkill() }
        let events = state.triggers.filter { selectedEvents.contains($0.id) && $0.type == .logic }.compactMap { $0.toWebEvent() }
        let apps = state.apps.filter { selectedApps.contains($0.id) }
        
        let bundle = ProfileBundle(skills: skills, events: events, apps: apps)
        if let data = try? JSONEncoder().encode(bundle),
           let str = String(data: data, encoding: .utf8) {
            exportJsonText = str
            isShowingExportResult = true
        }
    }
    
    private func processImport() {
        guard let data = importText.data(using: .utf8) else { return }
        if let bundle = try? JSONDecoder().decode(ProfileBundle.self, from: data) {
            // Merge skills and events
            let newSkills = bundle.skills.map { TriggerConfig.fromWebSkill($0) }
            let newEvents = bundle.events.map { TriggerConfig.fromWebEvent($0) }
            
            for newT in (newSkills + newEvents) {
                if let idx = state.triggers.firstIndex(where: { $0.id == newT.id }) {
                    state.triggers[idx] = newT
                } else {
                    state.triggers.append(newT)
                }
            }
            
            for app in bundle.apps {
                if let idx = state.apps.firstIndex(where: { $0.id == app.id }) {
                    state.apps[idx] = app
                } else {
                    state.apps.append(app)
                }
            }
            
            isPresented = false
        }
    }
}
