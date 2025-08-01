"""
ASGI server entry point for the WAVE Backend API.
"""

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "wave_backend.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
