from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home():
    return {"msg": "Atualização feita! Tudo funcionando! 🎉"}
