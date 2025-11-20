"""
Production configuration management for Healthcare AI Pre-authorization API.

Handles environment variables, secrets management, and configuration validation
for different deployment environments.
"""

import os
import secrets
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from loguru import logger
import yaml


class Environment(str, Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = "sqlite:///./healthcare_preauth.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            url=os.getenv("DATABASE_URL", cls.url),
            pool_size=int(os.getenv("DB_POOL_SIZE", str(cls.pool_size))),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", str(cls.max_overflow))),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", str(cls.pool_timeout))),
            echo=os.getenv("DB_ECHO", str(cls.echo)).lower() == "true"
        )


@dataclass
class RedisConfig:
    """Redis cache configuration."""
    url: str = "redis://localhost:6379/0"
    password: Optional[str] = None
    max_connections: int = 100
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    @classmethod
    def from_env(cls) -> "RedisConfig":
        return cls(
            url=os.getenv("REDIS_URL", cls.url),
            password=os.getenv("REDIS_PASSWORD"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", str(cls.max_connections))),
            socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", str(cls.socket_timeout))),
            socket_connect_timeout=int(os.getenv("REDIS_CONNECT_TIMEOUT", str(cls.socket_connect_timeout))),
            retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", str(cls.retry_on_timeout)).lower() == "true",
            health_check_interval=int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", str(cls.health_check_interval)))
        )


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    api_key_length: int = 32
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"])
    trusted_hosts: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])
    bcrypt_rounds: int = 12
    session_timeout_minutes: int = 60
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        trusted_hosts_str = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1")
        
        return cls(
            secret_key=os.getenv("SECRET_KEY", secrets.token_urlsafe(32)),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", cls.jwt_algorithm),
            jwt_expiry_hours=int(os.getenv("JWT_EXPIRY_HOURS", str(cls.jwt_expiry_hours))),
            api_key_length=int(os.getenv("API_KEY_LENGTH", str(cls.api_key_length))),
            cors_origins=cors_origins_str.split(",") if cors_origins_str else cls.cors_origins,
            trusted_hosts=trusted_hosts_str.split(",") if trusted_hosts_str else cls.trusted_hosts,
            bcrypt_rounds=int(os.getenv("BCRYPT_ROUNDS", str(cls.bcrypt_rounds))),
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", str(cls.session_timeout_minutes)))
        )


@dataclass
class PerformanceConfig:
    """Performance and resource configuration."""
    workers: int = 4
    max_requests: int = 1000
    max_requests_jitter: int = 50
    timeout: int = 120
    keepalive: int = 2
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    memory_limit_gb: float = 2.0
    cpu_limit: float = 2.0
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_max_size: int = 500
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    
    @classmethod
    def from_env(cls) -> "PerformanceConfig":
        return cls(
            workers=int(os.getenv("WORKERS", str(cls.workers))),
            max_requests=int(os.getenv("MAX_REQUESTS", str(cls.max_requests))),
            max_requests_jitter=int(os.getenv("MAX_REQUESTS_JITTER", str(cls.max_requests_jitter))),
            timeout=int(os.getenv("TIMEOUT", str(cls.timeout))),
            keepalive=int(os.getenv("KEEPALIVE", str(cls.keepalive))),
            max_file_size=int(os.getenv("MAX_FILE_SIZE", str(cls.max_file_size))),
            memory_limit_gb=float(os.getenv("MEMORY_LIMIT_GB", str(cls.memory_limit_gb))),
            cpu_limit=float(os.getenv("CPU_LIMIT", str(cls.cpu_limit))),
            cache_enabled=os.getenv("CACHE_ENABLED", str(cls.cache_enabled)).lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", str(cls.cache_ttl))),
            cache_max_size=int(os.getenv("CACHE_MAX_SIZE", str(cls.cache_max_size))),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", str(cls.rate_limit_requests))),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", str(cls.rate_limit_window)))
        )


