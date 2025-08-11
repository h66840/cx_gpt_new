from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field # 引入 Field 以便对字段进行更细粒度的控制
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from server.db_manager import db_manager
from server.models.user_model import User, OperationLog
from server.utils.auth_utils import AuthUtils
from server.utils.auth_middleware import get_db, get_current_user, get_admin_user, get_superadmin_user, oauth2_scheme

# 创建路由器
auth = APIRouter(prefix="/auth", tags=["auth"])

# --- Pydantic 请求和响应模型 ---

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    organization: Optional[str] = None # 在Token响应中包含organization

class UserRegister(BaseModel):
    """
    用于用户注册的请求模型，包含用户名、密码和机构名称。
    普通用户注册时，机构名称是必填的。w
    """
    username: str
    password: str
    organization: str = Field(..., min_length=1, max_length=100, description="用户所在机构名称") # 明确为必填，并可添加长度限制

    class Config:
        schema_extra = {
            "example": {
                "username": "newuser",
                "password": "strongpassword123",
                "organization": "我的公司名称"
            }
        }

class UserCreate(BaseModel):
    """
    用于管理员创建用户的请求模型。
    管理员创建普通用户时，机构名称可根据需求设置。
    """
    username: str
    password: str
    role: str = "user"
    organization: Optional[str] = None # 管理员创建用户时，机构名称可以为可选

class UserUpdate(BaseModel):
    """
    用于更新用户信息的请求模型。
    """
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None # 更新用户时，可更新机构名称

class UserResponse(BaseModel):
    """
    用户信息的响应模型。
    """
    id: int
    username: str
    role: str
    organization: Optional[str] = None # 在用户信息响应中包含organization
    created_at: str
    last_login: Optional[str] = None

class InitializeAdmin(BaseModel):
    """
    用于系统初始化创建超级管理员的请求模型。
    超级管理员不强制要求填写机构名称。
    """
    username: str
    password: str

# --- 辅助函数：记录操作日志 ---
def log_operation(db: Session, user_id: int, operation: str, details: str = None, request: Request = None):
    ip_address = None
    if request:
        ip_address = request.headers.get("X-Forwarded-For") or request.client.host if request.client else None

    log = OperationLog(
        user_id=user_id,
        operation=operation,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
    db.refresh(log)

# --- 路由：登录获取令牌 ---
@auth.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = Request
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not AuthUtils.verify_password(user.password_hash, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)

    token_data = {"sub": str(user.id)}
    access_token = AuthUtils.create_access_token(token_data)

    log_operation(db, user.id, "登录", details=f"用户 {user.username} 成功登录", request=request)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "organization": user.organization
    }

# --- 路由：校验是否需要初始化管理员 ---
@auth.get("/check-first-run")
async def check_first_run():
    is_first_run = db_manager.check_first_run()
    return {"first_run": is_first_run}

# --- 路由：初始化管理员账户 ---
@auth.post("/initialize", response_model=Token)
async def initialize_admin(
    admin_data: InitializeAdmin,
    db: Session = Depends(get_db),
    request: Request = Request
):
    if not db_manager.check_first_run():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统已经初始化，无法再次创建初始管理员",
        )

    hashed_password = AuthUtils.hash_password(admin_data.password)

    new_admin = User(
        username=admin_data.username,
        password_hash=hashed_password,
        role="superadmin",
        organization=None, # 超级管理员不强制填写机构名称，这里设置为None
        last_login=datetime.now()
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    token_data = {"sub": str(new_admin.id)}
    access_token = AuthUtils.create_access_token(token_data)

    log_operation(db, new_admin.id, "系统初始化", "创建超级管理员账户", request)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_admin.id,
        "username": new_admin.username,
        "role": new_admin.role,
        "organization": new_admin.organization
    }

# --- 路由：用户注册 ---
@auth.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister, # 使用 UserRegister 模型，它强制要求 organization 字段
    db: Session = Depends(get_db),
    request: Request = Request
):
    """
    注册新用户到系统。
    注册用户默认角色为 'user'，并强制要求填写机构名称。
    """
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    hashed_password = AuthUtils.hash_password(user_data.password)

    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role="user", # 注册用户默认角色为 'user'
        organization=user_data.organization # 保存用户提供的机构名称
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_operation(
        db,
        new_user.id,
        "用户注册",
        f"新用户 '{new_user.username}' (机构: {new_user.organization}) 注册成功",
        request
    )

    return {"message": "用户注册成功，请登录！"}


# --- 路由：获取当前用户信息 ---
@auth.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()

# --- 路由：创建新用户（管理员权限） ---
@auth.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate, # 使用UserCreate模型
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    hashed_password = AuthUtils.hash_password(user_data.password)

    if user_data.role == "superadmin" and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员才能创建超级管理员账户",
        )

    if current_user.role == "admin" and user_data.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员只能创建普通用户账户",
        )

    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role,
        organization=user_data.organization # 保存机构名称
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_operation(
        db,
        current_user.id,
        "创建用户",
        f"创建用户: {user_data.username}, 角色: {user_data.role}, 机构: {user_data.organization or '无'}",
        request
    )

    return new_user.to_dict()

# --- 路由：获取所有用户（管理员权限） ---
@auth.get("/users", response_model=list[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [user.to_dict() for user in users]

# --- 路由：获取特定用户信息（管理员权限） ---
@auth.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user.to_dict()

# --- 路由：更新用户信息（管理员权限） ---
@auth.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if user.role == "superadmin" and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员才能修改超级管理员账户",
        )

    if user.role == "superadmin" and user_data.role and user_data.role != "superadmin" and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能降级超级管理员账户",
        )

    update_details = []

    if user_data.username is not None:
        existing_user = db.query(User).filter(User.username == user_data.username, User.id != user_id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )
        user.username = user_data.username
        update_details.append(f"用户名: {user_data.username}")

    if user_data.password is not None:
        user.password_hash = AuthUtils.hash_password(user_data.password)
        update_details.append("密码已更新")

    if user_data.role is not None:
        user.role = user_data.role
        update_details.append(f"角色: {user_data.role}")

    if user_data.organization is not None:
        user.organization = user_data.organization
        update_details.append(f"机构: {user_data.organization}")

    db.commit()
    db.refresh(user)

    log_operation(
        db,
        current_user.id,
        "更新用户",
        f"更新用户ID {user_id}: {', '.join(update_details)}",
        request
    )

    return user.to_dict()

# --- 路由：删除用户（管理员权限） ---
@auth.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if user.role == "superadmin":
        if current_user.role != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有超级管理员才能删除超级管理员账户",
            )

        superadmin_count = db.query(User).filter(User.role == "superadmin").count()
        if superadmin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除最后一个超级管理员账户",
            )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户",
        )

    log_operation(
        db,
        current_user.id,
        "删除用户",
        f"删除用户: {user.username}, ID: {user.id}, 角色: {user.role}, 机构: {user.organization or '无'}",
        request
    )

    db.delete(user)
    db.commit()

    return {"success": True, "message": "用户已删除"}