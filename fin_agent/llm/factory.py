from fin_agent.config import Config
from fin_agent.llm.deepseek_client import DeepSeekClient
from fin_agent.llm.openai_client import OpenAICompatibleClient

class LLMFactory:
    @staticmethod
    def create_llm():
        provider = Config.LLM_PROVIDER
        
        if provider == "deepseek":
            return DeepSeekClient()
        elif provider == "openai" or provider == "local":
            # Generic OpenAI compatible
            return OpenAICompatibleClient(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_BASE_URL,
                model=Config.OPENAI_MODEL
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

