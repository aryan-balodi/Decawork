"""FastAPI IT Admin Panel — Main Application."""

import os
import secrets
import string
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import init_db, seed_db, get_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    await seed_db()
    yield


app = FastAPI(title="IT Admin Panel", lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def generate_temp_password(length=12):
    """Generate a random temporary password."""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))


# ============================================================
# Dashboard
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = await get_db()
    try:
        # Get stats
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
        active_users = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM license_assignments")
        total_assignments = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM licenses")
        total_licenses = (await cursor.fetchone())[0]

        # Recent activity
        cursor = await db.execute(
            "SELECT * FROM activity_log ORDER BY id DESC LIMIT 10"
        )
        activities = await cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "total_users": total_users,
                "active_users": active_users,
                "total_assignments": total_assignments,
                "total_licenses": total_licenses,
                "activities": activities,
                "page": "dashboard",
            },
        )
    finally:
        await db.close()


# ============================================================
# User Management
# ============================================================

@app.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, search: str = ""):
    db = await get_db()
    try:
        if search:
            cursor = await db.execute(
                "SELECT * FROM users WHERE name LIKE ? OR email LIKE ? ORDER BY id",
                (f"%{search}%", f"%{search}%"),
            )
        else:
            cursor = await db.execute("SELECT * FROM users ORDER BY id")
        users = await cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="users.html",
            context={
                "users": users,
                "search": search,
                "page": "users",
            },
        )
    finally:
        await db.close()


@app.get("/users/create", response_class=HTMLResponse)
async def create_user_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user_create.html",
        context={"page": "users"},
    )


@app.post("/users/create")
async def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form("employee"),
    department: str = Form("General"),
):
    db = await get_db()
    try:
        now = datetime.now().isoformat()
        await db.execute(
            "INSERT INTO users (name, email, role, department, status, created_at, password_reset_required) VALUES (?, ?, ?, ?, 'active', ?, 0)",
            (name, email, role, department, now),
        )
        await db.execute(
            "INSERT INTO activity_log (action, details, timestamp) VALUES (?, ?, ?)",
            ("User Created", f"Created user {email}", now),
        )
        await db.commit()
        return RedirectResponse(url="/users", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="user_create.html",
            context={
                "page": "users",
                "error": f"Error creating user: {str(e)}",
            },
        )
    finally:
        await db.close()


@app.get("/users/{user_id}", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user's license assignments
        cursor = await db.execute("""
            SELECT l.software, l.icon, la.assigned_at
            FROM license_assignments la
            JOIN licenses l ON la.license_id = l.id
            WHERE la.user_id = ?
        """, (user_id,))
        user_licenses = await cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="user_detail.html",
            context={
                "user": user,
                "user_licenses": user_licenses,
                "page": "users",
            },
        )
    finally:
        await db.close()


