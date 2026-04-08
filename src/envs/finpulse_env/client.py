"""
FinPulse HTTP Client
Used by training code to connect to environment server
"""
from core.http_env_client import HTTPEnvClient, StepResult
from .models import FinPulseAction, FinPulseObservation, FinPulseState


class FinPulseTradingEnv(HTTPEnvClient[FinPulseAction, FinPulseObservation]):
    """
    HTTP client for FinPulse trading environment.

    Usage:
        env = FinPulseTradingEnv(base_url="http://localhost:8000")

        # Reset
        result = env.reset()
        print(result.observation.prices)

        # Step
        action = FinPulseAction(
            action_type="buy",
            symbol="AAPL",
            amount_pct=0.3,
            user_stress=5,
            user_confidence=7
        )
        result = env.step(action)

        if result.observation.intervention:
            print(f"Blocked: {result.observation.intervention_reason}")
        else:
            print(f"Executed! Reward: {result.reward}")
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        print(f"✅ FinPulse client connected to: {base_url}")

    def _step_payload(self, action: FinPulseAction) -> dict:
        """Convert typed action to JSON for HTTP"""
        return {
            'action_type': action.action_type,
            'symbol': action.symbol,
            'amount_pct': action.amount_pct,
            'user_stress': action.user_stress,
            'user_confidence': action.user_confidence,
            'metadata': action.metadata
        }

    def _parse_result(self, payload: dict) -> StepResult:
        """Parse HTTP JSON response to typed observation"""
        obs = FinPulseObservation(**payload)

        return StepResult(
            observation=obs,
            reward=obs.reward,
            done=obs.done,
            metadata=obs.metadata
        )

    def _parse_state(self, payload: dict) -> FinPulseState:
        """Parse state JSON to typed state"""
        return FinPulseState(**payload)
