import SwiftUI

struct TriggersView: View {
    enum ActiveSheet: Identifiable {
        case create(TriggerConfig?)
        case importExportSkill
        case importExportEvent
        
        var id: String {
            switch self {
            case .create(let config): return "create_\(config?.id ?? "new")"
            case .importExportSkill: return "importExportSkill"
            case .importExportEvent: return "importExportEvent"
            }
        }
    }
    
    @ObservedObject var state: SharedState
    @State private var activeSheet: ActiveSheet? = nil
    
    private func t(_ key: String) -> String { I18nManager.shared.t(key, lang: state.language) }
    
    var body: some View {
        NavigationView {
            ZStack {
                if state.triggers.isEmpty {
                    VStack {
                        Image(systemName: "bolt.horizontal.circle")
                            .font(.system(size: 60))
                            .foregroundColor(.gray)
                        Text(t("no_triggers_found"))
                            .foregroundColor(.gray)
                    }
                } else {
                    List {
                        Section(header: HStack {
                            Text("Skills").font(.headline)
                            Spacer()
                            Button(action: { activeSheet = .importExportSkill }) {
                                Image(systemName: "square.and.arrow.up.on.square").foregroundColor(.blue)
                            }
                        }) {
                            ForEach(state.triggers.filter { $0.type == .geometric }) { trigger in
                                TriggerRowView(
                                    state: state,
                                    trigger: Binding(
                                        get: { state.triggers.first(where: { $0.id == trigger.id }) ?? trigger },
                                        set: { newValue in
                                            if let idx = state.triggers.firstIndex(where: { $0.id == trigger.id }) {
                                                state.triggers[idx] = newValue
                                            }
                                        }
                                    ),
                                    isActive: state.activeTriggers[trigger.id] ?? false
                                )
                                .contextMenu {
                                    Button {
                                        activeSheet = .create(state.triggers.first(where: { $0.id == trigger.id }))
                                    } label: {
                                        Label(t("edit"), systemImage: "pencil")
                                    }
                                    Button(role: .destructive) {
                                        state.triggers.removeAll(where: { $0.id == trigger.id })
                                    } label: {
                                        Label(t("delete"), systemImage: "trash")
                                    }
                                }
                            }
                            .onDelete { offsets in deleteTrigger(at: offsets, type: .geometric) }
                        }
                        
                        Section(header: HStack {
                            Text("Events").font(.headline)
                            Spacer()
                            Button(action: { activeSheet = .importExportEvent }) {
                                Image(systemName: "square.and.arrow.up.on.square").foregroundColor(.blue)
                            }
                        }) {
                            ForEach(state.triggers.filter { $0.type == .logic }) { trigger in
                                TriggerRowView(
                                    state: state,
                                    trigger: Binding(
                                        get: { state.triggers.first(where: { $0.id == trigger.id }) ?? trigger },
                                        set: { newValue in
                                            if let idx = state.triggers.firstIndex(where: { $0.id == trigger.id }) {
                                                state.triggers[idx] = newValue
                                            }
                                        }
                                    ),
                                    isActive: state.activeTriggers[trigger.id] ?? false
                                )
                                .contextMenu {
                                    Button {
                                        activeSheet = .create(state.triggers.first(where: { $0.id == trigger.id }))
                                    } label: {
                                        Label(t("edit"), systemImage: "pencil")
                                    }
                                    Button(role: .destructive) {
                                        state.triggers.removeAll(where: { $0.id == trigger.id })
                                    } label: {
                                        Label(t("delete"), systemImage: "trash")
                                    }
                                }
                            }
                            .onDelete { offsets in deleteTrigger(at: offsets, type: .logic) }
                        }
                    }
                    .listStyle(InsetGroupedListStyle())
                }
            }
            .navigationTitle("Triggers")
            .navigationBarItems(
                trailing: Button(action: {
                    activeSheet = .create(nil)
                }) {
                    Image(systemName: "plus")
                }
            )
            .sheet(item: $activeSheet) { sheet in
                switch sheet {
                case .create(let trigger):
                    CreateTriggerView(state: state, isPresented: Binding(
                        get: {
                            if case .create = activeSheet { return true }
                            return false
                        },
                        set: { if !$0 { activeSheet = nil } }
                    ), editingTrigger: trigger)
                case .importExportSkill:
                    SingleEntityImportExportView(state: state, isPresented: Binding(
                        get: {
                            if case .importExportSkill = activeSheet { return true }
                            return false
                        },
                        set: { if !$0 { activeSheet = nil } }
                    ), type: .skill)
                case .importExportEvent:
                    SingleEntityImportExportView(state: state, isPresented: Binding(
                        get: {
                            if case .importExportEvent = activeSheet { return true }
                            return false
                        },
                        set: { if !$0 { activeSheet = nil } }
                    ), type: .event)
                }
            }
        }
        .navigationViewStyle(.stack)
    }
    
