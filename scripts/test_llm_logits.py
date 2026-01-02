# scripts/test_llm_logits.py
"""
Test script to evaluate LLM confidence on multiple-choice questions
Extracts logits for A/B/C/D options to measure calibration for grouping loss analysis
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
import json
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from src.data.database import EntityDatabase
from src.data.question_generator import MultipleChoiceQuestionGenerator
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MultipleChoiceLogitsProcessor:
    """Constrains model to only output A, B, C, or D"""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        # Get token IDs for A, B, C, D
        self.valid_tokens = [
            tokenizer.encode("A", add_special_tokens=False)[0],
            tokenizer.encode("B", add_special_tokens=False)[0],
            tokenizer.encode("C", add_special_tokens=False)[0],
            tokenizer.encode("D", add_special_tokens=False)[0],
        ]
        logger.info(
            f"Valid answer tokens: A={self.valid_tokens[0]}, B={self.valid_tokens[1]}, "
            f"C={self.valid_tokens[2]}, D={self.valid_tokens[3]}"
        )

    def get_constrained_probabilities(self, logits):
        """
        Extract probabilities for A/B/C/D only, normalized to sum to 1.0

        Args:
            logits: Model logits for next token [vocab_size]

        Returns:
            Dict with probabilities for each option
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


def load_model_and_tokenizer(model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
    """Load quantized model for efficient inference"""
    logger.info(f"Loading model: {model_name}")

    # Create quantization config
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    model.eval()

    logger.info(f"✓ Model loaded on device: {model.device}")
    logger.info(f"✓ Model dtype: {model.dtype}")

    return model, tokenizer


def format_question_prompt(question_data: dict, language: str = "en") -> str:
    """
    Format multiple-choice question as a prompt for the LLM

    Args:
        question_data: Question from database with options as JSON string
        language: Language code

    Returns:
        Formatted prompt string
    """
    # Parse options - stored as list of dicts: [{"letter": "A", "text": "...", "entity_id": N}, ...]
    options_list = json.loads(question_data["options"])

    # Convert to dict for easier access: {"A": "text", "B": "text", ...}
    options = {opt["letter"]: opt["text"] for opt in options_list}

    # Build prompt based on language
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


def get_logits_for_question(
    model, tokenizer, prompt: str, processor: MultipleChoiceLogitsProcessor
) -> dict:
    """
    Get model's confidence distribution over A/B/C/D for a question

    Args:
        model: LLM model
        tokenizer: Tokenizer
        prompt: Formatted question prompt
        processor: Logits processor for constraining output

    Returns:
        Dict with probabilities and prediction
    """
    # Tokenize
    inputs = tokenizer(
        prompt, return_tensors="pt", padding=True, truncation=True, max_length=512
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # Get model output
    with torch.no_grad():
        outputs = model(**inputs)

        # Get logits for the last position (where answer would go)
        next_token_logits = outputs.logits[0, -1, :]

        # Get constrained probabilities
        probs = processor.get_constrained_probabilities(next_token_logits)

        # Determine prediction
        predicted_option = max(probs, key=probs.get)

        return {
            "probabilities": probs,
            "predicted_answer": predicted_option,
            "confidence": probs[predicted_option],
        }


def test_single_question(
    db: EntityDatabase,
    entity_id: int,
    question_type: str,
    language: str,
    model,
    tokenizer,
    processor: MultipleChoiceLogitsProcessor,
):
    """Test a single question and display results"""

    # Fetch question from database
    cursor = db.conn.cursor()
    cursor.execute(
        """
        SELECT * FROM questions
        WHERE entity_id = ? AND question_type = ? AND language = ?
    """,
        (entity_id, question_type, language),
    )

    question = cursor.fetchone()
    if not question:
        logger.warning(
            f"Question not found: entity_id={entity_id}, type={question_type}, lang={language}"
        )
        logger.info("Generating questions for this entity...")

        # Generate questions
        generator = MultipleChoiceQuestionGenerator(db)
        stats = generator.generate_all_questions(entity_id)

        logger.info(
            f"Generation results: ✅ Success: {stats['success']} ❌ Failed: {stats['failed']} ⏭️ Skipped: {stats['skipped']}"
        )

        # Try fetching again
        cursor.execute(
            """
            SELECT * FROM questions
            WHERE entity_id = ? AND question_type = ? AND language = ?
        """,
            (entity_id, question_type, language),
        )
        question = cursor.fetchone()

        if not question:
            logger.error(
                f"Question still not found after generation: entity_id={entity_id}, type={question_type}, lang={language}"
            )
            return None

    # Get entity info
    entity = db.get_entity_by_id(entity_id)

    # Format prompt
    prompt = format_question_prompt(question, language)

    # Get logits
    result = get_logits_for_question(model, tokenizer, prompt, processor)

    # Display results
    print("\n" + "=" * 80)
    print(f"QUESTION EVALUATION")
    print("=" * 80)
    print(f"\n📋 Entity: {entity['wikidata_id']}")

    # Get entity label
    cursor.execute(
        "SELECT label FROM entity_labels WHERE entity_id = ? AND language = ?",
        (entity_id, language),
    )
    label_row = cursor.fetchone()
    if label_row:
        print(f"   Name: {label_row['label']}")

    print(f"   Culture: {entity.get('culture', 'N/A')}")
    print(f"   Country: {entity.get('country', 'N/A')}")
    print(f"\n❓ Question Type: {question_type}")
    print(f"   Language: {language}")
    print(f"\n📝 Prompt:")
    print(prompt)

    print(f"\n🎯 Correct Answer: {question['correct_answer']}")
    print(f"   Ground Truth: {question['ground_truth']}")

    print(f"\n🤖 Model Prediction: {result['predicted_answer']}")
    print(f"   Confidence: {result['confidence']:.4f}")

    print(f"\n📊 Probability Distribution:")
    probs = result["probabilities"]
    for option in ["A", "B", "C", "D"]:
        bar_length = int(probs[option] * 40)
        bar = "█" * bar_length
        indicator = "✓" if option == question["correct_answer"] else " "
        star = "⭐" if option == result["predicted_answer"] else "  "
        print(f"   {option}) {probs[option]:.4f} {bar:<40} {indicator} {star}")

    # Evaluation
    is_correct = result["predicted_answer"] == question["correct_answer"]
    print(
        f"\n{'✅' if is_correct else '❌'} Result: {'CORRECT' if is_correct else 'INCORRECT'}"
    )

    # Calibration metrics
    correct_prob = probs[question["correct_answer"]]
    print(f"\n📈 Calibration Metrics:")
    print(f"   P(correct answer) = {correct_prob:.4f}")
    print(f"   P(predicted answer) = {result['confidence']:.4f}")
    print(
        f"   Calibration error = |P(predicted) - 1.0| = {abs(result['confidence'] - 1.0):.4f}"
    )

    print("\n" + "=" * 80 + "\n")

    return {
        "entity_id": entity_id,
        "question_type": question_type,
        "language": language,
        "correct_answer": question["correct_answer"],
        "predicted_answer": result["predicted_answer"],
        "is_correct": is_correct,
        "probabilities": probs,
        "confidence": result["confidence"],
        "correct_prob": correct_prob,
    }


def test_multiple_questions(
    db: EntityDatabase,
    entity_ids: list,
    model,
    tokenizer,
    processor: MultipleChoiceLogitsProcessor,
    question_types: list = None,
    languages: list = None,
):
    """Test multiple questions and return aggregated results"""

    if question_types is None:
        question_types = ["birth_place", "nationality", "birth_date"]
    if languages is None:
        languages = ["en", "fr", "ar"]

    results = []

    for entity_id in entity_ids:
        for question_type in question_types:
            for language in languages:
                try:
                    result = test_single_question(
                        db,
                        entity_id,
                        question_type,
                        language,
                        model,
                        tokenizer,
                        processor,
                    )
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(
                        f"Error testing entity={entity_id}, type={question_type}, lang={language}: {e}"
                    )

    # Aggregate statistics
    if results:
        print("\n" + "=" * 80)
        print("AGGREGATE STATISTICS")
        print("=" * 80)

        total = len(results)
        correct = sum(1 for r in results if r["is_correct"])

        print(f"\nTotal questions: {total}")
        print(f"Correct: {correct} ({correct/total*100:.1f}%)")
        print(f"Incorrect: {total-correct} ({(total-correct)/total*100:.1f}%)")

        avg_confidence = sum(r["confidence"] for r in results) / total
        avg_correct_prob = sum(r["correct_prob"] for r in results) / total

        print(f"\nAverage confidence in prediction: {avg_confidence:.4f}")
        print(f"Average P(correct answer): {avg_correct_prob:.4f}")

        # Group by culture if available
        print("\n" + "-" * 80)
        print("BREAKDOWN BY CULTURE/GROUP:")
        print("-" * 80)

        # This would require fetching entity culture info
        # For now, just show by language
        for lang in languages:
            lang_results = [r for r in results if r["language"] == lang]
            if lang_results:
                correct_lang = sum(1 for r in lang_results if r["is_correct"])
                avg_conf_lang = sum(r["confidence"] for r in lang_results) / len(
                    lang_results
                )
                print(
                    f"\n{lang.upper()}: {correct_lang}/{len(lang_results)} correct ({correct_lang/len(lang_results)*100:.1f}%)"
                )
                print(f"   Avg confidence: {avg_conf_lang:.4f}")

    return results


def main():
    """Main execution"""
    # Initialize database
    db_path = "data/entities.db"
    if not Path(db_path).exists():
        logger.error(f"Database not found at {db_path}")
        logger.error(
            "Please generate questions first using generate_questions.people.py"
        )
        return

    db = EntityDatabase(db_path)

    # Load model
    model, tokenizer = load_model_and_tokenizer()
    processor = MultipleChoiceLogitsProcessor(tokenizer)

    # Test single question
    logger.info("Testing single question...")
    test_single_question(
        db=db,
        entity_id=1,  # Dwayne Johnson
        question_type="birth_place",
        language="en",
        model=model,
        tokenizer=tokenizer,
        processor=processor,
    )

    # Test multiple questions (uncomment to test more)
    logger.info("Testing multiple questions...")
    results = test_multiple_questions(
        db=db,
        entity_ids=[1, 2, 3],
        model=model,
        tokenizer=tokenizer,
        processor=processor,
        languages=["en"],  # Start with English only
    )

    logger.info("Test complete!")


if __name__ == "__main__":
    main()
