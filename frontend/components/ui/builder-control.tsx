"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Edit, Power, PowerOff, Save, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface BuilderProps {
    className?: string;
    type: "skill" | "event";
}

export function BuilderControl({ className, type }: BuilderProps) {
    const [items, setItems] = useState<any[]>([]);
    const [editItem, setEditItem] = useState<any | null>(null);
    const [syntax, setSyntax] = useState("");
    
    // For creating/editing generic IDs
    const [pt1, setPt1] = useState("");
    const [pt2, setPt2] = useState("");
    const [op, setOp] = useState("><");
    const [num, setNum] = useState("20");

    const [formName, setFormName] = useState("");
    const [formDesc, setFormDesc] = useState("");

    const fetchItems = async () => {
        try {
            const res = await fetch(`http://localhost:5001/api/${type}s`);
            if (res.ok) setItems(await res.json());
        } catch {}
    };

    useEffect(() => {
        fetchItems();
    }, [type]);

    const handleToggle = async (name: string, enabled: boolean) => {
        await fetch(`http://localhost:5001/api/${type}s/toggle`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, enabled })
        });
        fetchItems();
    };

    const handleDelete = async (name: string) => {
        if (!confirm(`確定要刪除 ${name} 嗎？`)) return;
        await fetch(`http://localhost:5001/api/${type}s/delete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        fetchItems();
    };

    const handleEdit = (item: any) => {
        setEditItem(item);
        setFormName(item.name);
        setFormDesc(item.description || "");
        
        const r0 = item.rules?.[0];
        if (typeof r0 === 'string') {
            setSyntax(r0);
        } else if (typeof r0 === 'object' && r0 !== null) {
            setSyntax(`${r0.feature || ''} ${r0.operator || '>'} ${r0.threshold_key || ''}`);
        } else {
            setSyntax(item.rule_syntax || "");
        }
    };

    const generateSyntax = () => {
        if (pt1 && pt2 && num) {
            const ruleStr = `${pt1},${pt2} ${op} num=${num}%`;
            setSyntax(ruleStr);
        }
    };

    const submitCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        const payload = {
            name: formName,
            description: formDesc,
            rules: [syntax],
            rule_syntax: syntax,
            is_update: !!editItem,
            requirements: { face_mesh: true, pose: true },
            default_preferences: {}
        };
        try {
            await fetch(`http://localhost:5001/api/${type}s/create`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            fetchItems();
            setEditItem(null);
            setFormName("");
            setFormDesc("");
            setSyntax("");
        } catch (e) {
            alert("Error saving");
        }
    };

    return (
        <div className={cn("space-y-6", className)}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* List */}
                <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-300 uppercase">作用中的 {type === 'skill' ? '動作' : '事件'}</h3>
                    {items.map(item => (
                        <div key={item.name} className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 flex justify-between items-start">
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="font-bold text-slate-200">{item.name}</span>
                                    <span className={cn("text-[10px] px-1.5 py-0.5 rounded", item.enabled ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-500/20 text-slate-400")}>
                                        {item.enabled ? '開啟' : '關閉'}
                                    </span>
                                </div>
                                <p className="text-xs text-slate-400 mt-1">{item.description}</p>
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => handleEdit(item)} className="p-1.5 bg-slate-700 hover:bg-slate-600 rounded text-slate-300" title="編輯">
                                    <Edit className="w-4 h-4" />
                                </button>
                                <button onClick={() => handleToggle(item.name, !item.enabled)} className={cn("p-1.5 rounded", item.enabled ? "bg-red-500/20 text-red-400" : "bg-emerald-500/20 text-emerald-400")} title={item.enabled ? "關閉" : "開啟"}>
                                    {item.enabled ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
                                </button>
                                {!["slouch", "sway", "lean"].includes(item.name) && (
                                    <button onClick={() => handleDelete(item.name)} className="p-1.5 bg-red-500/20 hover:bg-red-500/40 rounded text-red-400" title="刪除">
                                        <X className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Builder Form */}
                <div className="bg-slate-800/30 p-4 rounded-xl border border-slate-700">
                    <h3 className="text-sm font-bold text-slate-300 uppercase mb-4">{editItem ? '編輯' : '建立'} {type === 'skill' ? '動作' : '事件'}</h3>
                    <form onSubmit={submitCreate} className="space-y-4">
                        <div>
                            <label className="text-xs text-slate-400 block mb-1">ID 名稱 (需英文小寫)</label>
                            <input value={formName} onChange={e => setFormName(e.target.value)} required readOnly={!!editItem} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:border-violet-500 outline-none" />
                        </div>
                        <div>
                            <label className="text-xs text-slate-400 block mb-1">中文描述</label>
                            <input value={formDesc} onChange={e => setFormDesc(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:border-violet-500 outline-none" />
                        </div>

                        {type === 'skill' && (
                            <div className="bg-slate-900 p-3 rounded-lg border border-slate-700 space-y-2">
                                <label className="text-xs text-slate-400 font-semibold">快速點位 ID 建構</label>
                                <div className="grid grid-cols-2 gap-2">
                                    <input placeholder="點位1 (如 f1)" value={pt1} onChange={e => setPt1(e.target.value)} className="bg-slate-800 border border-slate-600 rounded p-1.5 text-xs text-white" />
                                    <input placeholder="點位2 (如 f152)" value={pt2} onChange={e => setPt2(e.target.value)} className="bg-slate-800 border border-slate-600 rounded p-1.5 text-xs text-white" />
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                    <select value={op} onChange={e => setOp(e.target.value)} className="bg-slate-800 border border-slate-600 rounded p-1.5 text-xs text-white">
                                        <option value="><">{'>< (縮小)'}</option>
                                        <option value="<>">{'<> (放大)'}</option>
                                    </select>
                                    <input placeholder="閾值 %" value={num} onChange={e => setNum(e.target.value)} className="bg-slate-800 border border-slate-600 rounded p-1.5 text-xs text-white" />
                                </div>
                                <button type="button" onClick={generateSyntax} className="w-full py-1.5 bg-slate-700 hover:bg-slate-600 text-xs text-white rounded">產生語法</button>
                            </div>
                        )}

                        <div>
                            <label className="text-xs text-slate-400 block mb-1">語法規則</label>
                            <textarea required value={syntax} onChange={e => setSyntax(e.target.value)} rows={2} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:border-violet-500 outline-none font-mono" />
                        </div>

                        <div className="flex gap-2">
                            {editItem && (
                                <button type="button" onClick={() => setEditItem(null)} className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white">
                                    取消
                                </button>
                            )}
                            <button type="submit" className="flex-1 flex items-center justify-center gap-2 py-2 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm text-white font-medium">
                                <Save className="w-4 h-4" />
                                儲存套用
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
