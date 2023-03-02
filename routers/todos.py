import sys
sys.path.append("..")

from starlette.responses import RedirectResponse
from starlette import status
from fastapi import Depends, status, HTTPException, APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from .auth import get_current_user, get_user_exception


router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={
        404: {"description": "Not found"}
    }
)
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


class Todos(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=200)
    priority: int = Field(gt=0, lt=6, description = "Priority must be b/w 1 t0 5")
    complete: bool = Field(default=False)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request,db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/auth", status_code=status.HTTP_302_FOUND)

    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get("user_id")).all()
    return templates.TemplateResponse("index.html", {"request": request, "todos":todos, "user": user})


@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/auth", status_code=status.HTTP_302_FOUND)
    todos = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    return templates.TemplateResponse("edit-todo.html", {"request": request, "todos": todos})


@router.post("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, title: str = Form(...), description: str = Form(...), priority: int = Form(...),
                    db:Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/auth", status_code=status.HTTP_302_FOUND)
    todos = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todos.title = title
    todos.description = description
    todos.priority = priority
    db.add(todos)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/auth", status_code=status.HTTP_302_FOUND)
    todos = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todos is None:
        RedirectResponse(url="/todos",status_code=status.HTTP_302_FOUND)
    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/auth", status_code=status.HTTP_302_FOUND)
    todos = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todos.complete = not todos.complete
    db.add(todos)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/add-todo", response_class=HTMLResponse)
async def add_todo(request: Request,):
    return templates.TemplateResponse("add-todo.html", {"request": request})


@router.post("/add-todo", response_class=HTMLResponse)
async def add_todo(request: Request, title: str = Form(...), description: str = Form(...), priority: int = Form(...),
                   db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/auth", status_code=status.HTTP_302_FOUND)
    todo_model = models.Todos()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.owner_id = user.get("user_id")
    todo_model.complete = False
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)










#
# @router.get("/test")
# async def test(request: Request):
#     return templates.TemplateResponse("index.html",{"request": request})
#
#
# @router.get("/")
# async def read_all(db: Session = Depends(get_db)):
#     return db.query(models.Todos).all()
#
#
# @router.get("/{id}")
# async def read_by_id(id: int, db: Session = Depends(get_db)):
#     return db.query(models.Todos).get(ident=id)
#
#
# @router.get("/user")
# async def get_todo_by_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
#     if user is None:
#         raise get_user_exception()
#     return db.query(models.Todos).filter(models.Todos.owner_id == user.get("user_id")).all()
#
#
# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def create_todo(todo: Todos,
#                       user: dict = Depends(get_current_user),
#                       db: Session = Depends(get_db)):
#     if user is None:
#         raise get_user_exception()
#
#     todo_model = models.Todos()
#     todo_model.title = todo.title
#     todo_model.description = todo.description
#     todo_model.priority = todo.priority
#     todo_model.complete = todo.complete
#     todo_model.owner_id = user.get("user_id")
#     db.add(todo_model)
#     db.commit()
#     return {
#         "status": 201,
#         "Message": "Todos has been added successfully"
#     }
#
#
# @router.put("/{id}")
# async def update_todo(id: int,
#                       todo: Todos,
#                       user: dict = Depends(get_current_user),
#                       db: Session = Depends(get_db)):
#     if user is None:
#         raise get_user_exception()
#     todo_model = db.query(models.Todos).\
#         filter(models.Todos.id == id).\
#         filter(models.Todos.owner_id == user.get("user_id")).\
#         first()
#     if todo_model is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Request todo with id = {id} not found"
#         )
#     todo_model.title = todo.title
#     todo_model.description = todo.description
#     todo_model.priority = todo.priority
#     todo_model.complete = todo.complete
#     db.add(todo_model)
#     db.commit()
#     return {
#         "status": 200,
#         "Message": "Todos has been updated successfully"
#     }
#
#
# @router.delete("/{id}")
# async def delete_todo(id: int,
#                       user: dict = Depends(get_current_user),
#                       db: Session = Depends(get_db)):
#     if user is None:
#         raise get_user_exception()
#     todo_model = db.query(models.Todos).\
#         filter(models.Todos.id == id).\
#         filter(models.Todos.owner_id == user.get("user_id")).\
#         first()
#     if todo_model is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Request todo with id = {id} not found"
#         )
#     db.query(models.Todos).filter(models.Todos.id == id).delete()
#     db.commit()
#     return {
#         "status": 200,
#         "Message": "Todos has been Deleted successfully"
#     }
