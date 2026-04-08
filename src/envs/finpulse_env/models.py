"""
FinPulse Type-Safe Models
Defines Action, Observation, and State for emotional trading
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from core.env_server import Action, Observation, State


@dataclass
class FinPulseAction(Action):
    """
    Trading action with emotional context

    Attributes:
        action_type: "buy", "sell", or "hold"
        symbol: Stock symbol (e.g., "AAPL", "MSFT")
        amount_pct: Percentage of portfolio to use (0.0-1.0)
        user_stress: User's current stress level (1-10)
        user_confidence: User's confidence level (1-10)
    """
    action_type: str = "hold"  # "buy", "sell", "hold"
    symbol: str = "AAPL"  # "AAPL", "MSFT", "GOOGL"
    amount_pct: float = 0.3  # 30% of portfolio by default
    user_stress: int = 5  # 1-10 scale
    user_confidence: int = 5  # 1-10 scale


@dataclass
class FinPulseObservation(Observation):
    """
    Observation from trading environment

    Attributes:
        prices: Current stock prices {symbol: price}
        portfolio_value: Total portfolio value
        cash_balance: Available cash
        positions: Current positions {symbol: shares}
        emotional_state: User's emotional metrics
        intervention: Whether action was blocked
        intervention_reason: Why action was blocked (if applicable)
    """
    # Market data
    prices: Dict[str, float] = field(default_factory=dict)

    # Portfolio data
    portfolio_value: float = 0.0
    cash_balance: float = 0.0
    positions: Dict[str, int] = field(default_factory=dict)

    # Emotional intelligence
    emotional_state: Dict[str, float] = field(default_factory=dict)

    # Intervention data
    intervention: bool = False
    intervention_reason: Optional[str] = None


@dataclass
class FinPulseState(State):
    """
    Episode metadata and configuration

    Attributes:
        episode_id: Unique episode identifier
        step_count: Number of steps in episode
        initial_balance: Starting cash
        current_balance: Current cash
        total_trades: Number of trades executed
        blocked_trades: Number of interventions
        symbols: Trading symbols
        emotional_history: Recent emotional states
    """
    episode_id: str
    step_count: int

    # Financial metrics
    initial_balance: float
    current_balance: float
    total_trades: int
    blocked_trades: int

    # Configuration
    symbols: List[str]

    # Emotional tracking
    emotional_history: List[Dict[str, float]] = field(default_factory=list)
