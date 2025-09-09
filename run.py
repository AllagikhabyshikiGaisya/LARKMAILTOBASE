import uvicorn
from src.config import Config

if __name__ == "__main__":
    print("Starting Lark Mail to Base Automation Server...")
    print(f"Server will run on port {Config.SERVER_PORT}")
    print(f"Webhook endpoint: {Config.WEBHOOK_PATH}")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=Config.SERVER_PORT,
        reload=True,
        log_level="info"
    )