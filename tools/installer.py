import os
import sys
import json
import shutil
from pathlib import Path

def print_banner():
    print("="*60)
    print(" RenUniversal Plugin Installer")
    print("="*60)

def main():
    print_banner()
    if len(sys.argv) < 2:
        print("Usage: python tools/installer.py <path_to_plugin>")
        sys.exit(1)

    plugin_dir = os.path.abspath(sys.argv[1])
    config_file = os.path.join(plugin_dir, ".renuniversal")

    if not os.path.exists(plugin_dir):
        print(f"Error: Plugin directory '{plugin_dir}' does not exist.")
        sys.exit(1)
        
    if not os.path.exists(config_file):
        print(f"Error: Missing '.renuniversal' manifest in {plugin_dir}")
        sys.exit(1)

    with open(config_file, 'r', encoding='utf-8') as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in .renuniversal - {e}")
            sys.exit(1)

    name = manifest.get("name", "UnknownPlugin")
    version = manifest.get("version", "1.0")
    print(f"[*] Installing Plugin: {name} (v{version})")
    print(f"[*] Description: {manifest.get('description', '')}\n")

    # Target system paths
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_skills_dir = os.path.join(root_dir, "skills")
    target_events_dir = os.path.join(root_dir, "events")
    target_apps_dir = os.path.join(root_dir, "web", "apps")

    # Install Skills
    skills = manifest.get("skills", [])
    if skills:
        print("[+] Installing Skills...")
        for skill_path in skills:
            src = os.path.join(plugin_dir, skill_path)
            if not os.path.exists(src):
                print(f"    [Warning] Skill folder not found: {src}")
                continue
            
            basename = os.path.basename(os.path.normpath(src))
            dst = os.path.join(target_skills_dir, basename)
            
            if os.path.exists(dst):
                print(f"    [!] Overwriting existing skill: {basename}")
                shutil.rmtree(dst)
                
            shutil.copytree(src, dst)
            print(f"    -> Installed skill: {basename}")

    # Install Events
    events = manifest.get("events", [])
    if events:
        print("[+] Installing Events...")
        for event_path in events:
            src = os.path.join(plugin_dir, event_path)
            if not os.path.exists(src):
                print(f"    [Warning] Event folder not found: {src}")
                continue
                
            basename = os.path.basename(os.path.normpath(src))
            dst = os.path.join(target_events_dir, basename)
            
            if os.path.exists(dst):
                print(f"    [!] Overwriting existing event: {basename}")
                shutil.rmtree(dst)
                
            shutil.copytree(src, dst)
            print(f"    -> Installed event: {basename}")

    # Install Apps
    apps = manifest.get("apps", [])
    if apps:
        print("[+] Installing HTML Apps...")
        os.makedirs(target_apps_dir, exist_ok=True)
        for app_path in apps:
            src = os.path.join(plugin_dir, app_path)
            if not os.path.exists(src):
                print(f"    [Warning] App file not found: {src}")
                continue
                
            basename = os.path.basename(os.path.normpath(src))
            dst = os.path.join(target_apps_dir, basename)
            
            shutil.copy2(src, dst)
            print(f"    -> Installed app: {basename}")

    print("\n" + "="*60)
    print(f"✓ Installation of '{name}' completed successfully!")
    print("="*60)

if __name__ == "__main__":
    main()
