import SwiftUI
import WebKit

struct GameWebView: UIViewRepresentable {
    @ObservedObject var state: SharedState
    let htmlFileName: String
    
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let webView = WKWebView(frame: .zero, configuration: config)
        
        // Load a mock HTML for demonstration if the file doesn't exist
        let mockHtml = """
        <html><body style="background:#1a1a1a;color:#fff;font-family:sans-serif;text-align:center;padding:50px;">
        <h2>\(htmlFileName)</h2>
        <p>Waiting for posture data...</p>
        <div id="data" style="font-family:monospace;color:#0f0;margin-top:20px;"></div>
        <script>
        function updatePostureData(jsonStr) {
            document.getElementById('data').innerText = jsonStr;
        }
        </script>
        </body></html>
        """
        webView.loadHTMLString(mockHtml, baseURL: nil)
        return webView
    }
    
    func updateUIView(_ uiView: WKWebView, context: Context) {
        // Build JSON from SharedState active triggers
        var payload: [String: Bool] = [:]
        for (k,v) in state.activeTriggers { payload[k] = v }
        
        if let data = try? JSONSerialization.data(withJSONObject: payload),
           let jsonStr = String(data: data, encoding: .utf8) {
            // Call JS function
            let js = "if(typeof updatePostureData === 'function') { updatePostureData('\(jsonStr)'); }"
            uiView.evaluateJavaScript(js, completionHandler: nil)
        }
    }
}
