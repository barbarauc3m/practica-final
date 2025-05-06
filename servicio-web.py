# sudo apt install python3-fastapi
# sudo apt install uvicorn


from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/datetime")
async def get_datetime():
    now = datetime.now()
    return {"datetime": now.strftime("%d/%m/%Y %H:%M:%S")}

# Para arrancar:
#    uvicorn servicio-web:app --host 127.0.0.1 --port 8000 --reload
