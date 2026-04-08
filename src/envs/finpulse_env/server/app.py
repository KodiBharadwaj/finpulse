"""
FinPulse FastAPI Server
Exposes environment via HTTP endpoints with multi-task support
"""
import os
import sys
from typing import Dict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

# Add src to path (for local development)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.env_server import create_fastapi_app
from envs.finpulse_env.server.environment import FinPulseTradingEnvironment
from envs.finpulse_env.server.alpaca_service import create_alpaca_service
from envs.finpulse_env.server.tasks import TASKS, TaskGrader


# Initialize Alpaca service (if credentials available)
print("\n🔌 Initializing FinPulse Trading Environment...")
alpaca_service = create_alpaca_service()

# Create environment instances for each task (lazy initialization)
_environments: Dict[str, FinPulseTradingEnvironment] = {}
_current_task = os.getenv("FINPULSE_TASK", "balanced_trading")


def get_or_create_env(task: str = None) -> FinPulseTradingEnvironment:
    """Get or create environment for specified task"""
    task = task or _current_task

    if task not in _environments:
        print(f"Creating environment for task: {task}")
        _environments[task] = FinPulseTradingEnvironment(
            task=task,
            symbols=['AAPL', 'MSFT', 'GOOGL'],
            alpaca_service=alpaca_service
        )

    return _environments[task]


# Create default environment
env = get_or_create_env(_current_task)

# Get static directory path
static_dir = os.path.join(os.path.dirname(__file__), 'static')

# Create FastAPI app with standard OpenEnv endpoints and web UI
app = create_fastapi_app(env, static_dir=static_dir)


# Add custom endpoints for multi-task support
@app.post("/set_task")
def set_task(task: str):
    """Switch to a different task"""
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
    """List all available tasks"""
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
    """Grade an episode for a specific task"""
    if task not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task: {task}")

    try:
        result = TaskGrader.grade_task(task, metrics)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current_task")
def get_current_task():
    """Get current task configuration"""
    return {
        "task": env.task_name,
        "name": env.task_config.name,
        "difficulty": env.task_config.difficulty,
        "max_steps": env.max_steps,
        "success_threshold": env.task_config.success_threshold
    }


print("✅ FinPulse server ready!")
print(f"   Default task: {_current_task}")
print(f"   Available tasks: {list(TASKS.keys())}\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
