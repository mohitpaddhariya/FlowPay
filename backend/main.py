from fastapi import FastAPI

app = FastAPI(title="FlowPay API")

@app.get("/")
def read_root():
    return {"message": "Welcome to FlowPay API - Initial Setup"}
