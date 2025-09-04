// app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .deps.auth import get_current_user, User
from .routers import admin, students, sessions, homework, fees, qa

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Gambit Chess Club API"}

@app.get("/me")
def get_current_user_profile(user: User = Depends(get_current_user)):
    return user

app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(homework.router, prefix="/homework", tags=["Homework"])
app.include_router(fees.router, prefix="/fees", tags=["Fees"])
app.include_router(qa.router, prefix="/qa", tags=["Q&A"])

# Full router code for `admin.py`
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from ..config import settings
from ..deps.auth import get_admin_user, get_branch_coach_or_admin, User
from ..models.admin import UserCreate, UserUpdate
from pydantic import BaseModel
import random
import string

router = APIRouter()
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

def generate_temp_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

@router.post("/users", status_code=201)
def create_user(user_data: UserCreate, admin: User = Depends(get_admin_user)):
    try:
        temp_password = generate_temp_password()
        
        # Create auth user with Supabase service role key
        auth_response = supabase.auth.admin.create_user(
            email=user_data.email,
            password=temp_password,
        )
        user_id = auth_response.user.id

        # Insert into profiles table
        profile_response = supabase.from_('profiles').insert({
            "id": user_id,
            "email": user_data.email,
            "role": user_data.role,
            "branch_id": user_data.branch_id,
            "login_code": temp_password
        }).execute()

        # Handle other role-specific inserts (students, guardians, etc.)
        if user_data.role == 'student':
            supabase.from_('students').insert({
                "profile_id": user_id,
                "full_name": user_data.full_name,
                "branch_id": user_data.branch_id
            }).execute()
        
        # Similar logic for 'parent' and other roles
        
        return {"message": f"User {user_data.email} created successfully. Temporary password: {temp_password}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/users/{user_id}")
def update_user_role(user_id: str, user_update: UserUpdate, admin: User = Depends(get_admin_user)):
    try:
        supabase.from_('profiles').update(user_update.dict(exclude_unset=True)).eq("id", user_id).execute()
        return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))