    private func deleteTrigger(at offsets: IndexSet, type: TriggerType) {
        let filtered = state.triggers.filter { $0.type == type }
        let idsToDelete = offsets.map { filtered[$0].id }
        state.triggers.removeAll { idsToDelete.contains($0.id) }
    }
}

struct TriggerRowView: View {
    @ObservedObject var state: SharedState
    @Binding var trigger: TriggerConfig
    var isActive: Bool
    
    private func t(_ key: String) -> String { I18nManager.shared.t(key, lang: state.language) }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(trigger.id)
                    .font(.headline)
                    .foregroundColor(trigger.enabled ? .white : .gray)
                Spacer()
                Toggle("", isOn: $trigger.enabled).labelsHidden()
            }
            
            if trigger.enabled {
                Text(trigger.description)
                    .font(.subheadline)
                    .foregroundColor(.gray)
                
                HStack {
                    Text(trigger.type == .geometric ? "Skill" : "Event")
                        .font(.caption)
                        .padding(4)
                        .background(trigger.type == .geometric ? Color.purple.opacity(0.3) : Color.orange.opacity(0.3))
                        .cornerRadius(4)
                    
                    if trigger.type == .geometric, let rule = trigger.geometricRule {
                        let opText: String = {
                            switch rule.op {
                            case "><": return t("rule_shorter")
                            case "<>": return t("rule_longer")
                            case ">><<": return t("rule_change")
                            case "~~": return t("rule_capsule")
                            default: return rule.op
                            }
                        }()
                        Text("\(rule.pt1) \(t("rule_to")) \(rule.pt2) \(opText) \(String(format: "%.1f", rule.value))\(rule.isPercentage ? "%" : "px")")
                            .font(.caption)
                            .foregroundColor(.blue)
                            .lineLimit(1)
                    } else if trigger.type == .logic, let rule = trigger.logicRule {
                        let desc = rule.conditions.map { "\($0.isNot ? "\(t("rule_not")) " : "")\($0.triggerId)" }.joined(separator: " \(rule.joinOperator) ")
                        Text(desc)
                            .font(.caption)
                            .foregroundColor(.blue)
                            .lineLimit(1)
                    }
                }
                
                HStack {
                    Text(isActive ? "TRIGGERED" : "MONITORING")
                        .font(.caption)
                        .fontWeight(.bold)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(isActive ? Color.red.opacity(0.2) : Color.green.opacity(0.2))
                        .foregroundColor(isActive ? .red : .green)
                        .cornerRadius(6)
                }
            }
        }
        .padding(.vertical, 4)
        .listRowBackground(Color(white: 0.15))
    }
}

struct CreateTriggerView: View {
    @ObservedObject var state: SharedState
    @Binding var isPresented: Bool
    var editingTrigger: TriggerConfig?
    
    @State private var id = ""
    @State private var description = ""
    
    @State private var triggerType: TriggerType = .geometric
    
    @State private var pt1: String = ""
    @State private var pt2: String = ""
    @State private var op: String = "><"
    @State private var value: String = ""
    @State private var unit: String = "%"
    
    var ops: [(String, String)] {
        [
            ("><", t("rule_shorter")),
            ("<>", t("rule_longer")),
            (">><<", t("rule_change")),
            ("~~", t("rule_capsule"))
        ]
    }
    let units = ["%", "px"]
    
    @State private var logicConditions: [LogicCondition] = [LogicCondition()]
    @State private var logicOp: String = "AND"
    let logicOps = ["AND", "OR"]
    
