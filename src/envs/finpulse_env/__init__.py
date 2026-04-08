"""FinPulse Trading Environment with Emotional Intelligence"""

# Client is only needed when using the environment remotely
# Server-side code doesn't need it
try:
    from .client import FinPulseTradingEnv
    __all__ = ['FinPulseTradingEnv']
except ImportError:
    # Server environment - client imports not available
    __all__ = []
