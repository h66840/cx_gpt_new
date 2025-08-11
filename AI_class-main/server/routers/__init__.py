from fastapi import APIRouter
from server.routers.chat_router import chat
from server.routers.data_router import data
from server.routers.base_router import base
from server.routers.auth_router import auth
from server.routers.experiment_router import exp_router
from server.routers.lab_api_router import lab_api_router
from server.routers.dashboard_router import dashboard_router

# Import routers for visual reasoning
from server.routers.visual_graph import router as visual_graph_router
from server.routers.visual_workflow import router as visual_workflow_router
from server.routers.visual_sse import router as visual_sse_router
from server.routers.visual_router import router as new_visual_router # 導入我們的新路由

router = APIRouter()

# Existing routers
router.include_router(base)
router.include_router(chat)
router.include_router(data)
router.include_router(auth)
router.include_router(exp_router)
router.include_router(lab_api_router)
router.include_router(dashboard_router)

# Add new visual reasoning routers with a prefix
visual_router = APIRouter()
visual_router.include_router(visual_graph_router)
visual_router.include_router(visual_workflow_router)
visual_router.include_router(visual_sse_router)
visual_router.include_router(new_visual_router) # 將新路由添加到這個分組中

router.include_router(visual_router, prefix="/visual")