    private func t(_ key: String) -> String { I18nManager.shared.t(key, lang: state.language) }
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text(t("basic_info"))) {
                    Picker("Type", selection: $triggerType) {
                        Text("Skill").tag(TriggerType.geometric)
                        Text("Event").tag(TriggerType.logic)
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    
                    TextField(t("event_id"), text: $id)
                    TextField(t("description"), text: $description)
                }
                
                if triggerType == .geometric {
                    Section(header: Text(t("geometric_rule"))) {
                        HStack(alignment: .top) {
                            TextField(t("point_1"), text: $pt1).autocapitalization(.none)
                            TextField(t("point_2"), text: $pt2).autocapitalization(.none)
                        }
                        
                        Picker(t("operator"), selection: $op) {
                            ForEach(ops, id: \.0) { o in
                                Text(o.1).tag(o.0)
                            }
                        }
                        
                        HStack {
                            TextField(t("value"), text: $value).keyboardType(.decimalPad)
                            Picker(t("unit"), selection: $unit) {
                                ForEach(units, id: \.self) { Text($0) }
                            }
                            .pickerStyle(SegmentedPickerStyle())
                            .frame(width: 100)
                        }
                    }
                } else {
                    Section(header: Text(t("logic_conditions"))) {
                        Picker(t("join_with"), selection: $logicOp) {
                            Text(t("rule_and")).tag("AND")
                            Text(t("rule_or")).tag("OR")
                        }
                        .pickerStyle(SegmentedPickerStyle())
                        
                        ForEach(logicConditions.indices, id: \.self) { i in
                            HStack {
                                Picker("", selection: $logicConditions[i].isNot) {
                                    Text(t("rule_is")).tag(false)
                                    Text(t("rule_is_not")).tag(true)
                                }
                                .pickerStyle(MenuPickerStyle())
                                .frame(width: 120)
                                
                                Picker("", selection: $logicConditions[i].triggerId) {
                                    Text(t("select_trigger")).tag("")
                                    ForEach(state.triggers) { trigger in
                                        if trigger.id != id {
                                            Text(trigger.id).tag(trigger.id)
                                        }
                                    }
                                }
                                .pickerStyle(MenuPickerStyle())
                                
                                Spacer()
                                
                                if logicConditions.count > 1 {
                                    Button(action: {
                                        logicConditions.remove(at: i)
                                    }) {
                                        Image(systemName: "minus.circle.fill").foregroundColor(.red)
                                    }
                                }
                            }
                            .padding(.vertical, 4)
                        }
                        
                        Button(action: {
                            logicConditions.append(LogicCondition())
                        }) {
                            HStack {
                                Image(systemName: "plus.circle.fill")
                                Text(t("add_condition"))
                            }
                        }
                    }
                }
                
                Button(action: {
                    var newTrigger = TriggerConfig(id: id, description: description, enabled: editingTrigger?.enabled ?? true, type: triggerType)
                    if triggerType == .geometric {
                        newTrigger.geometricRule = GeometricRule(pt1: pt1, pt2: pt2, op: op, value: Double(value) ?? 0, isPercentage: unit == "%")
                    } else {
                        newTrigger.logicRule = LogicRule(conditions: logicConditions.filter { !$0.triggerId.isEmpty }, joinOperator: logicOp)
                    }
                    if let editingTrigger = editingTrigger, let idx = state.triggers.firstIndex(where: { $0.id == editingTrigger.id }) {
                        state.triggers[idx] = newTrigger
                    } else {
                        state.triggers.append(newTrigger)
                    }
                    isPresented = false
                }) {
                    HStack {
                        Spacer()
                        Text(t("deploy_rule"))
                            .bold()
                        Spacer()
                    }
                }
                .disabled(id.isEmpty || (triggerType == .geometric ? (pt1.isEmpty || pt2.isEmpty || value.isEmpty) : logicConditions.filter { !$0.triggerId.isEmpty }.isEmpty))
            }
            .navigationTitle(editingTrigger == nil ? t("create_rule") : t("edit"))
            .navigationBarItems(leading: Button(t("cancel")) {
                isPresented = false
            })
            .onAppear {
                if let editingTrigger = editingTrigger {
                    id = editingTrigger.id
                    description = editingTrigger.description
                    triggerType = editingTrigger.type
                    if let gr = editingTrigger.geometricRule {
                        pt1 = gr.pt1
                        pt2 = gr.pt2
                        op = gr.op
                        value = String(gr.value)
                        unit = gr.isPercentage ? "%" : "px"
                    } else if let lr = editingTrigger.logicRule {
                        logicOp = lr.joinOperator
                        logicConditions = lr.conditions
                    }
                }
            }
        }
        .navigationViewStyle(.stack)
        .preferredColorScheme(.dark)
    }
}

