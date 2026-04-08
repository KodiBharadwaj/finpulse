"""
FinPulse Trading Environment Implementation
Server-side logic with emotional intelligence
"""
import uuid
import numpy as np
from typing import Dict, List, Optional
from core.env_server import Environment
from envs.finpulse_env.models import FinPulseAction, FinPulseObservation, FinPulseState
from envs.finpulse_env.server.alpaca_service import AlpacaMarketDataService
from envs.finpulse_env.server.tasks import TASKS, TaskConfig


class FinPulseTradingEnvironment(Environment[FinPulseAction, FinPulseObservation, FinPulseState]):
    """
    Trading environment with emotional intelligence intervention.

    Features:
    - Real/simulated stock prices
    - Emotional state tracking
    - Panic selling prevention
    - Overtrading detection
    - FOMO buying prevention
    """

    def __init__(
        self,
        task: str = "balanced_trading",
        symbols: List[str] = None,
        alpaca_service: Optional[AlpacaMarketDataService] = None
    ):
        # Load task configuration
        if task not in TASKS:
            raise ValueError(f"Unknown task: {task}. Available: {list(TASKS.keys())}")

        self.task_config = TASKS[task]
        self.task_name = task
        self.initial_balance = self.task_config.initial_balance
        self.max_steps = self.task_config.max_steps
        self.symbols = symbols or ['AAPL', 'MSFT', 'GOOGL']
        self.alpaca_service = alpaca_service

        # Episode state
        self._episode_id = None
        self._step_count = 0
        self._balance = self.initial_balance
        self._positions = {symbol: 0 for symbol in self.symbols}
        self._prices = {}
        self._price_history = []
        self._emotional_history = []
        self._trade_history = []
        self._portfolio_value_history = []  # Track portfolio values for volatility calculation
        self._interventions_count = 0  # Track intervention count for grading

        # Log task info
        print(f"🎯 Task: {self.task_config.name} ({self.task_config.difficulty.upper()})")
        print(f"   Target: {self.task_config.success_threshold*100:.0f}% return in {self.max_steps} steps")

        # Log data source
        if self.alpaca_service:
            print("📊 Using REAL market data from Alpaca Paper Trading API")
        else:
            print("🎲 Using SIMULATED market data (random walk)")

        # Initialize
        self._init_prices()

    def _init_prices(self):
        """Initialize stock prices"""
        if self.alpaca_service:
            # Fetch real prices from Alpaca
            try:
                self._prices = self.alpaca_service.get_latest_prices(self.symbols)
                print(f"💰 Real prices loaded: {self._prices}")
            except Exception as e:
                print(f"⚠️ Failed to fetch Alpaca prices, using fallback: {e}")
                self._prices = {
                    'AAPL': 180.0,
                    'MSFT': 380.0,
                    'GOOGL': 140.0
                }
        else:
            # Use simulated prices
            self._prices = {
                'AAPL': 180.0,
                'MSFT': 380.0,
                'GOOGL': 140.0
            }
        self._price_history = [self._prices.copy()]

    def reset(self) -> FinPulseObservation:
        """Reset environment to initial state"""
        self._episode_id = str(uuid.uuid4())[:8]
        self._step_count = 0
        self._balance = self.initial_balance
        self._positions = {symbol: 0 for symbol in self.symbols}
        self._emotional_history = []
        self._trade_history = []
        self._portfolio_value_history = [self.initial_balance]
        self._interventions_count = 0  # Reset intervention counter

        self._init_prices()

        return self._build_observation(
            intervention=False,
            reward=0.0,
            done=False
        )

    def step(self, action_data: dict) -> FinPulseObservation:
        """
        Execute action with emotional intelligence check

        Args:
            action_data: Dict with action fields

        Returns:
            Observation with intervention info if blocked
        """
        # Parse action
        action = FinPulseAction(**action_data)

        # Track emotional state
        self._emotional_history.append({
            'stress': action.user_stress,
            'confidence': action.user_confidence,
            'step': self._step_count
        })

        # Check for emotional intervention
        intervention_result = self._check_intervention(action)

        if intervention_result['should_block']:
            # BLOCKED - Small penalty for needing intervention (agent made a mistake)
            # Don't reward being blocked - it's a safety net, not a goal
            self._interventions_count += 1  # Track for grading
            reward = self._calculate_reward(action, blocked=True)
            self._step_count += 1

            # Update portfolio value history even when blocked
            current_value = self._get_portfolio_value()
            self._portfolio_value_history.append(current_value)

            return self._build_observation(
                intervention=True,
                intervention_reason=intervention_result['reason'],
                reward=reward,
                done=False
            )

        # Execute trade
        trade_result = self._execute_trade(action)

        # Update prices
        self._update_prices()
        self._step_count += 1

        # Calculate reward (portfolio performance + emotional penalties)
        reward = self._calculate_reward(action, blocked=False)

        # Track portfolio value for risk calculation
        current_value = self._get_portfolio_value()
        self._portfolio_value_history.append(current_value)

        # Check if episode done
        done = self._step_count >= self.max_steps

        return self._build_observation(
            intervention=False,
            reward=reward,
            done=done
        )

    def _check_intervention(self, action: FinPulseAction) -> dict:
        """
        Check if action should be blocked due to emotional state

        Returns:
            Dict with 'should_block' and 'reason'
        """
        # Get recent emotional state
        recent_stress = self._get_avg_recent_stress()

        # Rule 1: Panic Selling
        if action.user_stress > 7 and action.action_type == 'sell':
            return {
                'should_block': True,
                'reason': f"🚨 Panic Selling Alert: Stress={action.user_stress}/10. "
                         f"Research shows 85% of panic sells are regretted. "
                         f"FinPulse recommends waiting 24 hours."
            }

        # Rule 2: Overtrading
        recent_trades = len([t for t in self._trade_history if self._step_count - t['step'] < 10])
        if recent_trades > 5:
            return {
                'should_block': True,
                'reason': f"⚠️ Overtrading Alert: {recent_trades} trades in 10 steps. "
                         f"Taking mandatory cooldown."
            }

        # Rule 3: FOMO Buying
        if action.user_confidence < 4 and action.action_type == 'buy':
            # Check if price recently surged
            if len(self._price_history) > 5:
                symbol = action.symbol
                recent_change = (self._prices[symbol] - self._price_history[-5][symbol]) / self._price_history[-5][symbol]
                if recent_change > 0.05:  # 5% surge
                    return {
                        'should_block': True,
                        'reason': f"💡 FOMO Check: {symbol} up {recent_change*100:.1f}% "
                                 f"and confidence={action.user_confidence}/10. "
                                 f"This might be FOMO. Wait 1 hour."
                    }

        return {'should_block': False, 'reason': None}

    def _execute_trade(self, action: FinPulseAction) -> dict:
        """Execute the trade action"""
        result = {'executed': False}

        if action.action_type == 'hold':
            return result

        symbol = action.symbol
        price = self._prices[symbol]

        if action.action_type == 'buy':
            # Calculate shares to buy
            amount = self._balance * action.amount_pct
            shares = int(amount / price)

            if shares > 0 and self._balance >= shares * price:
                cost = shares * price
                self._balance -= cost
                self._positions[symbol] += shares

                self._trade_history.append({
                    'step': self._step_count,
                    'type': 'buy',
                    'symbol': symbol,
                    'shares': shares,
                    'price': price
                })

                result = {'executed': True}

        elif action.action_type == 'sell':
            shares = self._positions[symbol]

            if shares > 0:
                proceeds = shares * price
                self._balance += proceeds
                self._positions[symbol] = 0

                self._trade_history.append({
                    'step': self._step_count,
                    'type': 'sell',
                    'symbol': symbol,
                    'shares': shares,
                    'price': price
                })

                result = {'executed': True}

        return result

    def _update_prices(self):
        """Update stock prices (real or simulated)"""
        if self.alpaca_service:
            # Fetch latest real prices
            try:
                self._prices = self.alpaca_service.get_latest_prices(self.symbols)
            except Exception as e:
                print(f"⚠️ Failed to update prices from Alpaca: {e}")
                # Keep previous prices if fetch fails
        else:
            # Simulated random walk
            new_prices = {}
            for symbol in self.symbols:
                # Random walk with 2% volatility
                change = np.random.randn() * 0.02
                new_prices[symbol] = self._prices[symbol] * (1 + change)
            self._prices = new_prices

        self._price_history.append(self._prices.copy())

    def _calculate_return(self) -> float:
        """Calculate portfolio return"""
        portfolio_value = self._get_portfolio_value()
        return (portfolio_value - self.initial_balance) / self.initial_balance

    def _calculate_reward(self, action: FinPulseAction, blocked: bool) -> float:
        """
        Calculate reward with improved logic:
        - Portfolio performance (smoothed over window)
        - Risk-adjusted returns (Sharpe-like)
        - Emotional stability penalty
        - Small penalty for interventions (not reward)
        """

        # Component 1: Smoothed portfolio returns (reduces short-term noise)
        window = min(10, len(self._portfolio_value_history))
        if window > 1:
            # Calculate return over the window
            recent_values = self._portfolio_value_history[-window:]
            smoothed_return = (recent_values[-1] - recent_values[0]) / recent_values[0]
        else:
            smoothed_return = 0.0

        # Scale to reasonable range (-10 to +10 for ±10% return)
        portfolio_reward = smoothed_return * 100

        # Component 2: Risk-adjusted returns (Sharpe-like ratio)
        # Penalize high volatility strategies
        if len(self._portfolio_value_history) >= 5:
            recent_values = self._portfolio_value_history[-10:]
            returns = [
                (recent_values[i] - recent_values[i-1]) / recent_values[i-1]
                for i in range(1, len(recent_values))
            ]
            volatility = np.std(returns) if len(returns) > 1 else 0.01

            # Penalize high volatility (risk adjustment)
            risk_penalty = -volatility * 50  # High volatility = negative reward
        else:
            risk_penalty = 0.0

        # Component 3: Emotional stability penalty
        # Penalize high stress and low confidence (agent should learn to manage emotions)
        stress_penalty = -max(0, action.user_stress - 5) * 0.5  # Cost for stress > 5
        confidence_penalty = -max(0, 5 - action.user_confidence) * 0.3  # Cost for confidence < 5

        emotional_penalty = stress_penalty + confidence_penalty

        # Component 4: Intervention penalty (small - it's a mistake, not a reward)
        if blocked:
            intervention_penalty = -2.0  # Small penalty for needing to be saved
        else:
            intervention_penalty = 0.0

        # Total reward
        total_reward = (
            portfolio_reward +      # Main component: portfolio growth
            risk_penalty +          # Penalize excessive volatility
            emotional_penalty +     # Penalize emotional instability
            intervention_penalty    # Small penalty for being blocked
        )

        return total_reward

    def _get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        return self._balance + sum(
            self._positions[s] * self._prices[s]
            for s in self.symbols
        )

    def _get_avg_recent_stress(self, window: int = 5) -> float:
        """Get average stress over recent steps"""
        if not self._emotional_history:
            return 5.0

        recent = self._emotional_history[-window:]
        return sum(h['stress'] for h in recent) / len(recent)

    def _build_observation(
        self,
        intervention: bool,
        reward: float,
        done: bool,
        intervention_reason: str = None
    ) -> FinPulseObservation:
        """Build typed observation"""

        # Get current emotional state
        if self._emotional_history:
            latest = self._emotional_history[-1]
            emotional_state = {
                'stress': latest['stress'],
                'confidence': latest['confidence'],
                'mood': 10 - latest['stress'],  # Inverse of stress
                'energy': latest['confidence']
            }
        else:
            emotional_state = {
                'stress': 5.0,
                'confidence': 5.0,
                'mood': 5.0,
                'energy': 5.0
            }

        return FinPulseObservation(
            prices=self._prices.copy(),
            portfolio_value=self._get_portfolio_value(),
            cash_balance=self._balance,
            positions=self._positions.copy(),
            emotional_state=emotional_state,
            intervention=intervention,
            intervention_reason=intervention_reason,
            done=done,
            reward=reward,
            metadata={
                'step': self._step_count,
                'trades': len(self._trade_history)
            }
        )

    @property
    def state(self) -> FinPulseState:
        """Get current episode state"""
        return FinPulseState(
            episode_id=self._episode_id or "none",
            step_count=self._step_count,
            initial_balance=self.initial_balance,
            current_balance=self._balance,
            total_trades=len(self._trade_history),
            blocked_trades=self._interventions_count,
            symbols=self.symbols,
            emotional_history=self._emotional_history.copy()
        )

    def get_grading_metrics(self) -> Dict[str, float]:
        """
        Get metrics for task grading

        Returns dict with:
        - portfolio_return: Final return percentage
        - interventions: Number of blocked actions
        - avg_stress: Average stress level
        - volatility: Portfolio volatility
        - sharpe_ratio: Risk-adjusted return
        - total_steps: Steps taken
        """
        final_value = self._get_portfolio_value()
        portfolio_return = (final_value - self.initial_balance) / self.initial_balance

        # Calculate average stress
        if self._emotional_history:
            avg_stress = sum(h['stress'] for h in self._emotional_history) / len(self._emotional_history)
        else:
            avg_stress = 5.0

        # Calculate portfolio volatility
        if len(self._portfolio_value_history) > 1:
            returns = [
                (self._portfolio_value_history[i] - self._portfolio_value_history[i-1]) / self._portfolio_value_history[i-1]
                for i in range(1, len(self._portfolio_value_history))
            ]
            volatility = float(np.std(returns)) if returns else 0.0
        else:
            volatility = 0.0

        # Calculate Sharpe ratio (simplified, assuming risk-free rate = 0)
        if volatility > 0 and self._step_count > 0:
            avg_return = portfolio_return / self._step_count
            sharpe_ratio = avg_return / volatility
        else:
            sharpe_ratio = 0.0

        return {
            "portfolio_return": portfolio_return,
            "interventions": self._interventions_count,
            "avg_stress": avg_stress,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "total_steps": self._step_count
        }
