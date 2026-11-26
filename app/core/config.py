import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    app_name: str = "AWS CI/CD Demo"
    app_version: str = "1.0.0"
    service_name: str = "aws-cicd-demo"

    log_level: str = "INFO"

    github_mcp_token: str | None = None
    github_repository_owner: str = "razamehar"
    github_repository_name: str = "python-service-lab"
    github_mcp_url: str = "https://api.githubcopilot.com/mcp/readonly"

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load configuration from environment variables."""
        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            github_mcp_token=os.getenv("GITHUB_MCP_TOKEN"),
            github_repository_owner=os.getenv(
                "GITHUB_REPOSITORY_OWNER",
                "razamehar",
            ),
            github_repository_name=os.getenv(
                "GITHUB_REPOSITORY_NAME",
                "python-service-lab",
            ),
            github_mcp_url=os.getenv(
                "GITHUB_MCP_URL",
                "https://api.githubcopilot.com/mcp/readonly",
            ),
        )


def get_settings() -> Settings:
    """Return the current application settings."""
    return Settings.from_environment()  