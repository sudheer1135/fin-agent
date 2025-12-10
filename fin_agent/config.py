import os
import sys
import platform
from pathlib import Path
from dotenv import load_dotenv

class Config:
    TUSHARE_TOKEN = None
    DEEPSEEK_API_KEY = None
    DEEPSEEK_BASE_URL = None
    DEEPSEEK_MODEL = None
    
    @staticmethod
    def get_config_dir():
        """Get the configuration directory based on the operating system."""
        app_name = "fin-agent"
        
        if platform.system() == "Windows":
            base_dir = os.getenv("APPDATA")
            if not base_dir:
                base_dir = os.path.expanduser("~")
            config_dir = os.path.join(base_dir, app_name)
        else:
            # Linux/Mac (XDG standard)
            base_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            config_dir = os.path.join(base_dir, app_name)
            
        return config_dir

    @staticmethod
    def get_env_path():
        """Get the full path to the .env file."""
        return os.path.join(Config.get_config_dir(), ".env")

    @classmethod
    def load(cls):
        # Explicitly define path to ensure we are loading the right file
        env_path = cls.get_env_path()
        
        # Also try loading from current directory for local overrides/dev
        local_env = os.path.join(os.getcwd(), ".env")
        if os.path.exists(local_env):
            load_dotenv(local_env, override=True)
            
        # Load from user config dir
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
        
        cls.TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")
        cls.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        cls.DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        cls.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    @classmethod
    def validate(cls):
        cls.load() # Ensure latest env is loaded
        missing = []
        if not cls.TUSHARE_TOKEN:
            missing.append("TUSHARE_TOKEN")
        if not cls.DEEPSEEK_API_KEY:
            missing.append("DEEPSEEK_API_KEY")
        
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    
    @classmethod
    def setup(cls):
        """Interactive setup for environment variables"""
        print("Configuration missing. Starting setup wizard...")
        
        tushare_token = input("Enter your Tushare Token: ").strip()
        deepseek_key = input("Enter your DeepSeek API Key: ").strip()
        
        config_dir = cls.get_config_dir()
        env_file = cls.get_env_path()
        
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Write to .env file
        with open(env_file, "w") as f: # Use 'w' to create/overwrite clean
            f.write(f"TUSHARE_TOKEN={tushare_token}\n")
            f.write(f"DEEPSEEK_API_KEY={deepseek_key}\n")
            f.write(f"DEEPSEEK_BASE_URL=https://api.deepseek.com\n")
            f.write(f"DEEPSEEK_MODEL=deepseek-chat\n")
            
        print(f"Configuration saved to {env_file}")
        
        # Manually set env vars for current session to ensure immediate availability
        os.environ["TUSHARE_TOKEN"] = tushare_token
        os.environ["DEEPSEEK_API_KEY"] = deepseek_key
        os.environ["DEEPSEEK_BASE_URL"] = "https://api.deepseek.com"
        os.environ["DEEPSEEK_MODEL"] = "deepseek-chat"
        
        cls.load()

# Load on module import
Config.load()