@app.post("/users/{user_id}/reset-password")
async def reset_password(user_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        temp_pass = generate_temp_password()
        now = datetime.now().isoformat()

        await db.execute(
            "UPDATE users SET password_reset_required = 1, temp_password = ? WHERE id = ?",
            (temp_pass, user_id),
        )
        await db.execute(
            "INSERT INTO activity_log (action, details, timestamp) VALUES (?, ?, ?)",
            ("Password Reset", f"Reset password for {user['email']} — temp: {temp_pass}", now),
        )
        await db.commit()
        return RedirectResponse(url=f"/users/{user_id}?reset=success&temp_pass={temp_pass}", status_code=303)
    finally:
        await db.close()


@app.post("/users/{user_id}/toggle-status")
async def toggle_status(user_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_status = "disabled" if user["status"] == "active" else "active"
        now = datetime.now().isoformat()

        await db.execute(
            "UPDATE users SET status = ? WHERE id = ?",
            (new_status, user_id),
        )
        action = "Account Disabled" if new_status == "disabled" else "Account Enabled"
        await db.execute(
            "INSERT INTO activity_log (action, details, timestamp) VALUES (?, ?, ?)",
            (action, f"{action.split()[1]} account for {user['email']}", now),
        )
        await db.commit()
        return RedirectResponse(url=f"/users/{user_id}", status_code=303)
    finally:
        await db.close()


@app.post("/users/{user_id}/delete")
async def delete_user(user_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        now = datetime.now().isoformat()

        # Remove license assignments first
        await db.execute("DELETE FROM license_assignments WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.execute(
            "INSERT INTO activity_log (action, details, timestamp) VALUES (?, ?, ?)",
            ("User Deleted", f"Deleted user {user['email']}", now),
        )
        await db.commit()
        return RedirectResponse(url="/users", status_code=303)
    finally:
        await db.close()


# ============================================================
# License Management
# ============================================================

@app.get("/licenses", response_class=HTMLResponse)
async def list_licenses(request: Request):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM licenses ORDER BY id")
        licenses = await cursor.fetchall()

        # Get assignment counts and details for each license
        license_data = []
        for lic in licenses:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM license_assignments WHERE license_id = ?",
                (lic["id"],),
            )
            used = (await cursor.fetchone())[0]

            cursor = await db.execute("""
                SELECT u.name, u.email, la.assigned_at
                FROM license_assignments la
                JOIN users u ON la.user_id = u.id
                WHERE la.license_id = ?
            """, (lic["id"],))
            assigned_users = await cursor.fetchall()

            license_data.append({
                "id": lic["id"],
                "software": lic["software"],
                "icon": lic["icon"],
                "total_seats": lic["total_seats"],
                "used_seats": used,
                "available_seats": lic["total_seats"] - used,
                "assigned_users": assigned_users,
            })

        # Get all active users for the assign dropdown
        cursor = await db.execute("SELECT id, name, email FROM users WHERE status = 'active' ORDER BY name")
        all_users = await cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="licenses.html",
            context={
                "licenses": license_data,
                "all_users": all_users,
                "page": "licenses",
            },
        )
    finally:
        await db.close()


@app.post("/licenses/{license_id}/assign")
async def assign_license(license_id: int, user_id: int = Form(...)):
    db = await get_db()
    try:
        # Check license exists and has seats
        cursor = await db.execute("SELECT * FROM licenses WHERE id = ?", (license_id,))
        lic = await cursor.fetchone()
        if not lic:
            raise HTTPException(status_code=404, detail="License not found")

        cursor = await db.execute(
            "SELECT COUNT(*) FROM license_assignments WHERE license_id = ?",
            (license_id,),
        )
        used = (await cursor.fetchone())[0]
        if used >= lic["total_seats"]:
            raise HTTPException(status_code=400, detail="No seats available")

        # Check user exists
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        now = datetime.now().isoformat()
        try:
            await db.execute(
                "INSERT INTO license_assignments (license_id, user_id, assigned_at) VALUES (?, ?, ?)",
                (license_id, user_id, now),
            )
        except Exception:
            raise HTTPException(status_code=400, detail="License already assigned to this user")

        await db.execute(
            "INSERT INTO activity_log (action, details, timestamp) VALUES (?, ?, ?)",
            ("License Assigned", f"Assigned {lic['software']} to {user['email']}", now),
        )
        await db.commit()
        return RedirectResponse(url="/licenses", status_code=303)
    finally:
        await db.close()


@app.post("/licenses/{license_id}/revoke/{user_id}")
async def revoke_license(license_id: int, user_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM licenses WHERE id = ?", (license_id,))
        lic = await cursor.fetchone()
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()

        await db.execute(
            "DELETE FROM license_assignments WHERE license_id = ? AND user_id = ?",
            (license_id, user_id),
        )

        now = datetime.now().isoformat()
        if lic and user:
            await db.execute(
                "INSERT INTO activity_log (action, details, timestamp) VALUES (?, ?, ?)",
                ("License Revoked", f"Revoked {lic['software']} from {user['email']}", now),
            )
        await db.commit()
        return RedirectResponse(url="/licenses", status_code=303)
    finally:
        await db.close()