@dataclass
class AIConfig:
    """AI/LLM service configuration."""
    # Claude/Anthropic settings
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    claude_max_tokens: int = 4000
    claude_temperature: float = 0.1
    
    # Cost controls
    daily_budget_usd: float = 50.0
    cost_alert_threshold_usd: float = 0.08
    max_tokens_per_request: int = 8000
    
    # Performance settings
    request_timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        return cls(
            claude_api_key=os.getenv("CLAUDE_API_KEY"),
            claude_model=os.getenv("CLAUDE_MODEL", cls.claude_model),
            claude_max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", str(cls.claude_max_tokens))),
            claude_temperature=float(os.getenv("CLAUDE_TEMPERATURE", str(cls.claude_temperature))),
            daily_budget_usd=float(os.getenv("DAILY_BUDGET", str(cls.daily_budget_usd))),
            cost_alert_threshold_usd=float(os.getenv("COST_ALERT_THRESHOLD", str(cls.cost_alert_threshold_usd))),
            max_tokens_per_request=int(os.getenv("MAX_TOKENS_PER_REQUEST", str(cls.max_tokens_per_request))),
            request_timeout=int(os.getenv("AI_REQUEST_TIMEOUT", str(cls.request_timeout))),
            max_retries=int(os.getenv("AI_MAX_RETRIES", str(cls.max_retries))),
            retry_delay=float(os.getenv("AI_RETRY_DELAY", str(cls.retry_delay)))
        )


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}"
    rotation: str = "10 MB"
    retention: str = "30 days"
    compression: str = "gz"
    serialize: bool = False
    
    # Structured logging
    structured_logs: bool = True
    json_logs: bool = False
    
    # File paths
    log_dir: str = "logs"
    api_log_file: str = "api.log"
    error_log_file: str = "errors.log"
    audit_log_file: str = "audit.log"
    
    @classmethod
    def from_env(cls) -> "LoggingConfig":
        return cls(
            level=os.getenv("LOG_LEVEL", cls.level),
            format=os.getenv("LOG_FORMAT", cls.format),
            rotation=os.getenv("LOG_ROTATION", cls.rotation),
            retention=os.getenv("LOG_RETENTION", cls.retention),
            compression=os.getenv("LOG_COMPRESSION", cls.compression),
            serialize=os.getenv("LOG_SERIALIZE", str(cls.serialize)).lower() == "true",
            structured_logs=os.getenv("STRUCTURED_LOGS", str(cls.structured_logs)).lower() == "true",
            json_logs=os.getenv("JSON_LOGS", str(cls.json_logs)).lower() == "true",
            log_dir=os.getenv("LOG_DIR", cls.log_dir),
            api_log_file=os.getenv("API_LOG_FILE", cls.api_log_file),
            error_log_file=os.getenv("ERROR_LOG_FILE", cls.error_log_file),
            audit_log_file=os.getenv("AUDIT_LOG_FILE", cls.audit_log_file)
        )


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    # Metrics
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    metrics_path: str = "/metrics"
    
    # Health checks
    health_check_interval: int = 30
    health_check_timeout: int = 10
    health_check_retries: int = 3
    
    # Alerting
    alert_webhook_url: Optional[str] = None
    alert_email_recipients: List[str] = field(default_factory=list)
    
    # Tracing
    jaeger_enabled: bool = False
    jaeger_endpoint: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "MonitoringConfig":
        alert_emails_str = os.getenv("ALERT_EMAIL_RECIPIENTS", "")
        
        return cls(
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", str(cls.prometheus_enabled)).lower() == "true",
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", str(cls.prometheus_port))),
            metrics_path=os.getenv("METRICS_PATH", cls.metrics_path),
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", str(cls.health_check_interval))),
            health_check_timeout=int(os.getenv("HEALTH_CHECK_TIMEOUT", str(cls.health_check_timeout))),
            health_check_retries=int(os.getenv("HEALTH_CHECK_RETRIES", str(cls.health_check_retries))),
            alert_webhook_url=os.getenv("ALERT_WEBHOOK_URL"),
            alert_email_recipients=alert_emails_str.split(",") if alert_emails_str else cls.alert_email_recipients,
            jaeger_enabled=os.getenv("JAEGER_ENABLED", str(cls.jaeger_enabled)).lower() == "true",
            jaeger_endpoint=os.getenv("JAEGER_ENDPOINT")
        )


