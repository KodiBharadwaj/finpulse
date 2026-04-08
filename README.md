---
title: FinPulse Trading Environment
emoji: 💰
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
---

---
title: FinPulse Trading Env
sdk: docker
app_port: 8000
---

# 🫀 FinPulse: OpenEnv Trading Environment with Emotional Intelligence

**AI-powered wealth management that prevents costly emotional trading decisions.**

## 🎯 Environment Description

FinPulse is a **production-ready OpenEnv environment** for reinforcement learning research in emotional trading.

### **Problem Statement**

Research shows that 85%+ of retail investors make costly emotional mistakes:
- **Panic Selling**: Selling during market drops, locking in losses
- **FOMO Buying**: Buying at peaks due to fear of missing out
- **Overtrading**: Making excessive trades driven by anxiety

FinPulse simulates real-world trading scenarios where AI agents must balance:
1. **Financial Performance**: Maximize portfolio returns
2. **Emotional Intelligence**: Manage stress and confidence levels
3. **Risk Management**: Control volatility and avoid destructive behavior

### **Key Innovation**

The environment actively **intervenes** when detecting emotional trading patterns, forcing agents to develop strategies that account for both market dynamics and psychological factors—mirroring real human investor challenges.

**OpenEnv Compliant:**
- ✅ Client-server architecture (HTTP)
- ✅ Type-safe models (dataclasses)
- ✅ Environment in Docker
- ✅ Dockerfile inside `server/`
- ✅ Standard endpoints: `/reset`, `/step`, `/state`
- ✅ 3 tasks with difficulty progression (easy → medium → hard)
- ✅ Programmatic graders with scores 0.0-1.0

## 🎮 Tasks

FinPulse includes **3 trading tasks** with increasing difficulty:

### **Task 1: Conservative Trading (Easy)** 🟢
- **Goal**: Achieve 5% return in 30 steps
- **Strategy**: Low-risk, focus on emotional stability
- **Success Criteria**: Portfolio return ≥ 5%, low interventions, stress ≤ 5
- **Grading**: 
  - Return (50%)
  - Low interventions (25%)
  - Emotional stability (25%)

### **Task 2: Balanced Trading (Medium)** 🟡
- **Goal**: Achieve 15% return in 50 steps
- **Strategy**: Balance risk and reward
- **Success Criteria**: Portfolio return ≥ 15%, managed volatility
- **Grading**:
  - Return (60%)
  - Risk management (30%)
  - Intervention avoidance (10%)

### **Task 3: Aggressive Growth (Hard)** 🔴
- **Goal**: Achieve 30% return in 100 steps
- **Strategy**: High returns with optimal risk-adjusted performance
- **Success Criteria**: Portfolio return ≥ 30%, high Sharpe ratio
- **Grading**:
  - Return (50%)
  - Sharpe ratio (40%)
  - Efficiency (10%)

## 🚀 Setup Instructions

### **Prerequisites**
- Docker Desktop or Docker Engine installed
- Python 3.10+ (for running inference)
- 2 vCPU + 8GB RAM minimum

### **Installation Steps**

**1. Clone Repository**
```bash
git clone https://github.com/saikiranworkmail13-cell/fin-pulse.git
cd fin-pulse
```

**2. Configure Environment (Optional)**
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

**Required variables for LLM inference:**
```bash
HF_TOKEN=your_huggingface_token          # Get from: https://huggingface.co/settings/tokens
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct     # Or any compatible model
API_BASE_URL=https://router.huggingface.co/v1
```

**Optional: Real market data via Alpaca:**
```bash
ALPACA_API_KEY=your_alpaca_key           # Get from: https://alpaca.markets/
ALPACA_SECRET_KEY=your_alpaca_secret
```

**3. Start Environment Server**
```bash
# Build and start Docker container
docker-compose up --build -d

# Verify server is running
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

**4. Install Client Dependencies**
```bash
pip install -r requirements-client.txt
```

**5. Run Baseline Inference**
```bash
# Test all 3 tasks
python inference.py
```

**Expected output:**
```
[START] task=conservative_trading env=finpulse model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=buy('AAPL',0.30) reward=0.00 done=false error=null
...
[END] success=true steps=30 score=0.750 rewards=0.00,1.20,...
[START] task=balanced_trading ...
...
[END] success=true steps=50 score=0.650 rewards=...
[START] task=aggressive_growth ...
...
[END] success=false steps=100 score=0.450 rewards=...
```

### **API Endpoints**

Once the server is running, you can interact via HTTP:

```bash
# List all tasks
curl http://localhost:8000/tasks

# Reset environment
curl -X POST http://localhost:8000/reset

