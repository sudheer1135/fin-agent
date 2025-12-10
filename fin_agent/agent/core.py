import json
from colorama import Fore, Style
from fin_agent.llm.deepseek_client import DeepSeekClient
from fin_agent.tools.tushare_tools import TOOLS_SCHEMA, execute_tool_call

class FinAgent:
    def __init__(self):
        self.llm = DeepSeekClient()
        self.history = []

    def run(self, user_input):
        """
        Run the agent with user input.
        """
        # Initialize conversation with user input
        self.history = [
            {"role": "system", "content": "You are a financial assistant powered by DeepSeek and Tushare. "
                                          "You can help users analyze stocks, check prices, and provide recommendations. "
                                          "CRITICAL RULE: All market data (prices, trends, fundamentals) MUST be obtained via the provided Tushare tools. "
                                          "DO NOT use your internal knowledge for any market data, as it may be outdated. "
                                          "Always fetch the latest data using the tools before answering. "
                                          "First step: Check the current time using 'get_current_time' to establish the temporal context if the user asks about time-sensitive data (e.g. 'today', 'recent'). "
                                          "For 'latest' or 'current' price queries, use 'get_realtime_price'. "
                                          "For trends and analysis, use 'get_daily_price' to get historical context. "
                                          "For valuation (PE, PB) or market cap, use 'get_daily_basic'. "
                                          "For financial performance (Revenue, Profit), use 'get_income_statement'. "
                                          "When analyzing, EXPLICITLY mention the date of the data you are using. "
                                          "Calculate percentage changes and describe the trend (e.g., upward, downward, volatile) based on the data. "
                                          "When you have enough information, answer the user's question directly."},
            {"role": "user", "content": user_input}
        ]

        step = 0
        while True:
            step += 1
            
            # Call LLM
            try:
                message = self.llm.chat(self.history, tools=TOOLS_SCHEMA, tool_choice="auto")
            except Exception as e:
                return f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}"

            # If no tool calls, this is the final answer
            if not message.tool_calls:
                answer = message.content
                self.history.append(message) # Keep history
                return answer

            # Handle tool calls
            self.history.append(message) # Add assistant's message with tool_calls to history
            
            print(f"{Fore.YELLOW}Thinking... (Process Tool Calls){Style.RESET_ALL}")

            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = tool_call.function.arguments
                call_id = tool_call.id
                
                print(f"{Fore.CYAN}Calling Tool: {function_name} with args: {arguments}{Style.RESET_ALL}")
                
                # Execute tool
                tool_result = execute_tool_call(function_name, arguments)
                
                # Truncate result if too long for display, but keep full for LLM (context window permitting)
                # For very large dataframes, we might need to summarize, but Tushare daily data for one stock is usually fine.
                display_result = tool_result[:200] + "..." if len(str(tool_result)) > 200 else tool_result
                print(f"{Fore.BLUE}Tool Result: {display_result}{Style.RESET_ALL}")

                # Append tool result to history
                self.history.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": str(tool_result)
                })
