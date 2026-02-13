"""
Planner Configuration - Multi-provider LLM settings

This module provides configuration for various LLM providers including:
- Commercial APIs: Anthropic, OpenAI, Mistral, Google, Cohere
- Open Source (self-hosted): Ollama, vLLM, Text Generation Inference
- HuggingFace: Inference API and custom endpoints

Open Source Models Supported (safe to fork and customize):
- Llama 3.x (Meta, Apache 2.0-like license)
- Mistral (Apache 2.0)
- Mixtral (Apache 2.0)
- Phi-3 (MIT)
- Gemma (Google, permissive license)
- Qwen (Apache 2.0)
- DeepSeek (MIT)
- StarCoder (BigCode OpenRAIL-M)
- CodeLlama (Meta, community license)
"""
import os
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class PlannerProvider(str, Enum):
    """Supported LLM providers"""
    STUB = "stub"
    # Commercial APIs
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    MISTRAL = "mistral"
    GOOGLE = "google"
    COHERE = "cohere"
    # Open Source / Self-hosted
    GPT_OSS = "gpt_oss"  # HuggingFace Inference API
    OLLAMA = "ollama"    # Local Ollama instance
    VLLM = "vllm"        # vLLM server
    TGI = "tgi"          # Text Generation Inference


class OpenSourceModel(BaseModel):
    """Configuration for an open-source model"""
    id: str
    name: str
    provider: str
    license: str
    parameters: str
    context_length: int
    recommended_for: List[str]
    huggingface_id: Optional[str] = None
    ollama_id: Optional[str] = None


