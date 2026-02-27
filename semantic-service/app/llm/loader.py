from vllm import LLM, SamplingParams
from app.config import settings


class LLMService:
    """
    Local DeepSeek-Coder inference using vLLM engine.
    No OpenAI API.
    Fully local GPU execution.
    """

    def __init__(self):
        print("Loading DeepSeek model locally...")

        # Loads model weights from HuggingFace automatically
        self.llm = LLM(
            model=settings.LLM_MODEL_NAME,
            dtype="auto",
            trust_remote_code=True,
        )

        self.sampling_params = SamplingParams(
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

        print("LLM ready")

    # -----------------------------
    # TEXT GENERATION
    # -----------------------------
    def generate(self, prompt: str) -> str:

        outputs = self.llm.generate(
            [prompt],   # vLLM expects batch input
            self.sampling_params
        )

        return outputs[0].outputs[0].text.strip()

# Singleton class
llm = LLMService()