# Execute trading action
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "buy",
    "symbol": "AAPL",
    "amount_pct": 0.3,
    "user_stress": 5,
    "user_confidence": 7
  }'

# Grade episode
curl -X POST "http://localhost:8000/grade?task=conservative_trading" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_return": 0.06,
    "interventions": 1,
    "avg_stress": 5.2,
    "total_steps": 25
  }'
```

### **Web Interface**

Access the interactive dashboard at: http://localhost:8000

Features:
- Real-time portfolio tracking
- Manual trading interface
- Emotional state controls
- Intervention alerts

## 📊 Action & Observation Spaces

### **Action Space**

The agent must provide trading decisions with emotional state information:

```python
{
    "action_type": str,      # "buy", "sell", or "hold"
    "symbol": str,           # "AAPL", "MSFT", or "GOOGL"
    "amount_pct": float,     # Percentage of portfolio (0.0 - 1.0)
    "user_stress": int,      # Stress level (1-10 scale)
    "user_confidence": int   # Confidence level (1-10 scale)
}
```

**Example:**
```python
FinPulseAction(
    action_type="buy",
    symbol="AAPL",
    amount_pct=0.3,        # Use 30% of available cash
    user_stress=4,         # Low stress
    user_confidence=8      # High confidence
)
```

---

### **Observation Space**

The environment returns comprehensive market and portfolio state:

```python
{
    "prices": {
        "AAPL": float,       # Current price of Apple stock
        "MSFT": float,       # Current price of Microsoft stock
        "GOOGL": float       # Current price of Google stock
    },
    "portfolio_value": float,     # Total portfolio value (cash + positions)
    "cash_balance": float,        # Available cash
    "positions": {
        "AAPL": int,         # Number of Apple shares owned
        "MSFT": int,         # Number of Microsoft shares owned
        "GOOGL": int         # Number of Google shares owned
    },
    "emotional_state": {
        "stress": float,     # Current stress level (1-10)
        "confidence": float, # Current confidence level (1-10)
        "mood": float,       # Derived from stress (10 - stress)
        "energy": float      # Derived from confidence
    },
    "intervention": bool,            # Was the action blocked?
    "intervention_reason": str,      # Why was it blocked (if applicable)
    "reward": float,                 # Reward signal for this step
    "done": bool,                    # Episode complete?
    "metadata": {
        "step": int,         # Current step number
        "trades": int        # Total trades executed
    }
}
```

**Example Observation:**
```python
{
    "prices": {"AAPL": 180.5, "MSFT": 385.2, "GOOGL": 142.8},
    "portfolio_value": 10250.0,
    "cash_balance": 7000.0,
    "positions": {"AAPL": 18, "MSFT": 0, "GOOGL": 0},
    "emotional_state": {"stress": 4.0, "confidence": 8.0},
    "intervention": false,
    "reward": 2.5,
    "done": false
}
```

---

## 💻 Usage

```python
from envs.finpulse_env import FinPulseTradingEnv
from envs.finpulse_env.models import FinPulseAction

env = FinPulseTradingEnv(base_url="http://localhost:8000")

result = env.reset()

action = FinPulseAction(
    action_type="buy",
    symbol="AAPL",
    amount_pct=0.3,
    user_stress=5,
    user_confidence=7
)

result = env.step(action)
```

## 📁 Structure

```
finpulse/
├── src/
│   ├── core/              # OpenEnv base classes
│   └── envs/finpulse_env/
│       ├── models.py      # Type-safe models
│       ├── client.py      # HTTP client
│       └── server/
│           ├── environment.py
│           ├── app.py
│           └── Dockerfile  ← OpenEnv requirement
├── examples/
└── docker-compose.yml
```

## 🧠 Features

### Emotional Intelligence
- **Panic Selling Prevention**: Blocks high-stress sells (stress > 7)
- **Overtrading Detection**: Prevents excessive trading (6+ trades in 10 steps)
- **FOMO Prevention**: Blocks low-confidence buys during price surges

### Real Market Data
- **Alpaca API Integration**: Fetch real-time stock prices from Alpaca Paper Trading
- **Graceful Fallback**: Works in demo mode if API unavailable
- **Live Portfolio Tracking**: Real-time portfolio value and positions

### Interactive Web UI
- **Beautiful Dashboard**: Real-time portfolio metrics and charts
- **Emotional Sliders**: Adjust stress and confidence levels
- **One-Click Trading**: Buy, sell, or hold with instant feedback
- **Intervention Alerts**: See why trades are blocked in real-time

## 📚 OpenEnv Compliance

✅ All requirements met - ready for hackathon submission!