# Curated list of safe, forkable open-source models
SAFE_OPEN_SOURCE_MODELS = [
    # Llama Family (Meta)
    OpenSourceModel(
        id="llama3-70b",
        name="Llama 3 70B",
        provider="Meta",
        license="Llama 3 Community License",
        parameters="70B",
        context_length=8192,
        recommended_for=["general", "coding", "reasoning"],
        huggingface_id="meta-llama/Meta-Llama-3-70B-Instruct",
        ollama_id="llama3:70b",
    ),
    OpenSourceModel(
        id="llama3-8b",
        name="Llama 3 8B",
        provider="Meta",
        license="Llama 3 Community License",
        parameters="8B",
        context_length=8192,
        recommended_for=["general", "fast-inference"],
        huggingface_id="meta-llama/Meta-Llama-3-8B-Instruct",
        ollama_id="llama3",
    ),
    # Mistral Family (Apache 2.0)
    OpenSourceModel(
        id="mistral-7b",
        name="Mistral 7B Instruct",
        provider="Mistral AI",
        license="Apache 2.0",
        parameters="7B",
        context_length=32768,
        recommended_for=["general", "fast-inference", "coding"],
        huggingface_id="mistralai/Mistral-7B-Instruct-v0.3",
        ollama_id="mistral",
    ),
    OpenSourceModel(
        id="mixtral-8x7b",
        name="Mixtral 8x7B",
        provider="Mistral AI",
        license="Apache 2.0",
        parameters="46.7B (MoE)",
        context_length=32768,
        recommended_for=["general", "reasoning", "coding"],
        huggingface_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
        ollama_id="mixtral",
    ),
    OpenSourceModel(
        id="mixtral-8x22b",
        name="Mixtral 8x22B",
        provider="Mistral AI",
        license="Apache 2.0",
        parameters="141B (MoE)",
        context_length=65536,
        recommended_for=["complex-tasks", "reasoning", "coding"],
        huggingface_id="mistralai/Mixtral-8x22B-Instruct-v0.1",
        ollama_id="mixtral:8x22b",
    ),
    # Microsoft Phi (MIT)
    OpenSourceModel(
        id="phi-3-medium",
        name="Phi-3 Medium",
        provider="Microsoft",
        license="MIT",
        parameters="14B",
        context_length=128000,
        recommended_for=["reasoning", "coding", "long-context"],
        huggingface_id="microsoft/Phi-3-medium-128k-instruct",
        ollama_id="phi3:14b",
    ),
    OpenSourceModel(
        id="phi-3-mini",
        name="Phi-3 Mini",
        provider="Microsoft",
        license="MIT",
        parameters="3.8B",
        context_length=128000,
        recommended_for=["fast-inference", "edge-deployment"],
        huggingface_id="microsoft/Phi-3-mini-128k-instruct",
        ollama_id="phi3",
    ),
    # Google Gemma (Apache 2.0)
    OpenSourceModel(
        id="gemma-2-27b",
        name="Gemma 2 27B",
        provider="Google",
        license="Gemma Terms of Use",
        parameters="27B",
        context_length=8192,
        recommended_for=["general", "reasoning"],
        huggingface_id="google/gemma-2-27b-it",
        ollama_id="gemma2:27b",
    ),
    OpenSourceModel(
        id="gemma-2-9b",
        name="Gemma 2 9B",
        provider="Google",
        license="Gemma Terms of Use",
        parameters="9B",
        context_length=8192,
        recommended_for=["general", "fast-inference"],
        huggingface_id="google/gemma-2-9b-it",
        ollama_id="gemma2",
    ),
    # Qwen (Apache 2.0)
    OpenSourceModel(
        id="qwen2-72b",
        name="Qwen 2 72B",
        provider="Alibaba",
        license="Apache 2.0",
        parameters="72B",
        context_length=131072,
        recommended_for=["general", "multilingual", "long-context"],
        huggingface_id="Qwen/Qwen2-72B-Instruct",
        ollama_id="qwen2:72b",
    ),
    OpenSourceModel(
        id="qwen2.5-coder-32b",
        name="Qwen 2.5 Coder 32B",
        provider="Alibaba",
        license="Apache 2.0",
        parameters="32B",
        context_length=131072,
        recommended_for=["coding", "code-generation"],
        huggingface_id="Qwen/Qwen2.5-Coder-32B-Instruct",
        ollama_id="qwen2.5-coder:32b",
    ),
    # DeepSeek (MIT)
    OpenSourceModel(
        id="deepseek-coder-33b",
        name="DeepSeek Coder 33B",
        provider="DeepSeek",
        license="MIT",
        parameters="33B",
        context_length=16384,
        recommended_for=["coding", "code-completion"],
        huggingface_id="deepseek-ai/deepseek-coder-33b-instruct",
        ollama_id="deepseek-coder:33b",
    ),
    OpenSourceModel(
        id="deepseek-v2",
        name="DeepSeek V2",
        provider="DeepSeek",
        license="DeepSeek License",
        parameters="236B (MoE)",
        context_length=128000,
        recommended_for=["general", "reasoning", "coding"],
        huggingface_id="deepseek-ai/DeepSeek-V2-Chat",
        ollama_id="deepseek-v2",
    ),
    # CodeLlama (Meta)
    OpenSourceModel(
        id="codellama-70b",
        name="CodeLlama 70B",
        provider="Meta",
        license="Llama 2 Community License",
        parameters="70B",
        context_length=16384,
        recommended_for=["coding", "code-completion", "code-review"],
        huggingface_id="codellama/CodeLlama-70b-Instruct-hf",
        ollama_id="codellama:70b",
    ),
    # StarCoder (BigCode)
    OpenSourceModel(
        id="starcoder2-15b",
        name="StarCoder2 15B",
        provider="BigCode",
        license="BigCode OpenRAIL-M",
        parameters="15B",
        context_length=16384,
        recommended_for=["coding", "code-completion"],
        huggingface_id="bigcode/starcoder2-15b-instruct-v0.1",
        ollama_id="starcoder2:15b",
    ),
]


def get_safe_models() -> List[OpenSourceModel]:
    """Get list of safe, forkable open-source models"""
    return SAFE_OPEN_SOURCE_MODELS


def get_model_by_id(model_id: str) -> Optional[OpenSourceModel]:
    """Get a specific model by ID"""
    for model in SAFE_OPEN_SOURCE_MODELS:
        if model.id == model_id:
            return model
    return None


def get_models_for_use_case(use_case: str) -> List[OpenSourceModel]:
    """Get models recommended for a specific use case"""
    return [m for m in SAFE_OPEN_SOURCE_MODELS if use_case in m.recommended_for]


