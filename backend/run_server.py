"""
run_server.py — starts the FairHire backend and keeps it running.
Run this with: venv312\Scripts\python.exe run_server.py
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
        reload=False,
    )