@dataclass
class AppConfig:
    """Complete application configuration."""
    env: Environment = Environment.DEVELOPMENT
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api"
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "authentication_required": False,
        "rate_limiting": True,
        "caching": True,
        "monitoring": True,
        "demo_mode": False
    })
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig.from_env)
    redis: RedisConfig = field(default_factory=RedisConfig.from_env)
    security: SecurityConfig = field(default_factory=SecurityConfig.from_env)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig.from_env)
    ai: AIConfig = field(default_factory=AIConfig.from_env)
    logging: LoggingConfig = field(default_factory=LoggingConfig.from_env)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig.from_env)
    
    @classmethod
    def from_env(cls, config_file: Optional[str] = None) -> "AppConfig":
        """Create configuration from environment variables and optional config file."""
        
        # Load environment
        env_str = os.getenv("ENV", "development").lower()
        try:
            env = Environment(env_str)
        except ValueError:
            logger.warning(f"Invalid environment '{env_str}', defaulting to development")
            env = Environment.DEVELOPMENT
        
        # Base configuration
        config = cls(
            env=env,
            debug=os.getenv("DEBUG", str(env == Environment.DEVELOPMENT)).lower() == "true",
            api_host=os.getenv("API_HOST", cls.api_host),
            api_port=int(os.getenv("API_PORT", str(cls.api_port))),
            api_prefix=os.getenv("API_PREFIX", cls.api_prefix)
        )
        
        # Load from config file if provided
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                    config = cls._merge_config(config, file_config)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        # Environment-specific adjustments
        if env == Environment.PRODUCTION:
            config.features["authentication_required"] = True
            config.features["demo_mode"] = False
            config.debug = False
        elif env == Environment.DEVELOPMENT:
            config.features["demo_mode"] = True
        
        return config
    
    @staticmethod
    def _merge_config(base_config: "AppConfig", file_config: Dict[str, Any]) -> "AppConfig":
        """Merge file configuration with base configuration."""
        # This is a simplified merge - in production you might want more sophisticated merging
        for key, value in file_config.items():
            if hasattr(base_config, key):
                setattr(base_config, key, value)
        return base_config
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == Environment.DEVELOPMENT
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        
        # Check required production settings
        if self.is_production():
            if not self.ai.claude_api_key:
                errors.append("Claude API key is required in production")
            
            if self.security.secret_key == "your-secret-key-change-in-production":
                errors.append("Default secret key detected in production")
            
            if "localhost" in self.security.cors_origins:
                errors.append("Localhost in CORS origins for production")
        
        # Validate port range
        if not (1 <= self.api_port <= 65535):
            errors.append(f"Invalid API port: {self.api_port}")
        
        # Validate performance settings
        if self.performance.workers < 1:
            errors.append("Workers count must be at least 1")
        
        if self.performance.memory_limit_gb < 0.5:
            errors.append("Memory limit too low (minimum 0.5GB)")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "env": self.env.value,
            "debug": self.debug,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "api_prefix": self.api_prefix,
            "features": self.features,
            # Note: Sensitive values like API keys are excluded
            "database_url": self.database.url.split("@")[-1] if "@" in self.database.url else "[hidden]",
            "redis_configured": bool(self.redis.url),
            "cache_enabled": self.performance.cache_enabled,
            "rate_limiting": self.features.get("rate_limiting", True),
            "authentication_required": self.features.get("authentication_required", False)
        }


# Global configuration instance
_app_config: Optional[AppConfig] = None


def get_config(config_file: Optional[str] = None, force_reload: bool = False) -> AppConfig:
    """Get the global application configuration."""
    global _app_config
    
    if _app_config is None or force_reload:
        # Determine config file path
        if not config_file:
            env = os.getenv("ENV", "development").lower()
            config_file = f"config/{env}.yaml"
        
        _app_config = AppConfig.from_env(config_file)
        
        # Validate configuration
        errors = _app_config.validate()
        if errors:
            logger.error("Configuration validation errors:")
            for error in errors:
                logger.error(f"  - {error}")
            if _app_config.is_production():
                raise ValueError("Configuration validation failed in production")
        
        logger.info(f"Configuration loaded: environment={_app_config.env.value}, debug={_app_config.debug}")
    
    return _app_config


# Environment variable helpers
def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        logger.warning(f"Invalid integer value for {key}, using default: {default}")
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float environment variable."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        logger.warning(f"Invalid float value for {key}, using default: {default}")
        return default


def get_env_list(key: str, default: List[str] = None, separator: str = ",") -> List[str]:
    """Get list environment variable."""
    if default is None:
        default = []
    
    value = os.getenv(key)
    if not value:
        return default
    
    return [item.strip() for item in value.split(separator) if item.strip()]