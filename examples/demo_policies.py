"""
Demo: Test different policies with FinPulse
Shows emotional intelligence in action
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from envs.finpulse_env import FinPulseTradingEnv
from envs.finpulse_env.models import FinPulseAction
import random


# ============================================================================
# POLICIES
# ============================================================================

class RandomPolicy:
    """Baseline: Random actions"""
    name = "🎲 Random Trader"

    def select_action(self, obs) -> FinPulseAction:
        return FinPulseAction(
            action_type=random.choice(['buy', 'sell', 'hold']),
            symbol=random.choice(['AAPL', 'MSFT', 'GOOGL']),
            amount_pct=0.3,
            user_stress=random.randint(1, 10),
            user_confidence=random.randint(1, 10)
        )


class PanicTrader:
    """Bad strategy: Always stressed, sells on dips"""
    name = "😰 Panic Trader"

    def select_action(self, obs) -> FinPulseAction:
        # Always stressed
        return FinPulseAction(
            action_type='sell',
            symbol='AAPL',
            amount_pct=0.5,
            user_stress=9,  # Very stressed!
            user_confidence=2
        )


class CalmTrader:
    """Good strategy: Calm, makes rational decisions"""
    name = "😎 Calm Trader"

    def select_action(self, obs) -> FinPulseAction:
        # Buy when calm
        return FinPulseAction(
            action_type='buy',
            symbol='AAPL',
            amount_pct=0.3,
            user_stress=3,  # Low stress
            user_confidence=8  # High confidence
        )


class LearningTrader:
    """Adapts stress based on portfolio performance"""
    name = "🧠 Learning Trader"

    def __init__(self):
        self.initial_value = None
        self.steps = 0

    def select_action(self, obs) -> FinPulseAction:
        self.steps += 1

        if self.initial_value is None:
            self.initial_value = obs.portfolio_value

        # Calculate stress based on performance
        performance = (obs.portfolio_value - self.initial_value) / self.initial_value

        if performance < -0.05:  # Losing money
            stress = 8
            confidence = 3
            action_type = 'hold'  # Don't panic sell!
        elif performance > 0.05:  # Making money
            stress = 2
            confidence = 9
            action_type = 'buy'  # Invest more
        else:
            stress = 5
            confidence = 6
            action_type = 'hold'

        return FinPulseAction(
            action_type=action_type,
            symbol='AAPL',
            amount_pct=0.3,
            user_stress=stress,
            user_confidence=confidence
        )


# ============================================================================
# EVALUATION
# ============================================================================

def run_episode(env: FinPulseTradingEnv, policy, max_steps=20, verbose=True):
    """Run one episode with a policy"""
    result = env.reset()

    total_reward = 0
    interventions = 0

    if verbose:
        print(f"\n{'='*70}")
        print(f"   Testing: {policy.name}")
        print(f"{'='*70}\n")

    for step in range(max_steps):
        obs = result.observation

        # Policy selects action
        action = policy.select_action(obs)

        # Execute
        result = env.step(action)

        total_reward += result.reward

        if verbose:
            if result.observation.intervention:
                interventions += 1
                print(f"Step {step+1}: 🛡️  BLOCKED - {result.observation.intervention_reason[:80]}...")
            else:
                print(f"Step {step+1}: ✅ {action.action_type.upper()} {action.symbol} | "
                      f"Portfolio: ${result.observation.portfolio_value:,.2f} | "
                      f"Reward: {result.reward:+.1f}")

        if result.done:
            break

    if verbose:
        print(f"\n{'─'*70}")
        print(f"Episode Summary:")
        print(f"  Total Reward: {total_reward:.2f}")
        print(f"  Interventions: {interventions}")
        print(f"  Final Portfolio: ${result.observation.portfolio_value:,.2f}")
        print(f"{'─'*70}\n")

    return {
        'reward': total_reward,
        'interventions': interventions,
        'final_value': result.observation.portfolio_value
    }


def compare_policies(env: FinPulseTradingEnv, num_episodes=5):
    """Compare all policies"""
    policies = [
        RandomPolicy(),
        PanicTrader(),
        CalmTrader(),
        LearningTrader()
    ]

    print("\n" + "="*70)
    print("   🏆 POLICY COMPARISON")
    print("="*70 + "\n")

    results = []

    for policy in policies:
        print(f"\n📊 Testing {policy.name} over {num_episodes} episodes...")

        episode_results = [
            run_episode(env, policy, max_steps=20, verbose=False)
            for _ in range(num_episodes)
        ]

        avg_reward = sum(r['reward'] for r in episode_results) / num_episodes
        avg_interventions = sum(r['interventions'] for r in episode_results) / num_episodes
        avg_value = sum(r['final_value'] for r in episode_results) / num_episodes

        results.append({
            'name': policy.name,
            'reward': avg_reward,
            'interventions': avg_interventions,
            'value': avg_value
        })

    # Display results
    print("\n" + "="*70)
    print("   📈 RESULTS")
    print("="*70 + "\n")

    results.sort(key=lambda x: x['reward'], reverse=True)

    for i, r in enumerate(results, 1):
        medal = ["🥇", "🥈", "🥉", "  "][min(i-1, 3)]
        print(f"{medal} {r['name']:25s} | "
              f"Reward: {r['reward']:+7.1f} | "
              f"Interventions: {r['interventions']:4.1f} | "
              f"Final: ${r['value']:,.0f}")

    print("\n" + "="*70)
    print("\n💡 Key Insights:")
    print("   • Panic Trader gets blocked the most (emotional protection)")
    print("   • Calm Trader performs well (rational decisions)")
    print("   • Learning Trader adapts stress to performance")
    print("   • FinPulse prevents costly emotional mistakes!\n")


def main():
    """Main demo"""
    print("\n🫀 " + "="*66 + " 🫀")
    print("   FINPULSE: AI Wealth Manager with Emotional Intelligence")
    print("🫀 " + "="*66 + " 🫀\n")

    # Connect to server
    print("🔌 Connecting to FinPulse environment server...")
    env = FinPulseTradingEnv(base_url="http://localhost:8000")

    try:
        # Test connection
        health = env.health()
        print(f"✅ Server healthy: {health}\n")

        # Run single episode with each policy
        print("\n" + "="*70)
        print("   PART 1: Individual Policy Demonstrations")
        print("="*70)

        policies = [PanicTrader(), CalmTrader(), LearningTrader()]
        for policy in policies:
            run_episode(env, policy, max_steps=10, verbose=True)

        # Compare policies
        print("\n" + "="*70)
        print("   PART 2: Statistical Comparison")
        print("="*70)

        compare_policies(env, num_episodes=5)

        print("\n✨ Demo complete! FinPulse protected you from emotional trading.\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure the FinPulse server is running:")
        print("   cd src/envs/finpulse_env/server")
        print("   python app.py\n")


if __name__ == '__main__':
    main()
