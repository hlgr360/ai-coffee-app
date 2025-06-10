from fastapi import FastAPI, Request, Form, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import aiosqlite
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
import uuid
import bcrypt
import secrets

# AI: Create FastAPI app instance
app = FastAPI()
# AI: Set up Jinja2 templates directory for HTML rendering
templates = Jinja2Templates(directory="templates")
# AI: SQLite database file path
DB_PATH = "coffee.db"

# AI: Mount static files for CSS/JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# AI: Define Pydantic models
class CoffeeEntry(BaseModel):
    user_id: str
    amount: float
    cup_id: Optional[str]
    timestamp: str

class Cup(BaseModel):
    id: Optional[str]
    user_id: str
    name: str
    size: float

class User(BaseModel):
    id: str
    username: str
    is_admin: bool
    must_change_password: bool

# AI: Helper to get current user (from session or fallback)
async def get_current_user():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT id, username, is_admin, must_change_password FROM users LIMIT 1')
        row = await cursor.fetchone()
        if row:
            return User(id=row[0], username=row[1], is_admin=bool(row[2]), must_change_password=bool(row[3]))
        return User(id="00000000-0000-0000-0000-000000000001", username="hlgr360", is_admin=False, must_change_password=False)

# AI: Get all cups for the current user
async def get_cups(user_id: str) -> List[Cup]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT id, user_id, name, size FROM cups WHERE user_id = ?', (user_id,))
        rows = await cursor.fetchall()
        return [Cup(id=row[0], user_id=row[1], name=row[2], size=row[3]) for row in rows]

# AI: Get default cup for the user
async def get_default_cup(user_id: str) -> Optional[Cup]:
    cups = await get_cups(user_id)
    return cups[0] if cups else None

# AI: Query the database for total coffee consumed per day (last 30 days)
async def get_daily_totals(user_id: str) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT date(timestamp) as day, SUM(amount) as total
            FROM coffee WHERE user_id = ?
            GROUP BY day
            ORDER BY day DESC
            LIMIT 30
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [{"day": row[0], "total": row[1]} for row in rows]

# AI: Main page route - displays the daily totals and the input form
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session_id: Optional[str] = Cookie(None)):
    session_user = await get_current_session_user(session_id)
    if not session_user:
        return RedirectResponse(url="/login", status_code=303)
    daily_totals = await get_daily_totals(session_user["id"])
    cups = await get_cups(session_user["id"])
    default_cup = await get_default_cup(session_user["id"])
    return templates.TemplateResponse("index.html", {
        "request": request,
        "daily_totals": daily_totals,
        "cups": cups,
        "default_cup": default_cup.id if default_cup else None,
        "username": session_user["username"],
        "is_admin": session_user["is_admin"]
    })

# AI: Handle form submission to add a new coffee entry
@app.post("/add", response_class=RedirectResponse)
async def add_coffee(cup_id: str = Form(...)):
    user = await get_current_user()
    async with aiosqlite.connect(DB_PATH) as db:
        # Get cup size
        cursor = await db.execute('SELECT size FROM cups WHERE id = ? AND user_id = ?', (cup_id, user.id))
        row = await cursor.fetchone()
        if not row:
            return RedirectResponse(url="/", status_code=303)
        amount = row[0]
        now = datetime.now().isoformat()
        entry_id = str(uuid.uuid4())
        await db.execute("INSERT INTO coffee (id, user_id, amount, cup_id, timestamp) VALUES (?, ?, ?, ?, ?)", (entry_id, user.id, amount, cup_id, now))
        await db.commit()
    return RedirectResponse(url="/", status_code=303)

# AI: Settings flyout page
@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request, session_id: Optional[str] = Cookie(None)):
    session_user = await get_current_session_user(session_id)
    if not session_user:
        return RedirectResponse(url="/login", status_code=303)
    cups = await get_cups(session_user["id"])
    users = await get_all_users() if session_user["is_admin"] else []
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "username": session_user["username"],
        "cups": cups,
        "is_admin": session_user["is_admin"],
        "users": users
    })

# AI: Update username
@app.post("/settings/username", response_class=RedirectResponse)
async def update_username(username: str = Form(...)):
    user = await get_current_user()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET username = ? WHERE id = ?', (username, user.id))
        await db.commit()
    return RedirectResponse(url="/settings", status_code=303)

# AI: Add a new cup
@app.post("/settings/cups", response_class=RedirectResponse)
async def add_cup(name: str = Form(...), size: float = Form(...)):
    user = await get_current_user()
    cup_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO cups (id, user_id, name, size) VALUES (?, ?, ?, ?)', (cup_id, user.id, name, size))
        await db.commit()
    return RedirectResponse(url="/settings", status_code=303)

# AI: Delete a cup by id for the current user
@app.post("/settings/cups/delete", response_class=RedirectResponse)
async def delete_cup(cup_id: str = Form(...)):
    user = await get_current_user()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM cups WHERE id = ? AND user_id = ?', (cup_id, user.id))
        await db.commit()
    return RedirectResponse(url="/settings", status_code=303)

# AI: Optional API endpoint to get all coffee entries as JSON using Pydantic
@app.get("/api/entries", response_model=List[CoffeeEntry])
async def api_entries():
    user = await get_current_user()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT user_id, amount, cup_id, timestamp FROM coffee WHERE user_id = ? ORDER BY timestamp DESC', (user.id,))
        rows = await cursor.fetchall()
        return [CoffeeEntry(user_id=row[0], amount=row[1], cup_id=row[2], timestamp=row[3]) for row in rows]

