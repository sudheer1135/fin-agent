import sys
import colorama
from colorama import Fore, Style
from fin_agent.agent.core import FinAgent
from fin_agent.config import Config

# Initialize colorama
colorama.init()

def main():
    print(f"{Fore.CYAN}Welcome to Fin-Agent!{Style.RESET_ALL}")
    
    # Check configuration and setup if needed
    try:
        Config.validate()
    except ValueError:
        print(f"{Fore.YELLOW}Environment variables missing. Initiating setup...{Style.RESET_ALL}")
        Config.setup()

    print("I can help you analyze stocks and provide recommendations using Tushare data and DeepSeek LLM.")
    print("Type 'exit' or 'quit' to end the session.")

    try:
        agent = FinAgent()
    except Exception as e:
         print(f"{Fore.RED}Failed to initialize Agent: {e}{Style.RESET_ALL}")
         sys.exit(1)

    while True:
        try:
            user_input = input(f"\n{Fore.GREEN}You: {Style.RESET_ALL}")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue

            response = agent.run(user_input)
            print(f"\n{Fore.MAGENTA}Agent:{Style.RESET_ALL}\n{response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
