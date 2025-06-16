from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.templating import Jinja2Templates
from services.supabase_client import supabase

router = APIRouter()
templates = Jinja2Templates(directory="template")

@router.get("/dashboard",  response_model=None)
async def show_dashboard(request: Request, role: str = Query("admin"), user_id: int = Query(None)):

    # 1. Admin: Get all metrics
    if role == "admin":
        perf_data = supabase.table("performance_metrics").select("*").execute()
        log_data = supabase.table("network_logs").select("*").execute()

        if not perf_data.data:
            raise HTTPException(status_code=404, detail="No performance data found")
        
        metrics = perf_data.data
        alerts = [{"node_id": log["node_id"], "message": log["event_type"]} for log in log_data.data]

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "metrics": metrics,
            "alerts": alerts,
            "usage": {},  # admin doesn't need personal usage
            "role": role
        })

    # 2. Regular user: Get metrics from node they're connected to
    elif role == "user":
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID required for user view")

        user_data = supabase.table("user_accounts").select("node_id").eq("user_id", user_id).execute()

        if not user_data.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        node_id = user_data.data[0]["node_id"]

        perf = supabase.table("performance_metrics").select("*").eq("node_id", node_id).limit(1).execute()

        if not perf.data:
            raise HTTPException(status_code=404, detail="No metrics for your node")

        usage = {
            "data_usage": perf.data[0]["data_usage"],
            "latency": perf.data[0]["latency"]
        }

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "metrics": [],  # not needed for user
            "alerts": [],
            "usage": usage,
            "role": role
        })

    else:
        raise HTTPException(status_code=400, detail="Invalid role provided")