# AI: API endpoint to get all cups for the current user
@app.get("/api/cups", response_model=List[Cup])
async def api_cups():
    user = await get_current_user()
    return await get_cups(user.id)

@app.post("/settings/username/json")
async def update_username_json(username: str = Form(...)):
    user = await get_current_user()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET username = ? WHERE id = ?', (username, user.id))
        await db.commit()
    return {"success": True, "username": username}

# AI: Session management helpers
SESSION_COOKIE = "session_id"
sessions = {}

async def get_user_by_username(username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT id, username, password_hash, is_admin, must_change_password FROM users WHERE username = ?', (username,))
        row = await cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "password_hash": row[2],
                "is_admin": bool(row[3]),
                "must_change_password": bool(row[4])
            }
        return None

async def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

async def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

async def get_current_session_user(session_id: Optional[str] = Cookie(None)):
    user_id = sessions.get(session_id)
    if not user_id:
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT id, username, is_admin, must_change_password FROM users WHERE id = ?', (user_id,))
        row = await cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "is_admin": bool(row[2]),
                "must_change_password": bool(row[3])
            }
    return None

# AI: Login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    user = await get_user_by_username(username)
    if not user or not await verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    # Create session
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = user["id"]
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key=SESSION_COOKIE, value=session_id, httponly=True)
    # Force password change if required
    if user["must_change_password"]:
        response = RedirectResponse(url="/settings/password", status_code=303)
        response.set_cookie(key=SESSION_COOKIE, value=session_id, httponly=True)
    return response

@app.get("/logout")
async def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    if session_id in sessions:
        del sessions[session_id]
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT id, username, is_admin, must_change_password FROM users')
        rows = await cursor.fetchall()
        return [User(id=row[0], username=row[1], is_admin=bool(row[2]), must_change_password=bool(row[3])) for row in rows]

# AI: Password change page (forced after login)
@app.get("/settings/password", response_class=HTMLResponse)
async def password_change_page(request: Request, session_id: Optional[str] = Cookie(None)):
    session_user = await get_current_session_user(session_id)
    if not session_user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("password_change.html", {"request": request, "error": None})

@app.post("/settings/password", response_class=HTMLResponse)
async def password_change(request: Request, response: Response, new_password: str = Form(...), session_id: Optional[str] = Cookie(None)):
    session_user = await get_current_session_user(session_id)
    if not session_user:
        return RedirectResponse(url="/login", status_code=303)
    hashed = await hash_password(new_password)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?', (hashed, session_user["id"]))
        await db.commit()
    return RedirectResponse(url="/", status_code=303)

# AI: Helper to add default settings (e.g., standard cup) for a new user
async def add_default_settings_for_user(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Add a standard cup (200ml) for the new user
        cup_id = str(uuid.uuid4())
        await db.execute('INSERT INTO cups (id, user_id, name, size) VALUES (?, ?, ?, ?)', (cup_id, user_id, 'Standard Cup', 200))
        await db.commit()

# AI: Admin endpoint to add a new user
@app.post("/settings/users/add", response_class=RedirectResponse)
async def add_user(request: Request, username: str = Form(...), password: str = Form(...), is_admin: Optional[str] = Form(None), session_id: Optional[str] = Cookie(None)):
    session_user = await get_current_session_user(session_id)
    if not session_user or not session_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin only")
    user_id = str(uuid.uuid4())
    hashed = await hash_password(password)
    is_admin_flag = 1 if is_admin else 0
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('INSERT INTO users (id, username, password_hash, is_admin, must_change_password) VALUES (?, ?, ?, ?, 0)', (user_id, username, hashed, is_admin_flag))
            await db.commit()
        # Add default settings (e.g., standard cup) for the new user
        await add_default_settings_for_user(user_id)
    except aiosqlite.IntegrityError:
        return RedirectResponse(url="/settings?error=Username+already+exists", status_code=303)
    return RedirectResponse(url="/settings", status_code=303)

# AI: Admin endpoint to delete a user
@app.post("/settings/users/delete", response_class=RedirectResponse)
async def delete_user(request: Request, user_id: str = Form(...), session_id: Optional[str] = Cookie(None)):
    session_user = await get_current_session_user(session_id)
    if not session_user or not session_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin only")
    # Prevent deleting the last admin or self
    if user_id == session_user["id"]:
        return RedirectResponse(url="/settings?error=Cannot+delete+self", status_code=303)
    async with aiosqlite.connect(DB_PATH) as db:
        # Prevent deleting the last admin
        cursor = await db.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
        admin_count = (await cursor.fetchone())[0]
        cursor = await db.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        row = await cursor.fetchone()
        if row and row[0] == 1 and admin_count <= 1:
            return RedirectResponse(url="/settings?error=Cannot+delete+last+admin", status_code=303)
        await db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        await db.commit()
    return RedirectResponse(url="/settings", status_code=303)

@app.get("/api/users")
async def api_users(session_id: Optional[str] = Cookie(None)):
    session_user = await get_current_session_user(session_id)
    if not session_user or not session_user["is_admin"]:
        return {"users": []}
    users = await get_all_users()
    return {"users": [
        {"id": u.id, "username": u.username, "is_admin": u.is_admin} for u in users
    ]}
