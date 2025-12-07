"""Decoder-only LLM interface using HuggingFace transformers."""

from typing import List, Optional, Dict, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from .base import LLMInterface
from .confidence.logits import LogitsConfidence


class DecoderLLM(LLMInterface):
    """Decoder-only LLM interface for models like Mistral, LLaMA, GPT-2.

    This class provides a unified interface to decoder-only language models
    with support for confidence extraction via logits.

    Args:
        model_name: HuggingFace model name (e.g., 'gpt2', 'mistralai/Mistral-7B-Instruct-v0.3')
        device: Device to use ('cuda', 'cpu', or 'auto')
        load_in_4bit: Whether to load model in 4-bit quantization
        load_in_8bit: Whether to load model in 8-bit quantization
        confidence_method: Confidence extraction method ('logits')
        **kwargs: Additional arguments for model loading

    Example:
        >>> llm = DecoderLLM(model_name='gpt2', device='cpu')
        >>> responses = llm.generate(["Who is Einstein?"])
        >>> confidences = llm.get_confidence(["Who is Einstein?"], responses)
    """

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        load_in_4bit: bool = False,
        load_in_8bit: bool = False,
        confidence_method: str = "logits",
        **kwargs,
    ):
        self.model_name = model_name
        self.device = device
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Set padding token if not exists
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        model_kwargs = {}
        if load_in_4bit:
            model_kwargs["load_in_4bit"] = True
            model_kwargs["device_map"] = "auto"
        elif load_in_8bit:
            model_kwargs["load_in_8bit"] = True
            model_kwargs["device_map"] = "auto"
        else:
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            model_kwargs["device_map"] = device

        model_kwargs.update(kwargs)

        self.model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)

        # Initialize confidence extractor
        if confidence_method == "logits":
            self.confidence_extractor = LogitsConfidence()
        else:
            raise ValueError(f"Unknown confidence method: {confidence_method}")

    def generate(
        self,
        prompts: List[str],
        max_new_tokens: int = 50,
        temperature: float = 0.7,
        do_sample: bool = True,
        **kwargs,
    ) -> List[str]:
        """Generate responses for prompts.

        Args:
            prompts: List of input prompts
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            do_sample: Whether to use sampling
            **kwargs: Additional generation parameters

        Returns:
            List of generated responses
        """
        # Tokenize inputs
        inputs = self.tokenizer(
            prompts, return_tensors="pt", padding=True, truncation=True
        )

        # Move to device
        if not self.load_in_4bit and not self.load_in_8bit:
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                **kwargs,
            )

        # Decode (only new tokens)
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[:, input_length:]

        responses = self.tokenizer.batch_decode(
            generated_tokens, skip_special_tokens=True
        )

        return responses

    def get_confidence(
        self,
        prompts: List[str],
        responses: List[str],
        max_new_tokens: int = 50,
        **kwargs,
    ) -> List[float]:
        """Extract confidence scores via logits.

        Args:
            prompts: List of input prompts
            responses: List of generated responses (not used for logits method)
            max_new_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            List of confidence scores
        """
        # Tokenize inputs
        inputs = self.tokenizer(
            prompts, return_tensors="pt", padding=True, truncation=True
        )

        # Move to device
        if not self.load_in_4bit and not self.load_in_8bit:
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # Generate with scores
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                output_scores=True,
                return_dict_in_generate=True,
                pad_token_id=self.tokenizer.pad_token_id,
                do_sample=False,  # Greedy for confidence
                **kwargs,
            )

        # Extract confidence from logits
        confidences = self.confidence_extractor.extract(outputs.scores)

        return confidences
