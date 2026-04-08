"""
FinPulse FastAPI Server
Exposes environment via HTTP endpoints with multi-task support
"""
import os
import sys
from typing import Dict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.env_server import create_fastapi_app
from envs.finpulse_env.server.environment import FinPulseTradingEnvironment
from envs.finpulse_env.server.alpaca_service import create_alpaca_service
from envs.finpulse_env.server.tasks import TASKS, TaskGrader


# Lazy globals (IMPORTANT for multi-mode)
alpaca_service = None
_environments: Dict[str, FinPulseTradingEnvironment] = {}
_current_task = os.getenv("FINPULSE_TASK", "balanced_trading")
env = None


def get_or_create_env(task: str = None) -> FinPulseTradingEnvironment:
    global alpaca_service

    task = task or _current_task

    if alpaca_service is None:
        print("🔌 Initializing Alpaca service...")
        alpaca_service = create_alpaca_service()

    if task not in _environments:
        print(f"Creating environment for task: {task}")
        _environments[task] = FinPulseTradingEnvironment(
            task=task,
            symbols=['AAPL', 'MSFT', 'GOOGL'],
            alpaca_service=alpaca_service
        )

    return _environments[task]


def create_app_instance() -> FastAPI:
    global env

    env = get_or_create_env(_current_task)

    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    app = create_fastapi_app(env, static_dir=static_dir)

    # ---- Routes ----
    @app.post("/set_task")
    def set_task(task: str):
        global env
        if task not in TASKS:
            raise HTTPException(status_code=400, detail=f"Unknown task: {task}")

        env = get_or_create_env(task)
        return {
            "task": task,
            "name": TASKS[task].name,
            "difficulty": TASKS[task].difficulty,
            "max_steps": TASKS[task].max_steps,
            "success_threshold": TASKS[task].success_threshold
        }

    @app.get("/tasks")
    def list_tasks():
        return {
            task_id: {
                "name": config.name,
                "difficulty": config.difficulty,
                "max_steps": config.max_steps,
                "success_threshold": config.success_threshold,
                "description": config.description
            }
            for task_id, config in TASKS.items()
        }

    @app.post("/grade")
    def grade_episode(task: str, metrics: Dict):
        if task not in TASKS:
            raise HTTPException(status_code=400, detail=f"Unknown task: {task}")

        try:
            return TaskGrader.grade_task(task, metrics)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/current_task")
    def get_current_task():
        return {
            "task": env.task_name,
            "name": env.task_config.name,
            "difficulty": env.task_config.difficulty,
            "max_steps": env.max_steps,
            "success_threshold": env.task_config.success_threshold
        }

    return app


# REQUIRED: module-level app
app = create_app_instance()


# REQUIRED: callable main()
def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution.

    Args:
        host: Host address to bind to
        port: Port number
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)


# REQUIRED: simple entrypoint
if __name__ == "__main__":
    main()