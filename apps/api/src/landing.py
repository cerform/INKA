"""Landing page and first setup endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import json

router = APIRouter(prefix="/", tags=["landing"])

SETUP_STATUS = {
    "database": False,
    "telegram_bot": False,
    "admin_panel": False,
    "api_ready": True,
}

SETUP_STEPS = [
    {
        "id": 1,
        "title": "🗄️ Setup Database",
        "description": "Configure PostgreSQL connection",
        "command": "make migrate",
        "status": "pending",
    },
    {
        "id": 2,
        "title": "🤖 Configure Telegram Bot",
        "description": "Get token from @BotFather and set BOT_TOKEN",
        "command": "export BOT_TOKEN=your_token_here",
        "status": "pending",
    },
    {
        "id": 3,
        "title": "🎨 Setup Admin Panel",
        "description": "Install dependencies and build",
        "command": "cd apps/admin && npm install && npm run build",
        "status": "pending",
    },
    {
        "id": 4,
        "title": "✅ Run Tests",
        "description": "Verify everything works",
        "command": "make test",
        "status": "pending",
    },
]


@router.get("/", response_class=HTMLResponse)
async def landing_page():
    """Return interactive landing page with first setup."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INKA - Tattoo Salon Admin System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            width: 100%;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 50px;
            animation: slideDown 0.8s ease-out;
        }
        
        .header h1 {
            font-size: 3.5em;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.95;
            margin-bottom: 10px;
        }
        
        .status-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .status-badge.online {
            background: rgba(76, 175, 80, 0.3);
            border: 1px solid #4caf50;
        }
        
        .setup-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
            animation: slideUp 0.8s ease-out 0.2s both;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0,0,0,0.2);
        }
        
        .card-icon {
            font-size: 2.5em;
            margin-bottom: 15px;
        }
        
        .card h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .card p {
            color: #666;
            font-size: 0.95em;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        
        .card-code {
            background: #f5f5f5;
            border-left: 4px solid #667eea;
            padding: 12px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #333;
            word-break: break-all;
            margin-bottom: 15px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-indicator.pending {
            background-color: #ff9800;
            animation: pulse 2s infinite;
        }
        
        .status-indicator.completed {
            background-color: #4caf50;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.95em;
            font-weight: 600;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #666;
            margin-right: 10px;
        }
        
        .quick-links {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            animation: slideUp 0.8s ease-out 0.4s both;
        }
        
        .quick-links h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .links-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .link-item {
            padding: 15px;
            background: #f9f9f9;
            border-radius: 8px;
            text-decoration: none;
            color: #667eea;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 1px solid #e0e0e0;
        }
        
        .link-item:hover {
            background: #667eea;
            color: white;
            transform: translateX(5px);
        }
        
        .api-docs {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            animation: slideUp 0.8s ease-out 0.6s both;
        }
        
        .api-docs h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .endpoint {
            margin-bottom: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }
        
        .endpoint-method {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.85em;
            margin-right: 10px;
        }
        
        .endpoint-method.get { background: #61affe; color: white; }
        .endpoint-method.post { background: #49cc90; color: white; }
        .endpoint-method.put { background: #fca130; color: white; }
        .endpoint-method.delete { background: #f93e3e; color: white; }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 50px;
            opacity: 0.8;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2.5em;
            }
            
            .setup-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 INKA</h1>
            <p>Tattoo Salon Admin System</p>
            <span class="status-badge online">✓ API Running</span>
        </div>
        
        <div class="setup-grid">
            <div class="card">
                <div class="card-icon">🚀</div>
                <h3>Quick Start</h3>
                <p>Get up and running in seconds with Docker</p>
                <div class="card-code">docker compose up</div>
                <button class="btn" onclick="copyToClipboard('docker compose up')">Copy Command</button>
            </div>
            
            <div class="card">
                <div class="card-icon">📚</div>
                <h3>Documentation</h3>
                <p>Read comprehensive guides and best practices</p>
                <div class="card-code">/docs</div>
                <a href="/docs" class="btn">Open Docs</a>
            </div>
            
            <div class="card">
                <div class="card-icon">🔗</div>
                <h3>API Reference</h3>
                <p>Interactive API documentation with Swagger</p>
                <div class="card-code">/docs</div>
                <a href="/docs" class="btn">View API</a>
            </div>
        </div>
        
        <div class="quick-links">
            <h2>Quick Links</h2>
            <div class="links-grid">
                <a href="/docs" class="link-item">📖 API Documentation</a>
                <a href="/redoc" class="link-item">📋 ReDoc</a>
                <a href="https://github.com" class="link-item" target="_blank">🔗 GitHub</a>
                <a href="/health" class="link-item">❤️ Health Check</a>
            </div>
        </div>
        
        <div class="api-docs">
            <h2>Available Endpoints</h2>
            <div class="endpoint">
                <span class="endpoint-method get">GET</span>
                <strong>/health</strong>
                <p style="margin-top: 8px; color: #666; font-size: 0.9em;">Check API health status</p>
            </div>
            <div class="endpoint">
                <span class="endpoint-method get">GET</span>
                <strong>/api/v1/setup</strong>
                <p style="margin-top: 8px; color: #666; font-size: 0.9em;">Get first setup status</p>
            </div>
            <div class="endpoint">
                <span class="endpoint-method post">POST</span>
                <strong>/api/v1/setup/complete</strong>
                <p style="margin-top: 8px; color: #666; font-size: 0.9em;">Mark setup step as complete</p>
            </div>
        </div>
        
        <div class="footer">
            <p>🚀 Ready to deploy? Check the deployment guide in /docs</p>
            <p style="margin-top: 10px; font-size: 0.9em;">INKA v1.0 • © 2026 Tattoo Salon Admin</p>
        </div>
    </div>
    
    <script>
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('Command copied to clipboard!');
            }).catch(() => {
                alert('Failed to copy');
            });
        }
        
        // Check health on page load
        fetch('/health')
            .then(r => r.json())
            .then(data => console.log('API Health:', data))
            .catch(e => console.warn('Health check failed:', e));
    </script>
</body>
</html>
    """


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "inka-api",
        "version": "1.0.0",
    }


@router.get("/api/v1/setup")
async def get_setup_status():
    """Get first setup status."""
    return {
        "setup_complete": False,
        "steps": SETUP_STEPS,
        "status": SETUP_STATUS,
    }


@router.post("/api/v1/setup/complete/{step_id}")
async def complete_setup_step(step_id: int):
    """Mark a setup step as complete."""
    for step in SETUP_STEPS:
        if step["id"] == step_id:
            step["status"] = "completed"
            return {"message": f"Step {step_id} completed", "step": step}
    raise HTTPException(status_code=404, detail="Step not found")
