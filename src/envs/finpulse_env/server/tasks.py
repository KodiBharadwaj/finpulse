"""
FinPulse Task Definitions and Graders
Implements 3 difficulty levels: Easy, Medium, Hard
"""
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TaskConfig:
    """Configuration for a trading task"""
    name: str
    difficulty: str
    max_steps: int
    initial_balance: float
    success_threshold: float  # Minimum return percentage for success
    description: str


# Task 1: Conservative Trading (Easy)
TASK_CONSERVATIVE = TaskConfig(
    name="conservative_trading",
    difficulty="easy",
    max_steps=30,
    initial_balance=10000.0,
    success_threshold=0.05,  # 5% return
    description="Achieve 5% return with emotional stability. Focus on risk management."
)

# Task 2: Balanced Trading (Medium)
TASK_BALANCED = TaskConfig(
    name="balanced_trading",
    difficulty="medium",
    max_steps=50,
    initial_balance=10000.0,
    success_threshold=0.15,  # 15% return
    description="Achieve 15% return while managing emotions. Balance risk and reward."
)

# Task 3: Aggressive Growth (Hard)
TASK_AGGRESSIVE = TaskConfig(
    name="aggressive_growth",
    difficulty="hard",
    max_steps=100,
    initial_balance=10000.0,
    success_threshold=0.30,  # 30% return
    description="Achieve 30% return with optimal risk-adjusted performance."
)

# All tasks
TASKS = {
    "conservative_trading": TASK_CONSERVATIVE,
    "balanced_trading": TASK_BALANCED,
    "aggressive_growth": TASK_AGGRESSIVE,
}


class TaskGrader:
    """Grades task performance with scores in [0.0, 1.0]"""

    @staticmethod
    def grade_conservative(
        portfolio_return: float,
        interventions: int,
        avg_stress: float,
        total_steps: int
    ) -> Dict[str, Any]:
        """
        Grade conservative trading task (Easy)

        Criteria:
        - Portfolio return (50%)
        - Low intervention count (25%)
        - Emotional stability (25%)
        """
        # Component 1: Portfolio return (target 5%)
        return_score = min(portfolio_return / 0.05, 1.0) if portfolio_return > 0 else 0.0
        return_score = max(0.0, return_score)

        # Component 2: Low interventions (penalize frequent blocks)
        intervention_rate = interventions / total_steps if total_steps > 0 else 0
        intervention_score = max(0.0, 1.0 - (intervention_rate * 5))  # Penalize >20% intervention rate

        # Component 3: Emotional stability (low average stress)
        stress_score = max(0.0, 1.0 - ((avg_stress - 5) / 5))  # Target stress <= 5

        # Weighted total
        total_score = (
            return_score * 0.5 +
            intervention_score * 0.25 +
            stress_score * 0.25
        )

        return {
            "score": round(total_score, 3),
            "components": {
                "return": round(return_score, 3),
                "interventions": round(intervention_score, 3),
                "emotional_stability": round(stress_score, 3)
            },
            "success": total_score >= 0.6  # 60% score = success
        }

    @staticmethod
    def grade_balanced(
        portfolio_return: float,
        interventions: int,
        volatility: float,
        total_steps: int
    ) -> Dict[str, Any]:
        """
        Grade balanced trading task (Medium)

        Criteria:
        - Portfolio return (60%)
        - Managed risk/volatility (30%)
        - Intervention avoidance (10%)
        """
        # Component 1: Portfolio return (target 15%)
        return_score = min(portfolio_return / 0.15, 1.0) if portfolio_return > 0 else 0.0
        return_score = max(0.0, return_score)

        # Component 2: Risk management (penalize high volatility)
        # Volatility typically 0.0-0.2, target < 0.1
        risk_score = max(0.0, 1.0 - (volatility * 5))

        # Component 3: Intervention avoidance
        intervention_rate = interventions / total_steps if total_steps > 0 else 0
        intervention_score = max(0.0, 1.0 - (intervention_rate * 10))

        # Weighted total
        total_score = (
            return_score * 0.6 +
            risk_score * 0.3 +
            intervention_score * 0.1
        )

        return {
            "score": round(total_score, 3),
            "components": {
                "return": round(return_score, 3),
                "risk_management": round(risk_score, 3),
                "interventions": round(intervention_score, 3)
            },
            "success": total_score >= 0.7  # 70% score = success
        }

    @staticmethod
    def grade_aggressive(
        portfolio_return: float,
        volatility: float,
        sharpe_ratio: float,
        total_steps: int
    ) -> Dict[str, Any]:
        """
        Grade aggressive growth task (Hard)

        Criteria:
        - High returns (50%)
        - Risk-adjusted performance / Sharpe ratio (40%)
        - Efficiency (10%)
        """
        # Component 1: Portfolio return (target 30%)
        return_score = min(portfolio_return / 0.30, 1.0) if portfolio_return > 0 else 0.0
        return_score = max(0.0, return_score)

        # Component 2: Sharpe ratio (risk-adjusted returns)
        # Sharpe typically -2 to +3, good = >1.0
        sharpe_normalized = min(sharpe_ratio / 2.0, 1.0) if sharpe_ratio > 0 else 0.0
        sharpe_score = max(0.0, sharpe_normalized)

        # Component 3: Efficiency (used steps well)
        # Penalize finishing too quickly (might not be optimized)
        step_efficiency = total_steps / 100.0  # Expect to use most of 100 steps
        efficiency_score = min(step_efficiency, 1.0)

        # Weighted total
        total_score = (
            return_score * 0.5 +
            sharpe_score * 0.4 +
            efficiency_score * 0.1
        )

        return {
            "score": round(total_score, 3),
            "components": {
                "return": round(return_score, 3),
                "sharpe_ratio": round(sharpe_score, 3),
                "efficiency": round(efficiency_score, 3)
            },
            "success": total_score >= 0.8  # 80% score = success
        }

    @staticmethod
    def grade_task(task_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate grader based on task"""
        if task_name == "conservative_trading":
            return TaskGrader.grade_conservative(
                portfolio_return=metrics["portfolio_return"],
                interventions=metrics["interventions"],
                avg_stress=metrics["avg_stress"],
                total_steps=metrics["total_steps"]
            )
        elif task_name == "balanced_trading":
            return TaskGrader.grade_balanced(
                portfolio_return=metrics["portfolio_return"],
                interventions=metrics["interventions"],
                volatility=metrics["volatility"],
                total_steps=metrics["total_steps"]
            )
        elif task_name == "aggressive_growth":
            return TaskGrader.grade_aggressive(
                portfolio_return=metrics["portfolio_return"],
                volatility=metrics["volatility"],
                sharpe_ratio=metrics["sharpe_ratio"],
                total_steps=metrics["total_steps"]
            )
        else:
            raise ValueError(f"Unknown task: {task_name}")
