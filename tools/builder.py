import os
import sys
import json
import shutil
import argparse
from pathlib import Path

def print_banner():
    print("="*60)
    print(" RenUniversal Plugin Builder")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="打包 RenUniversal 外掛")
    parser.add_argument("--name", type=str, required=True, help="外掛名稱 (例如: NeckGame)")
    parser.add_argument("--version", type=str, default="1.0", help="外掛版本 (預設: 1.0)")
    parser.add_argument("--desc", type=str, default="", help="外掛描述")
    parser.add_argument("--skills", type=str, nargs="*", default=[], help="要打包的 Skill 資料夾路徑 (例如: skills/lean skills/turn)")
    parser.add_argument("--events", type=str, nargs="*", default=[], help="要打包的 Event 檔案路徑 (例如: events/game.py)")
    parser.add_argument("--apps", type=str, nargs="*", default=[], help="要打包的 HTML App 檔案路徑 (例如: web/apps/game.html)")
    parser.add_argument("--out", type=str, default="dist", help="輸出目錄 (預設: dist)")

    args = parser.parse_args()
    print_banner()
    
    # 建立輸出目錄
    out_dir = os.path.join(args.out, args.name)
    if os.path.exists(out_dir):
        print(f"[*] 清除舊的建置目錄: {out_dir}")
        shutil.rmtree(out_dir)
        
    os.makedirs(out_dir, exist_ok=True)
    
    manifest = {
        "name": args.name,
        "version": args.version,
        "description": args.desc,
        "skills": [],
        "events": [],
        "apps": []
    }

    # 打包 Skills
    if args.skills:
        os.makedirs(os.path.join(out_dir, "skills"), exist_ok=True)
        print("[+] 正在打包 Skills...")
        for skill_path in args.skills:
            if not os.path.exists(skill_path):
                print(f"    [!] 找不到: {skill_path}，跳過。")
                continue
            basename = os.path.basename(os.path.normpath(skill_path))
            dst = os.path.join(out_dir, "skills", basename)
            shutil.copytree(skill_path, dst)
            manifest["skills"].append(f"skills/{basename}")
            print(f"    -> 加入: {skill_path}")

    # 打包 Events
    if args.events:
        os.makedirs(os.path.join(out_dir, "events"), exist_ok=True)
        print("[+] 正在打包 Events...")
        for event_path in args.events:
            if not os.path.exists(event_path):
                print(f"    [!] 找不到: {event_path}，跳過。")
                continue
            basename = os.path.basename(os.path.normpath(event_path))
            dst = os.path.join(out_dir, "events", basename)
            shutil.copytree(event_path, dst)
            manifest["events"].append(f"events/{basename}")
            print(f"    -> 加入: {event_path}")

    # 打包 Apps
    if args.apps:
        os.makedirs(os.path.join(out_dir, "apps"), exist_ok=True)
        print("[+] 正在打包 Apps...")
        for app_path in args.apps:
            if not os.path.exists(app_path):
                print(f"    [!] 找不到: {app_path}，跳過。")
                continue
            basename = os.path.basename(os.path.normpath(app_path))
            dst = os.path.join(out_dir, "apps", basename)
            shutil.copy2(app_path, dst)
            manifest["apps"].append(f"apps/{basename}")
            print(f"    -> 加入: {app_path}")

    # 產生 .renuniversal 檔案
    manifest_path = os.path.join(out_dir, ".renuniversal")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"\n[+] 成功產生配置檔: {manifest_path}")
    print("\n" + "="*60)
    print(f"✓ 外掛 '{args.name}' 已成功打包至: {out_dir}/")
    print("="*60)

if __name__ == "__main__":
    main()
