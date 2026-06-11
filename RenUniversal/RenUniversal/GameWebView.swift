import SwiftUI
import WebKit

struct GameWebView: UIViewRepresentable {
    @ObservedObject var state: SharedState
    let htmlFileName: String
    
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let webView = WKWebView(frame: .zero, configuration: config)
        
        if let app = state.apps.first(where: { $0.url == htmlFileName }), let html = app.html, !html.isEmpty {
            webView.loadHTMLString(html, baseURL: nil)
        } else if htmlFileName == "local://ctar_counter" || htmlFileName.isEmpty {
            let mockHtml = """
            <html><body>
            <h1 style="text-align:center;font-family:sans-serif;margin-top:50px;">CTAR Monitor</h1>
            <div id="status" style="text-align:center;font-size:30px;color:gray;">WAITING...</div>
            <div id="count" style="text-align:center;font-size:80px;font-weight:bold;margin-top:20px;">0</div>
            <script>
            window.updatePostureData = function(jsonStr) {
                try {
                    let data = JSON.parse(jsonStr);
                    let counts = data.trigger_counts;
                    let c = counts['ctar_tuck'] || 0;
                    document.getElementById('count').innerText = c;
                    let isTucked = data.active_triggers && data.active_triggers['ctar_tuck'] === true;
                    let stat = document.getElementById('status');
                    stat.innerText = isTucked ? "TUCKED" : "IDLE";
                    stat.style.color = isTucked ? "green" : "gray";
                } catch(e) {}
            }
            </script>
            </body></html>
            """
            webView.loadHTMLString(mockHtml, baseURL: nil)
        } else if let url = URL(string: htmlFileName) {
            webView.load(URLRequest(url: url))
        }
        
        return webView
    }
    
    func updateUIView(_ uiView: WKWebView, context: Context) {
        // Build JSON from SharedState active triggers and counts
        let payload: [String: Any] = [
            "active_triggers": state.activeTriggers,
            "trigger_counts": state.triggerCounts
        ]
        
        if let data = try? JSONSerialization.data(withJSONObject: payload),
           let jsonStr = String(data: data, encoding: .utf8) {
            // Call JS function
            let js = "if(typeof updatePostureData === 'function') { updatePostureData('\(jsonStr)'); }"
            uiView.evaluateJavaScript(js, completionHandler: nil)
        }
    }
}
