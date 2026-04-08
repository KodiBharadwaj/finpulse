"""
OpenEnv Server Base Classes
Defines contracts for environment implementations
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, TypeVar, Union, Optional


@dataclass
class Action:
    """Base class for all actions"""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Observation:
    """Base class for all observations"""
    done: bool = False
    reward: Optional[Union[float, int, bool]] = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class State:
    """Base class for episode state/metadata"""
    episode_id: Optional[str]
    step_count: int


ObservationType = TypeVar('ObservationType', bound=Observation)
ActionType = TypeVar('ActionType', bound=Action)
StateType = TypeVar('StateType', bound=State)


class Environment(ABC, Generic[ActionType, ObservationType, StateType]):
    """
    Base class for all OpenEnv environments.
    Implement reset() and step() to create a new environment.
    """

    @abstractmethod
    def reset(self) -> ObservationType:
        """
        Reset environment to initial state.
        Returns first observation.
        """
        pass

    @abstractmethod
    def step(self, action: ActionType) -> ObservationType:
        """
        Execute action and return next observation.

        Args:
            action: Type-safe action to execute

        Returns:
            Next observation with reward and done flag
        """
        pass

    @property
    @abstractmethod
    def state(self) -> StateType:
        """
        Get current episode metadata.
        Returns state information like episode_id, step_count, etc.
        """
        pass


def create_fastapi_app(environment: Environment, static_dir: str = None):
    """
    Create FastAPI app with standard OpenEnv endpoints.

    Args:
        environment: Environment instance
        static_dir: Optional path to static files directory for web UI

    Returns:
        FastAPI app with /reset, /step, /state endpoints
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    from dataclasses import asdict
    import os

    app = FastAPI(title="FinPulse OpenEnv Server", version="1.0.0")

    # CORS for web clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files if directory provided
    if static_dir and os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/")
        def web_ui():
            """Serve web interface"""
            return FileResponse(os.path.join(static_dir, "index.html"))
    else:
        @app.get("/")
        def root():
            return {
                "service": "FinPulse OpenEnv Server",
                "version": "1.0.0",
                "endpoints": ["/reset", "/step", "/state", "/health"]
            }

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.post("/reset")
    def reset():
        """Reset environment and return initial observation"""
        try:
            obs = environment.reset()
            return asdict(obs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/step")
    def step(action_data: dict):
        """Execute action and return next observation"""
        try:
            # Reconstruct action from dict
            # Environment subclass should handle this
            obs = environment.step(action_data)
            return asdict(obs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/state")
    def get_state():
        """Get current episode state"""
        try:
            state = environment.state
            return asdict(state)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app
