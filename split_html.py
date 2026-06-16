import re
import os

# Read the original file
with open('web/Monitor_backup.html', 'r', encoding='utf-8') as f:
    content = f.read()

pages = {
    'dashboard': ('web/monitor.html', '/'),
    'camera': ('web/camera.html', '/camera'),
    'skills': ('web/skills.html', '/skills'),
    'events': ('web/events.html', '/events')
}

tabs = ['dashboard', 'camera', 'skills', 'events']
titles = {
    'dashboard': '即時監控 (Monitor)',
    'camera': '相機設定 (Camera)',
    'skills': '技能中心 (Skills Hub)',
    'events': '事件處理 (Events)'
}

# The nav block
nav_regex = re.compile(r'<div class="flex border-b border-\[#b0aea5\]/10 mb-8 font-heading">.*?</div>', re.DOTALL)

def build_nav(active_tab):
    nav = '<div class="flex border-b border-[#b0aea5]/10 mb-8 font-heading">\n'
    for tab in tabs:
        href = pages[tab][1]
        if tab == active_tab:
            classes = 'px-6 py-3 text-sm font-semibold border-b-2 border-[#d97757] text-[#faf9f5] transition-all duration-200'
        else:
            classes = 'px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-[#b0aea5] hover:text-[#faf9f5] transition-all duration-200'
        nav += f'            <a href="{href}" class="{classes}">\n                {titles[tab]}\n            </a>\n'
    nav += '        </div>'
    return nav

# The tabs content blocks
def extract_tab_content(tab_idx):
    if tab_idx == 4:
        regex = r'(<!-- Tab 4.*?)(?=<!-- ════════)'
    else:
        regex = rf'(<!-- Tab {tab_idx}.*?)(?=<!-- Tab {tab_idx+1}:)'
    match = re.search(regex, content, re.DOTALL)
    return match.group(1) if match else ""

tab_contents = {
    'dashboard': extract_tab_content(1),
    'camera': extract_tab_content(2),
    'skills': extract_tab_content(3),
    'events': extract_tab_content(4),
}

# Also need to extract the Edit Modals
modals_regex = r'(<!-- ════════.*?)<script>'
modals_match = re.search(modals_regex, content, re.DOTALL)
modals_html = modals_match.group(1) if modals_match else ""

# Extract the header and footer
header_regex = r'(.*?<div class="flex border-b border-\[#b0aea5\]/10 mb-8 font-heading">.*?</div>)'
header_match = re.search(header_regex, content, re.DOTALL)
header_html = header_match.group(1) if header_match else content.split('<!-- Tab 1:')[0]

footer_html = "<script>\n" + content.split('<script>')[1]

# Remove the nav block from header_html because we will insert a custom one
header_html = nav_regex.sub('<!-- NAV -->', header_html)

for tab in tabs:
    page_html = header_html.replace('<!-- NAV -->', build_nav(tab))
    tab_html = tab_contents[tab]
    tab_html = tab_html.replace('class="hidden ', 'class="')
    page_html += "\n" + tab_html + "\n"
    page_html += modals_html + "\n"
    page_html += footer_html
    
    with open(pages[tab][0], 'w', encoding='utf-8') as f:
        f.write(page_html)

print("Split generated successfully")
