from openai import OpenAI
from fin_agent.config import Config

class DeepSeekClient:
    def __init__(self):
        Config.validate()
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
        self.model = Config.DEEPSEEK_MODEL

    def chat(self, messages, tools=None, tool_choice=None):
        """
        Send a chat completion request to DeepSeek.
        """
        params = {
            "model": self.model,
            "messages": messages,
        }
        
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice

        try:
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            raise e
