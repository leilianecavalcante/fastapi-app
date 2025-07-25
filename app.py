from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home():
    return {"msg": "hello this is mensage intial - by leiliane."}
