"""
Inference Script for FinPulse Trading Environment
===================================
MANDATORY ENVIRONMENT VARIABLES:
- API_BASE_URL: The API endpoint for the LLM (default: https://router.huggingface.co/v1)
- MODEL_NAME: The model identifier (default: Qwen/Qwen2.5-72B-Instruct)
- HF_TOKEN or API_KEY: Your Hugging Face / API key
- ENV_BASE_URL: FinPulse environment server URL (default: http://localhost:8000)

STDOUT FORMAT:
- [START] task=<task_name> env=<benchmark> model=<model_name>
- [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
- [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import os
import sys
import textwrap
from typing import List, Optional, Dict
import json

from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from envs.finpulse_env.client import FinPulseTradingEnv
from envs.finpulse_env.models import FinPulseAction

# ========== Configuration ==========
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
BENCHMARK = os.getenv("FINPULSE_BENCHMARK", "finpulse")

# All 3 tasks to test
TASKS_TO_TEST = [
    "conservative_trading",  # Easy
    "balanced_trading",      # Medium
    "aggressive_growth"      # Hard
]

TEMPERATURE = 0.7
MAX_TOKENS = 200
INITIAL_BALANCE = 10000.0

def get_system_prompt(task_name: str, target_return: float, max_steps: int) -> str:
    """Get task-specific system prompt"""
    return textwrap.dedent(
        f"""
        You are an AI trading advisor with emotional intelligence.

        Task: {task_name}
        Goal: Achieve {target_return*100:.0f}% return in {max_steps} steps

        Environment:
        - You have $10,000 to invest in stocks: AAPL, MSFT, GOOGL
        - Each step you can: BUY, SELL, or HOLD
        - You must provide your emotional state: stress (1-10) and confidence (1-10)

        Emotional Intelligence System:
        - High stress (>7) + SELL = BLOCKED (panic selling prevention)
        - Low confidence (<4) + BUY after price surge = BLOCKED (FOMO prevention)
        - Too many trades (>5 in 10 steps) = BLOCKED (overtrading prevention)

        Strategy:
        - Maximize portfolio value through smart trading
        - Maintain emotional stability (low stress, moderate confidence)
        - Avoid emotional mistakes that trigger interventions

        Respond with valid JSON only:
        {{
            "action_type": "buy" | "sell" | "hold",
            "symbol": "AAPL" | "MSFT" | "GOOGL",
            "amount_pct": 0.0-1.0,
            "user_stress": 1-10,
            "user_confidence": 1-10,
            "reasoning": "brief explanation"
        }}
        """
    ).strip()


def log_start(task: str, env: str, model: str) -> None:
    """Log episode start"""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int,
    action: Dict,
    reward: float,
    done: bool,
    error: Optional[str]
) -> None:
    """Log each step"""
    # Format action as readable string
    action_str = f"{action['action_type']}('{action['symbol']}',{action['amount_pct']:.2f})"
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Log episode end"""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True
    )


def build_user_prompt(
    step: int,
    observation: Dict,
    last_reward: float,
    history: List[str]
) -> str:
    """Build prompt for the LLM with current market state"""
    prices = observation.get('prices', {})
    portfolio_value = observation.get('portfolio_value', 0.0)
    cash_balance = observation.get('cash_balance', 0.0)
    positions = observation.get('positions', {})
    emotional_state = observation.get('emotional_state', {})
    intervention = observation.get('intervention', False)
    intervention_reason = observation.get('intervention_reason', None)

    history_block = "\n".join(history[-5:]) if history else "None"

    return_pct = ((portfolio_value - INITIAL_BALANCE) / INITIAL_BALANCE) * 100

    prompt = textwrap.dedent(
        f"""
        === STEP {step} ===

        Market Prices:
        - AAPL: ${prices.get('AAPL', 0):.2f}
        - MSFT: ${prices.get('MSFT', 0):.2f}
        - GOOGL: ${prices.get('GOOGL', 0):.2f}

        Your Portfolio:
        - Total Value: ${portfolio_value:.2f} (Return: {return_pct:+.2f}%)
        - Cash: ${cash_balance:.2f}
        - Positions: AAPL={positions.get('AAPL', 0)}, MSFT={positions.get('MSFT', 0)}, GOOGL={positions.get('GOOGL', 0)}

        Your Emotional State:
        - Stress: {emotional_state.get('stress', 5):.1f}/10
        - Confidence: {emotional_state.get('confidence', 5):.1f}/10

        Last Action Result:
        - Reward: {last_reward:.2f}
        - Intervention: {'Yes - ' + intervention_reason if intervention else 'No'}

        Recent History:
        {history_block}

        What is your next move? Reply with JSON only.
        """
    ).strip()

    return prompt


