"""
Enhanced Configuration Manager for Nazmito Pre-Authorization System.

Provides centralized configuration management with:
- Hierarchical YAML configuration files
- Environment variable overrides
- Type validation and conversion
- Path resolution
- Healthcare-specific configuration
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, TypeVar, Type
from dataclasses import dataclass
from loguru import logger
import yaml


T = TypeVar('T')


@dataclass
class HealthcareConfig:
    """Healthcare-specific configuration parameters."""
    default_currency: str
    default_timezone: str
    supported_code_systems: List[str]
    max_services_per_claim: int
    max_claim_amount_aed: int
    age_validation_min: int
    age_validation_max: int
    processing_timeout_seconds: int
    decision_timeout_seconds: int


@dataclass
class PolicyConfig:
    """Policy engine configuration parameters."""
    cost_thresholds: Dict[str, int]
    age_thresholds: Dict[str, int]
    clinical_thresholds: Dict[str, float]
    therapy_durations: Dict[str, int]


@dataclass
class StorageConfig:
    """File storage and path configuration."""
    data_directory: Path
    processed_data_directory: Path
    backup_directory: Path
    upload_directory: Path
    template_directory: Path
    knowledge_base_directory: Path
    policy_directory: Path
    
    def __post_init__(self):
        """Ensure all paths are Path objects and absolute."""
        project_root = Path(__file__).parent.parent
        
        for field_name in self.__dataclass_fields__:
            path_value = getattr(self, field_name)
            if isinstance(path_value, str):
                path_value = Path(path_value)
            
            # Make relative paths absolute from project root
            if not path_value.is_absolute():
                path_value = project_root / path_value
            
            setattr(self, field_name, path_value)


@dataclass
class DemoConfig:
    """Demo and testing configuration."""
    sample_files: Dict[str, str]
    max_demo_requests_per_hour: int
    demo_data_retention_days: int


class ConfigManager:
    """
    Centralized configuration manager with hierarchical loading.
    
    Loads configuration from:
    1. Base configuration (config/base.yaml)
    2. Environment-specific configuration (config/{env}.yaml)
    3. Environment variables (overrides)
    """
    
    def __init__(self, environment: Optional[str] = None, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            environment: Target environment (development, staging, production)
            config_dir: Custom configuration directory path
        """
        self.environment = environment or os.getenv("ENV", "development").lower()
        
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to config/ directory from project root
            project_root = Path(__file__).parent.parent
            self.config_dir = project_root / "config"
        
        self.config_dir.mkdir(exist_ok=True)
        
        # Load configuration hierarchy
        self._config: Dict[str, Any] = {}
        self._load_configuration()
        
        # Initialize structured configs
        self._healthcare_config: Optional[HealthcareConfig] = None
        self._policy_config: Optional[PolicyConfig] = None
        self._storage_config: Optional[StorageConfig] = None
        self._demo_config: Optional[DemoConfig] = None
    
    def _load_configuration(self):
        """Load configuration from files and environment variables."""
        # 1. Load base configuration
        base_file = self.config_dir / "base.yaml"
        if base_file.exists():
            with open(base_file, 'r') as f:
                base_config = yaml.safe_load(f) or {}
            self._config = self._deep_merge(self._config, base_config)
            logger.debug(f"Loaded base configuration from {base_file}")
        
        # 2. Load environment-specific configuration  
        env_file = self.config_dir / f"{self.environment}.yaml"
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_config = yaml.safe_load(f) or {}
            self._config = self._deep_merge(self._config, env_config)
            logger.debug(f"Loaded {self.environment} configuration from {env_file}")
        
        # 3. Apply environment variable overrides
        self._apply_env_overrides()
        
        # 4. Resolve variable references
        self._resolve_variables()
        
        logger.info(f"Configuration loaded for environment: {self.environment}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides using dot notation."""
        # Map common environment variables to config paths
        env_mappings = {
            "DATABASE_URL": "database.url",
            "REDIS_URL": "cache.redis_url", 
            "CLAUDE_API_KEY": "ai.claude_api_key",
            "SECRET_KEY": "security.secret_key",
            "JWT_SECRET": "security.jwt_secret",
            "API_HOST": "server.host",
            "API_PORT": "server.port",
            "WORKERS": "server.workers",
            "LOG_LEVEL": "logging.level",
            "ENV": "app.environment",
            "DEBUG": "app.debug"
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_path, self._convert_env_value(env_value))
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type."""
        # Boolean values
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        
        # Numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # String value
        return value
    
    def _set_nested_value(self, path: str, value: Any):
        """Set a nested dictionary value using dot notation."""
        keys = path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _resolve_variables(self):
        """Resolve variable references like ${ENV_VAR} in configuration values."""
        def resolve_value(value):
            if isinstance(value, str):
                # Find ${VAR} patterns
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                
                for match in matches:
                    env_value = os.getenv(match, f"${{{match}}}")  # Keep original if not found
                    value = value.replace(f"${{{match}}}", env_value)
                
                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            else:
                return value
        
        self._config = resolve_value(self._config)
    
    def get(self, path: str, default: Any = None, value_type: Optional[Type[T]] = None) -> T:
        """
        Get configuration value using dot notation.
        
        Args:
            path: Dot-separated path to configuration value
            default: Default value if path not found
            value_type: Expected type for validation
            
        Returns:
            Configuration value with optional type conversion
        """
        keys = path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
        except (KeyError, TypeError):
            return default
        
        # Type conversion if requested
        if value_type and current is not None:
            try:
                if value_type == bool and isinstance(current, str):
                    return current.lower() in ('true', '1', 'yes', 'on')
                elif value_type == Path:
                    return Path(current)
                else:
                    return value_type(current)
            except (ValueError, TypeError) as e:
                logger.warning(f"Type conversion failed for {path}: {e}")
                return default
        
        return current
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self._config.get(section, {})
    
    def get_healthcare_config(self) -> HealthcareConfig:
        """Get structured healthcare configuration."""
        if self._healthcare_config is None:
            hc_config = self.get_section('healthcare')
            age_val = hc_config.get('age_validation', {})
            
            self._healthcare_config = HealthcareConfig(
                default_currency=hc_config.get('default_currency', 'AED'),
                default_timezone=hc_config.get('default_timezone', 'Asia/Dubai'),
                supported_code_systems=hc_config.get('supported_code_systems', []),
                max_services_per_claim=hc_config.get('max_services_per_claim', 50),
                max_claim_amount_aed=hc_config.get('max_claim_amount_aed', 500000),
                age_validation_min=age_val.get('min_age', 0),
                age_validation_max=age_val.get('max_age', 120),
                processing_timeout_seconds=hc_config.get('processing_timeout_seconds', 300),
                decision_timeout_seconds=hc_config.get('decision_timeout_seconds', 180)
            )
        
        return self._healthcare_config
    
    def get_policy_config(self) -> PolicyConfig:
        """Get structured policy engine configuration."""
        if self._policy_config is None:
            policy_config = self.get_section('policy')
            
            self._policy_config = PolicyConfig(
                cost_thresholds=policy_config.get('cost_thresholds', {}),
                age_thresholds=policy_config.get('age_thresholds', {}),
                clinical_thresholds=policy_config.get('clinical_thresholds', {}),
                therapy_durations=policy_config.get('therapy_durations', {})
            )
        
        return self._policy_config
    
    def get_storage_config(self) -> StorageConfig:
        """Get structured storage configuration with resolved paths."""
        if self._storage_config is None:
            storage_config = self.get_section('storage')
            
            self._storage_config = StorageConfig(
                data_directory=storage_config.get('data_directory', 'data'),
                processed_data_directory=storage_config.get('processed_data_directory', 'data/processed'),
                backup_directory=storage_config.get('backup_directory', 'data/backups'),
                upload_directory=storage_config.get('upload_directory', 'data/uploads'),
                template_directory=storage_config.get('template_directory', 'preauth_system/templates'),
                knowledge_base_directory=storage_config.get('knowledge_base_directory', 'kb'),
                policy_directory=storage_config.get('policy_directory', 'preauth_system/policy/policies')
            )
        
        return self._storage_config
    
    def get_demo_config(self) -> DemoConfig:
        """Get structured demo configuration."""
        if self._demo_config is None:
            demo_config = self.get_section('demo')
            
            self._demo_config = DemoConfig(
                sample_files=demo_config.get('sample_files', {}),
                max_demo_requests_per_hour=demo_config.get('max_demo_requests_per_hour', 100),
                demo_data_retention_days=demo_config.get('demo_data_retention_days', 7)
            )
        
        return self._demo_config
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        
        # Required environment variables in production
        if self.is_production():
            required_env_vars = ["DATABASE_URL", "REDIS_URL", "CLAUDE_API_KEY", "SECRET_KEY"]
            for var in required_env_vars:
                if not os.getenv(var):
                    errors.append(f"Missing required environment variable: {var}")
        
        # Validate port ranges
        api_port = self.get('server.port', 8000, int)
        if not (1 <= api_port <= 65535):
            errors.append(f"Invalid API port: {api_port}")
        
        # Validate required directories exist or can be created
        try:
            storage = self.get_storage_config()
            for field_name in storage.__dataclass_fields__:
                path = getattr(storage, field_name)
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {field_name}: {path} - {e}")
        except Exception as e:
            errors.append(f"Storage configuration error: {e}")
        
        # Validate healthcare limits
        healthcare = self.get_healthcare_config()
        if healthcare.max_claim_amount_aed <= 0:
            errors.append("Healthcare max_claim_amount_aed must be positive")
        
        if healthcare.processing_timeout_seconds <= 0:
            errors.append("Healthcare processing_timeout_seconds must be positive")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary (excluding sensitive values)."""
        config_copy = self._config.copy()
        
        # Remove sensitive values
        sensitive_paths = [
            'ai.claude_api_key',
            'database.url',
            'security.secret_key',
            'security.jwt_secret'
        ]
        
        for path in sensitive_paths:
            keys = path.split('.')
            current = config_copy
            try:
                for key in keys[:-1]:
                    current = current[key]
                if keys[-1] in current:
                    current[keys[-1]] = "[REDACTED]"
            except (KeyError, TypeError):
                pass  # Path doesn't exist
        
        return config_copy


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(environment: Optional[str] = None, force_reload: bool = False) -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None or force_reload:
        _config_manager = ConfigManager(environment)
        
        # Validate configuration
        errors = _config_manager.validate()
        if errors:
            logger.error("Configuration validation errors:")
            for error in errors:
                logger.error(f"  - {error}")
            
            if _config_manager.is_production():
                raise ValueError("Configuration validation failed in production")
    
    return _config_manager


def get_config(path: str, default: Any = None, value_type: Optional[Type[T]] = None) -> T:
    """Convenience function to get configuration value."""
    return get_config_manager().get(path, default, value_type)


if __name__ == "__main__":
    # Test configuration loading
    config_mgr = ConfigManager("development")
    
    print("Configuration Test")
    print("==================")
    print(f"Environment: {config_mgr.environment}")
    print(f"Debug mode: {config_mgr.get('app.debug')}")
    print(f"API host: {config_mgr.get('server.host')}")
    print(f"API port: {config_mgr.get('server.port')}")
    
    # Test healthcare config
    hc = config_mgr.get_healthcare_config()
    print(f"\nHealthcare Config:")
    print(f"  Currency: {hc.default_currency}")
    print(f"  Max claim amount: {hc.max_claim_amount_aed} AED")
    
    # Test storage config
    sc = config_mgr.get_storage_config()
    print(f"\nStorage Config:")
    print(f"  Data directory: {sc.data_directory}")
    print(f"  Template directory: {sc.template_directory}")
    
    # Test validation
    errors = config_mgr.validate()
    if errors:
        print(f"\nValidation Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration validation passed")