from typing import List, Optional
from fastapi import FastAPI, status, Depends, HTTPException, BackgroundTasks
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from back.models import User, Item
from back.database import SessionLocal, engine
from datetime import datetime, timedelta
from back.config import SECRET_KEY
import time

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

origins = [
    "http://localhost:3000",  # Adjust the port if your frontend runs on a different one
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins from the list
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

token_blacklist = set()

class ItemCreate(BaseModel):
    title: str
    content: str
    expiration_date: Optional[datetime] = None

class ItemResponse(BaseModel):
    id: int
    title: str
    content: str
    short_url: str
    user_id: int
    expiration_date: Optional[datetime] = None
    owner_username: str  # Добавляем поле для имени пользователя

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return "complete"

@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)

# Authenticate the user
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

# Create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")
        return username
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid or expired")

@app.get("/verify-token/{token}")
async def verify_user_token(token: str):
    username = verify_token(token=token)
    return {"username": username}

@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_item = Item(
        title=item.title,
        content=item.content,
        user_id=user.id,
        expiration_date=item.expiration_date
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Возвращаем объект ItemResponse с именем пользователя
    return {
        "id": db_item.id,
        "title": db_item.title,
        "content": db_item.content,
        "short_url": db_item.short_url,
        "user_id": db_item.user_id,
        "expiration_date": db_item.expiration_date,
        "owner_username": user.username
    }

@app.get("/items/", response_model=List[ItemResponse])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    current_time = datetime.utcnow()
    items = (
        db.query(Item)
        .join(User)
        .options(joinedload(Item.user))
        .filter((Item.expiration_date.is_(None) | (Item.expiration_date > current_time)))
        .offset(skip)
        .limit(limit)
        .all()
    )

    item_responses = []
    for item in items:
        item_response = ItemResponse(
            id=item.id,
            title=item.title,
            content=item.content,
            short_url=item.short_url,
            user_id=item.user_id,
            expiration_date=item.expiration_date,
            owner_username=item.user.username
        )
        item_responses.append(item_response)

    return item_responses



@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_time = datetime.utcnow()
    item = db.query(Item).options(joinedload(Item.user)).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # Включаем owner_username в ответ
    item_response = ItemResponse(
        id=item.id,
        title=item.title,
        content=item.content,
        short_url=item.short_url,
        user_id=item.user_id,
        expiration_date=item.expiration_date,
        owner_username=item.user.username  # Добавляем имя пользователя
    )
    return item_response

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    item = db.query(Item).filter(Item.id == item_id, Item.user_id == user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}

def remove_expired_items(db: Session):
    current_time = datetime.utcnow()
    expired_items = db.query(Item).filter(Item.expiration_date <= current_time).all()
    for item in expired_items:
        db.delete(item)
    db.commit()

@app.on_event("startup")
@repeat_every(seconds=60 * 60)  # Every hour
def cleanup_expired_items():
    db = SessionLocal()
    try:
        remove_expired_items(db)
    finally:
        db.close()

@app.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    token_blacklist.add(token)
    return {"message": "Successfully logged out"}
