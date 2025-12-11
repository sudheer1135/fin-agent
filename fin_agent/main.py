import sys
import argparse
import subprocess
import re
import os
from importlib.metadata import version, PackageNotFoundError
import colorama
from colorama import Fore, Style
from fin_agent.agent.core import FinAgent
from fin_agent.config import Config

# Initialize colorama
colorama.init()

def get_version():
    try:
        return version("fin-agent")
    except PackageNotFoundError:
        return "unknown (dev)"

def parse_version(v_str):
    """
    Parse a version string into a tuple of integers.
    Example: '0.2.1' -> (0, 2, 1)
             '0.2.1rc1' -> (0, 2, 1)
    """
    if v_str == "unknown (dev)":
        return (0, 0, 0)
    parts = []
    for part in v_str.split('.'):
        if part.isdigit():
            parts.append(int(part))
        else:
            # Handle suffixes like rc1, b1 etc by just taking the leading digits
            match = re.match(r'(\d+)', part)
            if match:
                parts.append(int(match.group(1)))
            else:
                parts.append(0)
    return tuple(parts)

def post_upgrade_hook(old_version_str):
    """
    Hook to be run AFTER the package has been upgraded.
    This runs in the context of the NEW version.
    """
    try:
        new_version_str = get_version()
        print(f"{Fore.CYAN}Running post-upgrade hook... (v{old_version_str} -> v{new_version_str}){Style.RESET_ALL}")
        
        curr_tuple = parse_version(old_version_str)
        new_tuple = parse_version(new_version_str)
        
        # Migration Logic (Now defined in the NEW version)
        # 1. old < 0.2.1 AND new >= 0.2.1 (Config location change)
        target_v2_1 = (0, 2, 1)
        # 2. old < 0.3.4 AND new >= 0.3.4 (Streaming support & multi-model provider structure update)
        target_v3_4 = (0, 3, 4)
        
        need_clear = False
        
        if curr_tuple < target_v2_1 and new_tuple >= target_v2_1:
            need_clear = True
        elif curr_tuple < target_v3_4 and new_tuple >= target_v3_4:
            need_clear = True
            
        if need_clear:
             print(f"{Fore.YELLOW}Major configuration update detected.{Style.RESET_ALL}")
             print(f"{Fore.YELLOW}Clearing old configuration to support new features...{Style.RESET_ALL}")
             Config.clear()
             print(f"{Fore.GREEN}Configuration cleared. Please restart the agent to re-configure.{Style.RESET_ALL}")
        else:
             print(f"{Fore.GREEN}Upgrade complete. No configuration reset needed.{Style.RESET_ALL}")
             
    except Exception as e:
        print(f"{Fore.RED}Error in post-upgrade hook: {e}{Style.RESET_ALL}")

def upgrade_package():
    package_name = "fin-agent"
    
    try:
        current_v_str = version(package_name)
    except PackageNotFoundError:
        print(f"{Fore.YELLOW}Package '{package_name}' not found (installed in development mode?). Cannot auto-upgrade.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}Current version: {current_v_str}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Upgrading {package_name} from PyPI...{Style.RESET_ALL}")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package_name])
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Upgrade failed. Please check your network connection or permissions.{Style.RESET_ALL}")
        return

    # Call the new version's post-upgrade hook
    # We use sys.executable and -m fin_agent.main to ensure we invoke the module from the same python environment
    print(f"{Fore.GREEN}Package installed successfully.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Invoking post-upgrade hook...{Style.RESET_ALL}")
    
    try:
        # Use subprocess to run the NEW code using env vars to pass state
        env = os.environ.copy()
        env["FIN_AGENT_POST_UPGRADE"] = "1"
        env["FIN_AGENT_OLD_VERSION"] = current_v_str
        
        subprocess.check_call([sys.executable, "-m", "fin_agent.main"], env=env)
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Post-upgrade hook failed.{Style.RESET_ALL}")


def run_chat_loop(agent):
    print(f"{Fore.GREEN}Agent initialized successfully.{Style.RESET_ALL}")
    print("Type 'exit' or 'quit' to end the session.")
    
    while True:
        try:
            user_input = input(f"\n{Fore.GREEN}You: {Style.RESET_ALL}").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            response = agent.run(user_input)
            if response: # Only print if there's a response (might be empty if interrupted)
                print(f"\n{Fore.CYAN}Agent: {Style.RESET_ALL}{response}")
            
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            # Use os._exit(0) to immediately terminate without triggering atexit handlers
            # which can cause "Exception ignored in atexit callback" stack traces with colorama on Windows
            os._exit(0)
        except Exception as e:
            print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(
        description="Fin-Agent: A financial analysis AI agent powered by LLMs (DeepSeek/OpenAI) and Tushare data.",
        epilog="Examples:\n  fin-agent                 # Start interactive mode\n  fin-agent --clear-token   # Clear configuration\n  fin-agent --upgrade       # Upgrade to latest version",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-v", "--version", action="store_true", help="Show version number and exit")
    parser.add_argument("--clear-token", action="store_true", help="Clear the existing configuration token and exit.")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade fin-agent to the latest version.")
    
    args = parser.parse_args()

    # Check for internal post-upgrade flag via environment variable
    if os.environ.get("FIN_AGENT_POST_UPGRADE"):
        post_upgrade_hook(os.environ.get("FIN_AGENT_OLD_VERSION", "0.0.0"))
        return

    if args.version:
        print(f"fin-agent version {get_version()}")
        sys.exit(0)

    if args.clear_token:
        print(f"{Fore.YELLOW}Clearing configuration...{Style.RESET_ALL}")
        Config.clear()
        print(f"{Fore.GREEN}Configuration cleared successfully.{Style.RESET_ALL}")
        return

    if args.upgrade:
        upgrade_package()
        return

    print(f"{Fore.GREEN}Welcome to Fin-Agent (v{get_version()})!{Style.RESET_ALL}")
    print("Initializing...")

    agent = None
    try:
        agent = FinAgent()
    except ValueError as e:
        error_msg = str(e)
        if "Missing environment variables" in error_msg:
             print(f"{Fore.YELLOW}Configuration missing or incomplete. Starting setup...{Style.RESET_ALL}")
        else:
             print(f"{Fore.RED}Configuration Error: {error_msg}{Style.RESET_ALL}")
             print(f"{Fore.YELLOW}Running setup...{Style.RESET_ALL}")
        try:
            Config.setup()
            # Retry initialization
            agent = FinAgent()
        except Exception as setup_error:
             print(f"{Fore.RED}Setup failed: {str(setup_error)}{Style.RESET_ALL}")
             return

    if agent:
        run_chat_loop(agent)

if __name__ == "__main__":
    main()
