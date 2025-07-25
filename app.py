from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home():
    return {"msg": "Hello Compass! o teste está funcionando! 🎉"}
