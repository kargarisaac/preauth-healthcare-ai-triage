#!/usr/bin/env python3
"""
Configuration Loader
Loads and validates YAML configuration for the Nazmito API.

This module provides centralized configuration management with validation,
environment-specific overrides, and path resolution.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from loguru import logger


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class ConfigLoader:
    """
    Configuration loader with validation and environment support.
    
    Loads YAML configuration files with support for environment-specific
    overrides and path validation.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None, environment: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to configuration file (defaults to api/config.yaml)
            environment: Environment name for override (development, production, testing)
        """
        self.config_path = Path(config_path) if config_path else Path(__file__).parent / "config.yaml"
        self.environment = environment or os.getenv("NAZMITO_ENV", "development")
        self.config = {}
        self._load_config()
        
    def _load_config(self) -> None:
        """Load and validate configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise ConfigurationError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            if not isinstance(self.config, dict):
                raise ConfigurationError("Invalid configuration file format")
            
            # Apply environment-specific overrides
            self._apply_environment_overrides()
            
            # Validate configuration
            self._validate_config()
            
            # Resolve and validate paths
            self._resolve_paths()
            
            logger.info(f"Configuration loaded successfully from {self.config_path} (env: {self.environment})")
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"YAML parsing error: {e}")
        except Exception as e:
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides."""
        if self.environment in self.config:
            env_config = self.config[self.environment]
            if isinstance(env_config, dict):
                self._deep_merge(self.config, env_config)
                logger.debug(f"Applied {self.environment} environment overrides")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Deep merge override configuration into base configuration.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _validate_config(self) -> None:
        """Validate configuration structure and required fields."""
        required_sections = ["dataset", "processing", "patient", "claude", "api"]
        
        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
        
        # Validate dataset paths
        dataset_config = self.config["dataset"]
        required_paths = ["raw_data_path", "processed_data_path"]
        
        for path_key in required_paths:
            if path_key not in dataset_config:
                raise ConfigurationError(f"Missing required dataset path: {path_key}")
        
        # Validate processing configuration
        processing_config = self.config["processing"]
        if "supported_formats" not in processing_config:
            raise ConfigurationError("Missing supported_formats in processing configuration")
        
        # Validate claude configuration
        claude_config = self.config["claude"]
        if "default_cost_limit_usd" in claude_config:
            cost_limit = claude_config["default_cost_limit_usd"]
            if not isinstance(cost_limit, (int, float)) or cost_limit <= 0:
                raise ConfigurationError("Invalid default_cost_limit_usd value")
        
        logger.debug("Configuration validation passed")
    
    def _resolve_paths(self) -> None:
        """Resolve and validate configured paths."""
        # Get project root (assuming config is in api/ subdirectory)
        project_root = self.config_path.parent.parent
        
        # Resolve dataset paths
        dataset_config = self.config["dataset"]
        path_keys = ["raw_data_path", "processed_data_path", "test_data_path", "backup_path", "logs_path"]
        
        for path_key in path_keys:
            if path_key in dataset_config:
                relative_path = dataset_config[path_key]
                absolute_path = project_root / relative_path
                dataset_config[f"{path_key}_resolved"] = str(absolute_path)
                
                # Create directory if it doesn't exist (except for backup paths)
                if path_key != "backup_path":
                    try:
                        absolute_path.mkdir(parents=True, exist_ok=True)
                        logger.debug(f"Ensured path exists: {absolute_path}")
                    except OSError as e:
                        logger.warning(f"Failed to create directory {absolute_path}: {e}")
        
        # Resolve log file paths
        logging_config = self.config.get("logging", {})
        log_files = ["api_log_file", "processing_log_file", "claude_log_file"]
        
        for log_file_key in log_files:
            if log_file_key in logging_config:
                relative_path = logging_config[log_file_key]
                absolute_path = project_root / relative_path
                logging_config[f"{log_file_key}_resolved"] = str(absolute_path)
                
                # Ensure log directory exists
                log_dir = absolute_path.parent
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    logger.warning(f"Failed to create log directory {log_dir}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key path.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'dataset.raw_data_path')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_dataset_paths(self) -> Dict[str, str]:
        """
        Get resolved dataset paths.
        
        Returns:
            Dictionary of dataset paths
        """
        dataset_config = self.config["dataset"]
        return {
            "raw_data": dataset_config.get("raw_data_path_resolved", dataset_config["raw_data_path"]),
            "processed_data": dataset_config.get("processed_data_path_resolved", dataset_config["processed_data_path"]),
            "test_data": dataset_config.get("test_data_path_resolved", dataset_config.get("test_data_path", "data/test_data")),
            "logs": dataset_config.get("logs_path_resolved", dataset_config.get("logs_path", "logs"))
        }
    
    def get_source_detection_patterns(self) -> Dict[str, list]:
        """
        Get XML source detection patterns.
        
        Returns:
            Dictionary with eclaim and shafafiya patterns
        """
        return self.config.get("processing", {}).get("source_detection", {
            "eclaim_patterns": ["dubai_*.xml", "*_eclaim.xml"],
            "shafafiya_patterns": ["abudhabi_*.xml", "*_shafafiya.xml"]
        })
    
    def get_claude_config(self) -> Dict[str, Any]:
        """
        Get Claude analysis configuration.
        
        Returns:
            Claude configuration dictionary
        """
        return self.config.get("claude", {})
    
    def is_claude_enabled(self) -> bool:
        """Check if Claude analysis is enabled."""
        return self.config.get("claude", {}).get("enabled", True)
    
    def get_processing_limits(self) -> Dict[str, Any]:
        """
        Get processing limits and settings.
        
        Returns:
            Processing limits configuration
        """
        processing_config = self.config.get("processing", {})
        return {
            "max_file_size_mb": processing_config.get("max_file_size_mb", 50),
            "batch_size": processing_config.get("batch_size", 10),
            "auto_detect_source": processing_config.get("auto_detect_source", True),
            "default_source": processing_config.get("default_source", "eclaim")
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API server configuration.
        
        Returns:
            API configuration dictionary
        """
        return self.config.get("api", {})
    
    def validate_paths_exist(self) -> Dict[str, bool]:
        """
        Validate that configured paths exist.
        
        Returns:
            Dictionary of path existence status
        """
        paths = self.get_dataset_paths()
        validation_results = {}
        
        for path_name, path_str in paths.items():
            path_obj = Path(path_str)
            validation_results[path_name] = path_obj.exists()
            
            if not path_obj.exists():
                logger.warning(f"Configured path does not exist: {path_name} -> {path_str}")
        
        return validation_results
    
    def reload(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading configuration...")
        self._load_config()
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        Get complete configuration dictionary.
        
        Returns:
            Complete configuration
        """
        return self.config.copy()


# Global configuration instance
_config_loader: Optional[ConfigLoader] = None

def get_config() -> ConfigLoader:
    """
    Get global configuration loader instance.
    
    Returns:
        Global ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def reload_config() -> None:
    """Reload global configuration."""
    global _config_loader
    if _config_loader is not None:
        _config_loader.reload()
    else:
        _config_loader = ConfigLoader()


# Convenience functions
def get_dataset_paths() -> Dict[str, str]:
    """Get dataset paths from configuration."""
    return get_config().get_dataset_paths()

def get_claude_config() -> Dict[str, Any]:
    """Get Claude configuration."""
    return get_config().get_claude_config()

def is_claude_enabled() -> bool:
    """Check if Claude analysis is enabled."""
    return get_config().is_claude_enabled()


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = ConfigLoader()
        print("Configuration loaded successfully!")
        print(f"Environment: {config.environment}")
        print(f"Dataset paths: {config.get_dataset_paths()}")
        print(f"Claude enabled: {config.is_claude_enabled()}")
        print(f"Path validation: {config.validate_paths_exist()}")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")