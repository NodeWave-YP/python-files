from fastapi import FastAPI, Depends
from routes import auth, dashboard, register

app = FastAPI()


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(register.router)





