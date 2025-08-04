#!/usr/bin/env python3
"""
Simple HTTP server to serve frontend files
"""
import http.server
import socketserver
import os

PORT = 8080

# Change to frontend directory
os.chdir('/workspaces/workflow-ai-app/workflowai-app/frontend')

Handler = http.server.SimpleHTTPRequestHandler

print(f"🚀 Serving frontend files at http://localhost:{PORT}")
print("📝 Available pages:")
print("   - http://localhost:8080/ (Landing page)")
print("   - http://localhost:8080/login.html")
print("   - http://localhost:8080/signup.html")
print("   - http://localhost:8080/dashboard.html")
print("   - http://localhost:8080/templates.html")
print("   - http://localhost:8080/builder.html")
print("   - http://localhost:8080/settings.html")
print("\n⚠️  Press Ctrl+C to stop the server")

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n🎯 Server started at http://localhost:{PORT}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Server stopped")