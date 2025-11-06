from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from . import models
from .database import engine, get_db
from .models import Post
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import secrets
from datetime import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
security = HTTPBasic()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get(
    "/",
    response_class=HTMLResponse,
)
async def root(request: Request, db: Session = Depends(get_db)):

    posts = db.query(Post).order_by(Post.id.desc()).all()

    return templates.TemplateResponse(
        "posts.html", {"request": request, "posts": posts}
    )


@app.get("/posts/{id}", response_class=HTMLResponse)
async def get_posts(id: int, request: Request, db: Session = Depends(get_db)):

    post = db.query(Post).filter(Post.id == id).first()
    return templates.TemplateResponse("post.html", {"request": request, "post": post})


def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"kacperg"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"swordfish"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/users/me")
async def read_current_user(
    username: Annotated[str, Depends(get_current_username)],
    request: Request,
    db: Session = Depends(get_db),
):

    posts = db.query(Post).all()

    return templates.TemplateResponse("base.html", {"request": request, "posts": posts})


@app.get("/new")
async def create_new_post(
    username: Annotated[str, Depends(get_current_username)], request: Request
):

    return templates.TemplateResponse("new.html", {"request": request})


@app.post("/new")
async def post_new_page(
    username: Annotated[str, Depends(get_current_username)],
    newpost: Annotated[str, Form()],
    title: Annotated[str, Form()],
    db: Session = Depends(get_db),
):

    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")

    new_post = models.Post(title=title, content=newpost, created_at=formatted_time)

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return RedirectResponse(url="/", status_code=303)


@app.get("/edit/{id}")
async def show_edit_post(
    id: int,
    username: Annotated[str, Depends(get_current_username)],
    request: Request,
    db: Session = Depends(get_db),
):

    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse("edit.html", {"request": request, "post": post})


@app.post("/edit/{id}")
async def edit_post(
    id: int,
    username: Annotated[str, Depends(get_current_username)],
    newpost: Annotated[str, Form()],
    title: Annotated[str, Form()],
    db: Session = Depends(get_db),
):

    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.title = title
    post.content = newpost
    db.commit()

    db.refresh(post)
    return RedirectResponse(url="/", status_code=303)


@app.get("/delete/{id}")
async def click_delete_post(
    id: int,
    username: Annotated[str, Depends(get_current_username)],
    request: Request,
    db: Session = Depends(get_db),
):

    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse("delete.html", {"request": request, "post": post})


@app.post("/delete/{id}")
async def delete_post(
    id: int,
    username: Annotated[str, Depends(get_current_username)],
    db: Session = Depends(get_db),
):

    post = db.query(Post).filter(Post.id == id).first()
    db.delete(post)
    db.commit()

    return RedirectResponse(url="/", status_code=303)
