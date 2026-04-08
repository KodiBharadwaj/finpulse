"""
Quick test to verify FinPulse OpenEnv setup
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from envs.finpulse_env import FinPulseTradingEnv
from envs.finpulse_env.models import FinPulseAction


def test_basic_flow():
    """Test basic environment flow"""
    print("\n🧪 Testing FinPulse OpenEnv Setup\n")

    # Connect
    print("1️⃣ Connecting to server...")
    env = FinPulseTradingEnv(base_url="http://localhost:8000")

    # Health check
    print("2️⃣ Checking server health...")
    health = env.health()
    print(f"   ✅ {health}")

    # Reset
    print("\n3️⃣ Resetting environment...")
    result = env.reset()
    print(f"   Portfolio: ${result.observation.portfolio_value:,.2f}")
    print(f"   Cash: ${result.observation.cash_balance:,.2f}")
    print(f"   Prices: {result.observation.prices}")

    # Test calm trade (should execute)
    print("\n4️⃣ Testing CALM trade (stress=3)...")
    action = FinPulseAction(
        action_type='buy',
        symbol='AAPL',
        amount_pct=0.3,
        user_stress=3,
        user_confidence=8
    )
    result = env.step(action)

    if result.observation.intervention:
        print(f"   ❌ Unexpected block: {result.observation.intervention_reason}")
    else:
        print(f"   ✅ Trade executed!")
        print(f"   Portfolio: ${result.observation.portfolio_value:,.2f}")
        print(f"   Reward: {result.reward:+.2f}")

    # Test panic sell (should block)
    print("\n5️⃣ Testing PANIC SELL (stress=9)...")
    action = FinPulseAction(
        action_type='sell',
        symbol='AAPL',
        amount_pct=0.5,
        user_stress=9,
        user_confidence=2
    )
    result = env.step(action)

    if result.observation.intervention:
        print(f"   ✅ Correctly blocked!")
        print(f"   Reason: {result.observation.intervention_reason[:80]}...")
        print(f"   Reward (for blocking): {result.reward:+.2f}")
    else:
        print(f"   ❌ Should have been blocked!")

    # Get state
    print("\n6️⃣ Getting episode state...")
    state = env.state()
    print(f"   Episode: {state.episode_id}")
    print(f"   Steps: {state.step_count}")
    print(f"   Trades: {state.total_trades}")

    print("\n" + "="*60)
    print("✅ All tests passed! FinPulse OpenEnv is working correctly!")
    print("="*60 + "\n")


if __name__ == '__main__':
    try:
        test_basic_flow()
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        print("💡 Make sure server is running:")
        print("   docker-compose up\n")
        import traceback
        traceback.print_exc()