def parse_model_response(response: str) -> Dict:
    """Parse LLM response to extract action"""
    try:
        # Try to find JSON in the response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            data = json.loads(json_str)

            # Validate and set defaults
            return {
                'action_type': data.get('action_type', 'hold'),
                'symbol': data.get('symbol', 'AAPL'),
                'amount_pct': float(data.get('amount_pct', 0.3)),
                'user_stress': int(data.get('user_stress', 5)),
                'user_confidence': int(data.get('user_confidence', 5)),
            }
    except Exception as e:
        print(f"[DEBUG] Failed to parse model response: {e}", flush=True)

    # Default safe action
    return {
        'action_type': 'hold',
        'symbol': 'AAPL',
        'amount_pct': 0.0,
        'user_stress': 5,
        'user_confidence': 5,
    }


def get_model_action(
    client: OpenAI,
    step: int,
    observation: Dict,
    last_reward: float,
    history: List[str],
    system_prompt: str
) -> Dict:
    """Get trading decision from LLM"""
    user_prompt = build_user_prompt(step, observation, last_reward, history)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )

        response_text = (completion.choices[0].message.content or "").strip()
        action = parse_model_response(response_text)
        return action

    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        # Return safe default
        return {
            'action_type': 'hold',
            'symbol': 'AAPL',
            'amount_pct': 0.0,
            'user_stress': 5,
            'user_confidence': 5,
        }


def run_task(
    client: OpenAI,
    env: FinPulseTradingEnv,
    task_name: str,
    task_config: Dict
) -> Dict:
    """Run a single task and return results"""
    max_steps = task_config['max_steps']
    success_threshold = task_config['success_threshold']
    system_prompt = get_system_prompt(task_name, success_threshold, max_steps)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Set task on server
        import requests
        try:
            requests.post(f"{ENV_BASE_URL}/set_task", params={"task": task_name})
        except:
            pass  # Server might not support /set_task yet

        # Reset environment
        result = env.reset()
        obs_dict = result.observation.__dict__
        last_reward = 0.0

        for step in range(1, max_steps + 1):
            if result.done:
                break

            # Get action from model
            action_dict = get_model_action(client, step, obs_dict, last_reward, history, system_prompt)

            # Execute action
            action = FinPulseAction(**action_dict)
            result = env.step(action)
            obs_dict = result.observation.__dict__

            reward = result.reward or 0.0
            done = result.done
            error = obs_dict.get('intervention_reason') if obs_dict.get('intervention') else None

            rewards.append(reward)
            steps_taken = step
            last_reward = reward

            # Log step
            log_step(step=step, action=action_dict, reward=reward, done=done, error=error)

            # Update history
            portfolio_value = obs_dict.get('portfolio_value', INITIAL_BALANCE)
            return_pct = ((portfolio_value - INITIAL_BALANCE) / INITIAL_BALANCE) * 100
            history.append(
                f"Step {step}: {action_dict['action_type']} {action_dict['symbol']} "
                f"-> reward={reward:+.2f}, portfolio=${portfolio_value:.2f} ({return_pct:+.1f}%)"
            )

            if done:
                break

        # Calculate final score (normalized portfolio return in [0, 1])
        final_value = obs_dict.get('portfolio_value', INITIAL_BALANCE)
        portfolio_return = (final_value - INITIAL_BALANCE) / INITIAL_BALANCE

        # Score: map portfolio return to [0, 1] based on task threshold
        # 0% return = 0.5, target return = 1.0
        score = 0.5 + (portfolio_return / success_threshold * 0.5)
        score = min(max(score, 0.0), 1.0)  # clamp to [0, 1]

        success = portfolio_return >= success_threshold

    except Exception as e:
        print(f"[DEBUG] Inference error: {e}", flush=True)
        score = 0.0
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {
        "task": task_name,
        "success": success,
        "score": score,
        "steps": steps_taken,
        "portfolio_return": portfolio_return if 'portfolio_return' in locals() else 0.0
    }


def main() -> None:
    """Main inference loop - runs all 3 tasks"""
    if not API_KEY:
        print("[ERROR] API_KEY or HF_TOKEN environment variable not set!", flush=True)
        sys.exit(1)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = FinPulseTradingEnv(base_url=ENV_BASE_URL)

    # Get task configs from server
    import requests
    try:
        response = requests.get(f"{ENV_BASE_URL}/tasks")
        tasks_config = response.json()
    except:
        # Fallback configs if server doesn't support /tasks endpoint
        tasks_config = {
            "conservative_trading": {"max_steps": 30, "success_threshold": 0.05},
            "balanced_trading": {"max_steps": 50, "success_threshold": 0.15},
            "aggressive_growth": {"max_steps": 100, "success_threshold": 0.30}
        }

    all_results = []

    # Run all 3 tasks
    for task_name in TASKS_TO_TEST:
        task_config = tasks_config.get(task_name, {"max_steps": 50, "success_threshold": 0.10})
        print(f"\n{'='*60}")
        print(f"Running Task: {task_name.upper().replace('_', ' ')}")
        print(f"{'='*60}\n")

        result = run_task(client, env, task_name, task_config)
        all_results.append(result)

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY - All Tasks")
    print(f"{'='*60}")
    for result in all_results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{result['task']:25s} {status:10s} Score: {result['score']:.3f} ({result['portfolio_return']*100:+.1f}%)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
