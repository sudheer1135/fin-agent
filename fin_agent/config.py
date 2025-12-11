import os
import sys
import platform
from pathlib import Path
from dotenv import load_dotenv

class Config:
    TUSHARE_TOKEN = None
    LLM_PROVIDER = None
    LLM_STREAM = True
    
    # DeepSeek Config
    DEEPSEEK_API_KEY = None
    DEEPSEEK_BASE_URL = None
    DEEPSEEK_MODEL = None
    
    # Generic OpenAI Config
    OPENAI_API_KEY = None
    OPENAI_BASE_URL = None
    OPENAI_MODEL = None
    
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
        cls.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")
        cls.LLM_STREAM = os.getenv("LLM_STREAM", "True").lower() == "true"
        
        cls.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        cls.DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        cls.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        cls.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
        cls.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    @classmethod
    def validate(cls):
        cls.load() # Ensure latest env is loaded
        missing = []
        if not cls.TUSHARE_TOKEN:
            missing.append("TUSHARE_TOKEN")
            
        if cls.LLM_PROVIDER == "deepseek":
            if not cls.DEEPSEEK_API_KEY:
                missing.append("DEEPSEEK_API_KEY")
        elif cls.LLM_PROVIDER == "openai" or cls.LLM_PROVIDER == "local":
             if not cls.OPENAI_API_KEY and cls.LLM_PROVIDER != "local":
                # For strictly OpenAI provider, key is usually required.
                # For 'local', we might allow empty key if user really wants to, 
                # but standard check:
                pass
        
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    
    @classmethod
    def setup(cls):
        """Interactive setup for environment variables"""
        print("Configuration missing. Starting setup wizard...")
        
        tushare_token = input("Enter your Tushare Token: ").strip()
        
        print("\nSelect LLM Provider:")
        print("1. DeepSeek (Default)")
        print("2. Moonshot (Kimi)")
        print("3. ZhipuAI (GLM-4)")
        print("4. Yi (01.AI)")
        print("5. Qwen (Aliyun DashScope)")
        print("6. SiliconFlow (Aggregator)")
        print("7. Custom (Manual Input)")
        print("8. Local / Self-Hosted (Ollama, LM Studio, etc.)")
        
        choice = input("Enter choice (1-8): ").strip()
        
        provider = "deepseek"
        deepseek_key = ""
        
        openai_key = ""
        openai_base = ""
        openai_model = ""
        
        if choice == "1" or not choice:
            # DeepSeek logic (using specific config variables as before)
            provider = "deepseek"
            deepseek_key = input("Enter DeepSeek API Key: ").strip()
            
        else:
            # All others use the generic OpenAI provider logic
            provider = "openai"
            
            if choice == "2": # Moonshot
                openai_base = "https://api.moonshot.cn/v1"
                default_model = "moonshot-v1-8k"
                print(f"Using Base URL: {openai_base}")
                openai_key = input("Enter Moonshot API Key: ").strip()
                openai_model = input(f"Enter Model Name [default: {default_model}]: ").strip() or default_model
                
            elif choice == "3": # ZhipuAI
                openai_base = "https://open.bigmodel.cn/api/paas/v4"
                default_model = "glm-4"
                print(f"Using Base URL: {openai_base}")
                openai_key = input("Enter ZhipuAI API Key: ").strip()
                openai_model = input(f"Enter Model Name [default: {default_model}]: ").strip() or default_model
                
            elif choice == "4": # Yi
                openai_base = "https://api.lingyiwanwu.com/v1"
                default_model = "yi-34b-chat-0205"
                print(f"Using Base URL: {openai_base}")
                openai_key = input("Enter Yi API Key: ").strip()
                openai_model = input(f"Enter Model Name [default: {default_model}]: ").strip() or default_model
                
            elif choice == "5": # Qwen
                openai_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
                default_model = "qwen-turbo"
                print(f"Using Base URL: {openai_base}")
                openai_key = input("Enter DashScope API Key: ").strip()
                openai_model = input(f"Enter Model Name [default: {default_model}]: ").strip() or default_model
                
            elif choice == "6": # SiliconFlow
                openai_base = "https://api.siliconflow.cn/v1"
                default_model = "deepseek-ai/DeepSeek-V3"
                print(f"Using Base URL: {openai_base}")
                openai_key = input("Enter SiliconFlow API Key: ").strip()
                openai_model = input(f"Enter Model Name [default: {default_model}]: ").strip() or default_model

            elif choice == "8": # Local
                provider = "local"
                default_base = "http://localhost:11434/v1"
                openai_base = input(f"Enter Base URL [default: {default_base}]: ").strip() or default_base
                default_model = "llama3"
                openai_model = input(f"Enter Model Name [default: {default_model}]: ").strip() or default_model
                openai_key = "ollama" # Local models usually don't need a key, setting dummy
                
            else: # Custom
                openai_key = input("Enter API Key: ").strip()
                openai_base = input("Enter Base URL: ").strip()
                openai_model = input("Enter Model Name: ").strip()
        
        config_dir = cls.get_config_dir()
        env_file = cls.get_env_path()
        
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Write to .env file
        with open(env_file, "w") as f: # Use 'w' to create/overwrite clean
            f.write(f"TUSHARE_TOKEN={tushare_token}\n")
            f.write(f"LLM_PROVIDER={provider}\n")
            
            if provider == "deepseek":
                f.write(f"DEEPSEEK_API_KEY={deepseek_key}\n")
                f.write(f"DEEPSEEK_BASE_URL=https://api.deepseek.com\n")
                f.write(f"DEEPSEEK_MODEL=deepseek-chat\n")
            else:
                f.write(f"OPENAI_API_KEY={openai_key}\n")
                f.write(f"OPENAI_BASE_URL={openai_base}\n")
                f.write(f"OPENAI_MODEL={openai_model}\n")
            
        print(f"Configuration saved to {env_file}")
        
        # Check if local .env exists and warn user
        local_env = os.path.join(os.getcwd(), ".env")
        if os.path.exists(local_env):
            print(f"WARNING: A local .env file exists at {local_env}")
            print("This local file might override or conflict with the global configuration.")
        
        # Manually set env vars for current session to ensure immediate availability
        os.environ["TUSHARE_TOKEN"] = tushare_token
        os.environ["LLM_PROVIDER"] = provider
        if provider == "deepseek":
            os.environ["DEEPSEEK_API_KEY"] = deepseek_key
            os.environ["DEEPSEEK_BASE_URL"] = "https://api.deepseek.com"
            os.environ["DEEPSEEK_MODEL"] = "deepseek-chat"
        else:
            os.environ["OPENAI_API_KEY"] = openai_key
            os.environ["OPENAI_BASE_URL"] = openai_base
            os.environ["OPENAI_MODEL"] = openai_model
        
        cls.load()

    @classmethod
    def clear(cls):
        """Clear the configuration file."""
        env_path = cls.get_env_path()
        if os.path.exists(env_path):
            os.remove(env_path)
            print(f"Configuration file removed: {env_path}")
        else:
            print(f"No configuration file found at: {env_path}")
            
        # Also clear local .env if it exists
        local_env = os.path.join(os.getcwd(), ".env")
        if os.path.exists(local_env):
            os.remove(local_env)
            print(f"Local configuration file removed: {local_env}")
            
        # Clear environment variables
        env_vars = [
            "TUSHARE_TOKEN", "LLM_PROVIDER", 
            "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL",
            "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Reset class variables
        cls.TUSHARE_TOKEN = None
        cls.LLM_PROVIDER = None
        cls.DEEPSEEK_API_KEY = None
        cls.DEEPSEEK_BASE_URL = None
        cls.DEEPSEEK_MODEL = None
        cls.OPENAI_API_KEY = None
        cls.OPENAI_BASE_URL = None
        cls.OPENAI_MODEL = None

# Load on module import
Config.load()
