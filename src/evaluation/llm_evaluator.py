"""
LLM evaluation utilities
Load models and evaluate questions with logit extraction
"""

import torch
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

logger = logging.getLogger(__name__)


class LLMEvaluator:
    """Simple LLM evaluator with logit extraction"""

    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        """
        Initialize evaluator

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.valid_tokens = None  # A, B, C, D token IDs

        logger.info(f"LLMEvaluator initialized with model: {model_name}")

    def load_model(self, use_4bit: bool = True):
        """
        Load model and tokenizer

        Args:
            use_4bit: Use 4-bit quantization
        """
        logger.info(f"Loading model: {self.model_name}")

        if use_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name, device_map="auto", torch_dtype=torch.bfloat16
            )

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "left"

        self.model.eval()

        # Get A/B/C/D token IDs
        self.valid_tokens = [
            self.tokenizer.encode("A", add_special_tokens=False)[0],
            self.tokenizer.encode("B", add_special_tokens=False)[0],
            self.tokenizer.encode("C", add_special_tokens=False)[0],
            self.tokenizer.encode("D", add_special_tokens=False)[0],
        ]

        logger.info(f"✓ Model loaded on device: {self.model.device}")
        logger.info(
            f"✓ Answer tokens: A={self.valid_tokens[0]}, B={self.valid_tokens[1]}, "
            f"C={self.valid_tokens[2]}, D={self.valid_tokens[3]}"
        )

    def get_constrained_probabilities(self, logits: torch.Tensor) -> Dict[str, float]:
        """
        Extract probabilities for A/B/C/D only

        Args:
            logits: Model logits [vocab_size]

        Returns:
            Dict with probabilities
        """
        # Create mask: set all tokens to -inf except A/B/C/D
        mask = torch.full_like(logits, float("-inf"))
        mask[self.valid_tokens] = 0

        # Apply mask and get probabilities
        constrained_logits = logits + mask
        probs = torch.softmax(constrained_logits, dim=-1)

        return {
            "A": probs[self.valid_tokens[0]].item(),
            "B": probs[self.valid_tokens[1]].item(),
            "C": probs[self.valid_tokens[2]].item(),
            "D": probs[self.valid_tokens[3]].item(),
        }

    def evaluate_prompt(self, prompt: str) -> Dict:
        """
        Evaluate a single prompt

        Args:
            prompt: Formatted question prompt

        Returns:
            Dict with probabilities and prediction
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")

        # Tokenize
        inputs = self.tokenizer(
            prompt, return_tensors="pt", padding=True, truncation=True, max_length=512
        )
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # Get model output
        with torch.no_grad():
            outputs = self.model(**inputs)
            next_token_logits = outputs.logits[0, -1, :]

            # Get constrained probabilities
            probs = self.get_constrained_probabilities(next_token_logits)

            # Determine prediction
            predicted_option = max(probs, key=probs.get)

            return {
                "probabilities": probs,
                "predicted_answer": predicted_option,
                "confidence": probs[predicted_option],
            }


def format_question_prompt(question_data: Dict, language: str) -> str:
    """
    Format question as prompt

    Args:
        question_data: Question dict with options
        language: Language code

    Returns:
        Formatted prompt
    """
    # Parse options
    options_list = json.loads(question_data["options"])
    options = {opt["letter"]: opt["text"] for opt in options_list}

    if language == "en":
        prompt = f"""Question: {question_data['question_text']}

A) {options['A']}
B) {options['B']}
C) {options['C']}
D) {options['D']}

Answer:"""
    elif language == "fr":
        prompt = f"""Question: {question_data['question_text']}

A) {options['A']}
B) {options['B']}
C) {options['C']}
D) {options['D']}

Réponse:"""
    elif language == "ar":
        prompt = f"""السؤال: {question_data['question_text']}

أ) {options['A']}
ب) {options['B']}
ج) {options['C']}
د) {options['D']}

الإجابة:"""
    else:
        raise ValueError(f"Unsupported language: {language}")

    return prompt


def evaluate_question(
    evaluator: LLMEvaluator, question: Dict, entity_info: Optional[Dict] = None
) -> Dict:
    """
    Evaluate a single question

    Args:
        evaluator: LLMEvaluator instance
        question: Question dict from database
        entity_info: Optional entity metadata

    Returns:
        Dict with evaluation results
    """
    # Format prompt
    prompt = format_question_prompt(question, question["language"])

    # Get model prediction
    result = evaluator.evaluate_prompt(prompt)

    # Check correctness
    is_correct = result["predicted_answer"] == question["correct_answer"]
    correct_prob = result["probabilities"][question["correct_answer"]]

    # Build result
    eval_result = {
        "entity_id": question["entity_id"],
        "question_type": question["question_type"],
        "language": question["language"],
        "correct_answer": question["correct_answer"],
        "ground_truth": question["ground_truth"],
        "predicted_answer": result["predicted_answer"],
        "is_correct": is_correct,
        "probabilities": result["probabilities"],
        "confidence": result["confidence"],
        "correct_prob": correct_prob,
        "calibration_error": abs(result["confidence"] - (1.0 if is_correct else 0.0)),
    }

    # Add entity info if provided
    if entity_info:
        eval_result["culture"] = entity_info.get("culture")
        eval_result["country"] = entity_info.get("country")

    return eval_result


def save_results(
    results: List[Dict],
    model_name: str,
    save_dir: Path,
    metadata: Optional[Dict] = None,
):
    """
    Save evaluation results

    Args:
        results: List of evaluation results
        model_name: Model name
        save_dir: Directory to save results
        metadata: Optional metadata
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_slug = model_name.replace("/", "_")
    filename = f"results_{model_slug}_{timestamp}.pkl"
    filepath = save_dir / filename

    # Prepare data
    data = {
        "results": results,
        "model_name": model_name,
        "timestamp": timestamp,
        "num_results": len(results),
        "metadata": metadata or {},
    }

    # Save
    with open(filepath, "wb") as f:
        pickle.dump(data, f)

    logger.info(f"Saved results to {filepath}")
    logger.info(f"  Number of results: {len(results)}")

    return filepath


def load_results(filepath: Path) -> Dict:
    """
    Load evaluation results

    Args:
        filepath: Path to results file

    Returns:
        Dict with results and metadata
    """
    filepath = Path(filepath)
    logger.info(f"Loading results from {filepath}")

    with open(filepath, "rb") as f:
        data = pickle.load(f)

    logger.info(f"Loaded {len(data['results'])} results")
    logger.info(f"Model: {data['model_name']}")

    return data
