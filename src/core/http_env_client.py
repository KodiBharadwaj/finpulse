"""
OpenEnv HTTP Client Base Class
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar
import requests


@dataclass
class StepResult:
    """Result from environment step"""
    observation: any
    reward: float
    done: bool
    metadata: dict = None


ActionType = TypeVar('ActionType')
ObservationType = TypeVar('ObservationType')


class HTTPEnvClient(ABC, Generic[ActionType, ObservationType]):
    """
    Base class for HTTP environment clients.

    Subclasses implement:
    - _step_payload(): Convert action to JSON
    - _parse_result(): Parse JSON to observation
    - _parse_state(): Parse JSON to state
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def reset(self) -> StepResult:
        """Reset environment via HTTP"""
        response = self.session.post(f"{self.base_url}/reset")
        response.raise_for_status()
        return self._parse_result(response.json())

    def step(self, action: ActionType) -> StepResult:
        """Execute action via HTTP"""
        payload = self._step_payload(action)
        response = self.session.post(f"{self.base_url}/step", json=payload)
        response.raise_for_status()
        return self._parse_result(response.json())

    def state(self):
        """Get current state via HTTP"""
        response = self.session.get(f"{self.base_url}/state")
        response.raise_for_status()
        return self._parse_state(response.json())

    def health(self) -> dict:
        """Check server health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    @abstractmethod
    def _step_payload(self, action: ActionType) -> dict:
        """Convert typed action to JSON dict"""
        pass

    @abstractmethod
    def _parse_result(self, payload: dict) -> StepResult:
        """Parse JSON response to typed StepResult"""
        pass

    @abstractmethod
    def _parse_state(self, payload: dict):
        """Parse JSON response to typed State"""
        pass
