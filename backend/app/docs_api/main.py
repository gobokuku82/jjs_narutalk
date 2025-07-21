from fastapi import FastAPI
from classify_module import router

app = FastAPI(title="Document Processing API", version="1.0.0")

app.include_router(router, prefix="/api/docs", tags=["documents"])

@app.get("/")
async def root():
    return {"message": "Document Processing API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)