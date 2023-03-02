import sys
sys.path.append("..")
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models
from database import engine, SessionLocal
from .auth import get_db, get_current_user, get_user_exception, get_hash, verify_password

models.Base.metadata.create_all(bind=engine)
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        404: {"Detail": "User not found"}
    }
)


class UserVerification(BaseModel):
    user_name: str
    password: str
    new_password: str



@router.get("/")
async def read_all_users(db: Session = Depends(get_db)):
    return db.query(models.Users).all()


@router.get("/user/{user_id}")
async def user_by_path(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).\
        filter(models.Users.id == user_id).\
        first()
    if user_model is not None:
        return user_model
    raise HTTPException(
        status_code= 404,
        detail="Invalid User Id"
    )


@router.get("/user/")
async def user_by_query(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users). \
        filter(models.Users.id == user_id). \
        first()
    if user_model is not None:
        return user_model
    raise HTTPException(
        status_code=404,
        detail="Invalid User Id"
    )


@router.put("/password_change")
async def update_password(user_verification: UserVerification, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    db_user = db.query(models.Users).filter(models.Users.id == user.get("user_id")).first()
    if db_user.username == user_verification.user_name and \
            verify_password(user_verification.password, db_user.hashed_password):
        db_user.hashed_password = get_hash(user_verification.new_password)
        db.add(db_user)
        db.commit()
        return {
            "status": 200,
            "message": "Password has been updated successfully"
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Username or Password is incorrect"
        )


@router.delete("/user")
async def delete_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    db_user = db.query(models.Users).filter(models.Users.id == user.get("user_id")).first()
    if db_user is None:
        raise HTTPException(
            status_code= 404,
            detail="User not found"
        )
    db.query(models.Users).filter(models.Users.id == user.get("user_id")).delete()
    db.commit()
    return {
        "status": 200,
        "Message": "User has been deleted"
    }
