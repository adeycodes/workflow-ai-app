from fastapi import FastAPI, Request, Response
import os

def create_app():
    app = FastAPI()
    
    @app.get("/api/test")
    async def test_endpoint():
        return {
            "status": "success",
            "message": "Vercel Python function is working!",
            "environment": dict(os.environ)
        }
    
    return app

# This is the entry point Vercel will use
app = create_app()