class PlannerConfig(BaseModel):
    """Configuration for the LLM planner"""
    provider: PlannerProvider = PlannerProvider.STUB

    # Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    # Google (Gemini)
    google_api_key: Optional[str] = None
    google_model: str = "gemini-1.5-flash"

    # Cohere
    cohere_api_key: Optional[str] = None
    cohere_model: str = "command-r-plus"

    # HuggingFace / GPT-OSS
    hf_api_token: Optional[str] = None
    gpt_oss_model: str = "mistralai/Mistral-7B-Instruct-v0.3"
    gpt_oss_endpoint: Optional[str] = None  # Custom endpoint if self-hosting

    # Mistral API
    mistral_api_key: Optional[str] = None
    mistral_model: str = "mistral-large-latest"

    # Ollama (local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # vLLM (self-hosted)
    vllm_base_url: str = "http://localhost:8000"
    vllm_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    vllm_api_key: Optional[str] = None

    # Text Generation Inference (TGI)
    tgi_base_url: str = "http://localhost:8080"
    tgi_model: str = "mistralai/Mistral-7B-Instruct-v0.3"

    # General settings
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout_seconds: int = 120

    @classmethod
    def from_env(cls) -> "PlannerConfig":
        """Load configuration from environment variables"""
        # Determine provider
        provider_str = os.environ.get("PLANNER_PROVIDER", "").lower()

        if provider_str:
            try:
                provider = PlannerProvider(provider_str)
            except ValueError:
                provider = PlannerProvider.STUB
        else:
            # Auto-detect based on available keys (priority order)
            if os.environ.get("ANTHROPIC_API_KEY"):
                provider = PlannerProvider.ANTHROPIC
            elif os.environ.get("OPENAI_API_KEY"):
                provider = PlannerProvider.OPENAI
            elif os.environ.get("GOOGLE_API_KEY"):
                provider = PlannerProvider.GOOGLE
            elif os.environ.get("MISTRAL_API_KEY"):
                provider = PlannerProvider.MISTRAL
            elif os.environ.get("COHERE_API_KEY"):
                provider = PlannerProvider.COHERE
            elif os.environ.get("HF_API_TOKEN"):
                provider = PlannerProvider.GPT_OSS
            elif os.environ.get("VLLM_BASE_URL"):
                provider = PlannerProvider.VLLM
            elif os.environ.get("TGI_BASE_URL"):
                provider = PlannerProvider.TGI
            elif os.environ.get("OLLAMA_MODEL") or os.environ.get("OLLAMA_BASE_URL"):
                provider = PlannerProvider.OLLAMA
            else:
                provider = PlannerProvider.STUB

        return cls(
            provider=provider,
            # Anthropic
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
            anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            # OpenAI
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            # Google
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            google_model=os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash"),
            # Cohere
            cohere_api_key=os.environ.get("COHERE_API_KEY"),
            cohere_model=os.environ.get("COHERE_MODEL", "command-r-plus"),
            # HuggingFace
            hf_api_token=os.environ.get("HF_API_TOKEN"),
            gpt_oss_model=os.environ.get("GPT_OSS_MODEL", "mistralai/Mistral-7B-Instruct-v0.3"),
            gpt_oss_endpoint=os.environ.get("GPT_OSS_ENDPOINT"),
            # Mistral
            mistral_api_key=os.environ.get("MISTRAL_API_KEY"),
            mistral_model=os.environ.get("MISTRAL_MODEL", "mistral-large-latest"),
            # Ollama
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.environ.get("OLLAMA_MODEL", "llama3"),
            # vLLM
            vllm_base_url=os.environ.get("VLLM_BASE_URL", "http://localhost:8000"),
            vllm_model=os.environ.get("VLLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct"),
            vllm_api_key=os.environ.get("VLLM_API_KEY"),
            # TGI
            tgi_base_url=os.environ.get("TGI_BASE_URL", "http://localhost:8080"),
            tgi_model=os.environ.get("TGI_MODEL", "mistralai/Mistral-7B-Instruct-v0.3"),
            # General
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "2000")),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            timeout_seconds=int(os.environ.get("LLM_TIMEOUT_SECONDS", "120")),
        )

    def get_available_providers(self) -> List[str]:
        """Get list of providers with configured credentials"""
        available = []
        if self.anthropic_api_key:
            available.append("anthropic")
        if self.openai_api_key:
            available.append("openai")
        if self.google_api_key:
            available.append("google")
        if self.mistral_api_key:
            available.append("mistral")
        if self.cohere_api_key:
            available.append("cohere")
        if self.hf_api_token:
            available.append("gpt_oss")
        if self.vllm_base_url != "http://localhost:8000" or self.vllm_api_key:
            available.append("vllm")
        if self.tgi_base_url != "http://localhost:8080":
            available.append("tgi")
        # Ollama is always potentially available (local)
        available.append("ollama")
        available.append("stub")
        return available
