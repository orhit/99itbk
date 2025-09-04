// app/deps/auth.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from pydantic import BaseModel
import jwt

supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
oauth2_scheme = HTTPBearer()

class User(BaseModel):
    id: str
    email: str
    role: str
    branch_id: str | None = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(oauth2_scheme)):
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Use the service role key to get the user's role and branch
        user_data = supabase.from_('profiles').select('id, email, role, branch_id').eq('id', user_id).single().execute()
        if not user_data.data:
            raise HTTPException(status_code=404, detail="User not found")

        return User(**user_data.data)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def get_admin_user(user: User = Security(get_current_user)):
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not an admin")
    return user

def get_branch_coach_or_admin(user: User = Security(get_current_user)):
    if user.role not in ['admin', 'branch_coach']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return user