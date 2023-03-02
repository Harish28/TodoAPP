import sys

from starlette.responses import RedirectResponse

sys.path.append("..")

from typing import Optional
from fastapi import FastAPI, Depends, status, HTTPException, APIRouter, Request, Response, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
import models
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal, engine
from datetime import timedelta
from fastapi.encoders import jsonable_encoder
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


class LoginForm:
    def __init__(self, request: Request):
        self.request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")


class CreateUser(BaseModel):
    email: Optional[str]
    username: str
    first_name: str
    last_name: str
    password: str


"""
Basic setup
"""
models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={
        404: {"user": "User is not authenticated"}
    }
)

"""
Authentication and Authorization 
"""
bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRETE_KEY = "adsflkafgakijVGUVkldfjkLKBGLKNdlfngwfgo432"
oauth_bearer = OAuth2PasswordBearer(tokenUrl="/token")

"""
Import methods
"""


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "expire": jsonable_encoder(expires_delta)}
    return jwt.encode(encode, SECRETE_KEY, algorithm="HS256")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_hash(password: str):
    return bcrypt.hash(password)


def verify_password(plain_pwd, hashed_pwd):
    return bcrypt.verify(plain_pwd, hashed_pwd)


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(models.Users). \
        filter(models.Users.username == username).first()
    if user is None:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(request: Request, token: str = Depends(oauth_bearer)):
    try:
        token = request.cookies.get("access-token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRETE_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        user_id = payload.get("id")
        if user_id is None or username is None:
            return None
        return {"username": username, "user_id": user_id}
    except JWTError:
        raise get_user_exception()


"""
Exceptions 
"""


def get_user_exception():
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate the user",
        headers={"WWW-Authenticate": "Bearer"}
    )
    return credential_exception


def token_exception():
    token__exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}
    )
    return token__exception


"""
End points
"""


@router.post("/create/user", status_code=status.HTTP_201_CREATED)
async def create_user(createUser: CreateUser, db: Session = Depends(get_db)):
    create_user_model = models.Users()
    create_user_model.email = createUser.email
    create_user_model.last_name = createUser.last_name
    create_user_model.first_name = createUser.first_name
    create_user_model.username = createUser.username
    create_user_model.hashed_password = get_hash(createUser.password)
    create_user_model.is_active = True
    db.add(create_user_model)
    db.commit()
    return {
        "status": 201,
        "Message": "Todos has been added successfully"
    }


@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False
    token = create_access_token(user.username,
                                user.id,
                                expires_delta=timedelta(minutes=60))
    response.set_cookie(key="access-token", value=token, httponly=True)
    return True


@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    print(request)
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

        isValid = await login_for_access_token(response=response, form_data=form, db=db)
        if isValid:
            return response
        else:
            return templates.TemplateResponse("login.html",
                                              {"request": request, "msg": "Incorrect Username or Password"})
    except HTTPException:
        return templates.TemplateResponse("login.html", {"request": request, "msg": "Something went wrong"})


@router.get("/logout")
async def logout(request: Request):
    response = templates.TemplateResponse("login.html", {"request": request, "msg": "Logout"})
    response.delete_cookie(key="access-token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(request: Request, email: str = Form(...), username: str = Form(...), firstname: str = Form(...),
                   lastname: str = Form(...), password: str = Form(...), password2: str = Form(...),
                   db: Session = Depends(get_db)):
    val1 = db.query(models.Users).filter(models.Users.username == username).first()
    val2 = db.query(models.Users).filter(models.Users.email == email).first()
    if password != password2 or val1 is not None or val2 is not None:
        return templates.TemplateResponse("register.html", {"request": request, "msg": "Invalid Registration Request"})
    user_model = models.Users()
    user_model.email = email
    user_model.username = username
    user_model.first_name = firstname
    user_model.last_name = lastname
    user_model.hashed_password = get_hash(password)
    user_model.is_active = True
    db.add(user_model)
    db.commit()
    return templates.TemplateResponse("login.html", {"request": request, "msg": "User successfully created"})
