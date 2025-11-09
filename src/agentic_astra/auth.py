import time
from typing import Any
from fastmcp.server.auth.providers.jwt import AccessToken, TokenVerifier
from .logger import get_logger
import os
logger = get_logger("auth")

class AstraAuth(TokenVerifier):
    """
    Astra auth for testing and development.
    """

    def __init__(
        self,
        token: str
    ):
        """
        Initialize the Astra auth.

        Args:
            token: Dict mapping token strings to token metadata
                   Each token should have: client_id, scopes, expires_at (optional)
        """
        super().__init__()
        self.token = token

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify token against Astra token dictionary."""
        logger.info(f"Token: {token}")
        
        token_env = os.getenv("AGENTIC_ASTRA_TOKEN") or os.getenv("ASTRA_MCP_SERVER_TOKEN")
        if token != token_env:
            return None
        logger.info(f"Token successfully verified: {token}")
        
        return AccessToken(
            token=token,
            client_id="agentic-astra",
            scopes=["read:data"],
            expires_at=time.time() + 3600,
            claims={},
        )