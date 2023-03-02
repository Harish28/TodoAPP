from fastapi import FastAPI, Depends
from starlette.staticfiles import StaticFiles
import models
from database import engine
from routers import auth, todos, users
app = FastAPI()
print(models.Base.metadata)
models.Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(todos.router)
app.include_router(auth.router)
app.include_router(users.router)