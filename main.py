from fastapi import FastAPI
import models
from database import engine
from routers import users


app = FastAPI()
models.Base.metadata.create_all(bind=engine)

app.include_router(users.router)