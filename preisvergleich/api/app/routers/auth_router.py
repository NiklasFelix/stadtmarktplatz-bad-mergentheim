from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from common.db import get_cursor

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
def login(body: LoginRequest):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE username = %s", (body.username,))
        user = cur.fetchone()
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Benutzername oder Passwort ist falsch")
    token = create_access_token(user)
    return {
        "access_token": token,
        "user": {"id": user["id"], "username": user["username"], "name": user["name"], "role": user["role"]},
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


@router.put("/me/password")
def change_password(body: PasswordChangeRequest, user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user["id"],))
        row = cur.fetchone()
        if not row or not verify_password(body.current_password, row["password_hash"]):
            raise HTTPException(status_code=400, detail="Aktuelles Passwort ist falsch")
        if len(body.new_password) < 8:
            raise HTTPException(status_code=400, detail="Neues Passwort muss mindestens 8 Zeichen haben")
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(body.new_password), user["id"]),
        )
    return {"status": "password_changed"}
