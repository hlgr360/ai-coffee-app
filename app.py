from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import aiosqlite
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
import uuid

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

# AI: Helper to get current user (single user for now)
async def get_current_user():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT id, username FROM users LIMIT 1')
        row = await cursor.fetchone()
        if row:
            return User(id=row[0], username=row[1])
        return User(id="00000000-0000-0000-0000-000000000001", username="hlgr360")

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
async def index(request: Request):
    user = await get_current_user()
    daily_totals = await get_daily_totals(user.id)
    cups = await get_cups(user.id)
    default_cup = await get_default_cup(user.id)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "daily_totals": daily_totals,
        "cups": cups,
        "default_cup": default_cup.id if default_cup else None,
        "username": user.username
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
async def settings(request: Request):
    user = await get_current_user()
    cups = await get_cups(user.id)
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "username": user.username,
        "cups": cups
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
