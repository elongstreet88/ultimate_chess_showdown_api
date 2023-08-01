import logging
import os
from jsonargparse import ArgumentParser, Namespace
from tools.logs.logs import get_logger

# Setup logger. Manually set level to info since this is our settings init
logger = get_logger(__name__, log_level=logging.INFO)

class AppSettings():
    def __init__(self, log_results=False) -> None:
        parser = ArgumentParser(
            default_config_files=["config/config.yaml"],
            env_prefix="UCS",
            default_env=True,
            description="Global App settings"
        )
        parser.add_argument(
            '--redis-url',
            type=str,
            required=True,
            default='redis://localhost:6379',
            help='Redis URL'
        )

        # Parse arguments (note - we skip actual command line arguments)
        self.config:Namespace = parser.parse_args([])

        # Add properties to class to easily access config values
        self.redis_url      = self.config.redis_url

        # Log if requested
        if log_results:
            self._log_config_settings()
    
    def _log_config_settings(self):
        for attr, value in vars(self.config).items():
            if attr.startswith("_") or attr == 'config_source':
                continue
            source = 'DFLT'
            if hasattr(self.config, 'config_source') and self.config.config_source:
                source = 'CNFG'
            elif os.environ.get(f'UCS_{attr.upper()}'):
                source = 'ENVR'
            elif hasattr(self.config, 'args_source') and self.config.args_source:
                source = 'ARGS'

            keywords = ["password", "secret_key", "api_key", "access_token"]
            if value and any(keyword in attr.lower() for keyword in keywords):
                value = '******removed*****'

            logger.info(f"App Settings: [{source}]:[{attr}] -> [{value}]")

# Declare instance of AppSettings that can be imported
app_settings = AppSettings(log_results=True)