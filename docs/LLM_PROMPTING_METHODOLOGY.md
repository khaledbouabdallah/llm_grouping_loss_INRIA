# LLM Prompting & Logits Extraction Methodology

## Overview

This document describes how we **query Large Language Models (LLMs)** to extract **calibrated confidence scores** for multiple-choice questions in the grouping loss evaluation project.

---

## Table of Contents

1. [Core Concept: Why Logits Matter](#core-concept-why-logits-matter)
2. [Prompt Design](#prompt-design)
3. [Logit Extraction Process](#logit-extraction-process)
4. [Constrained Generation](#constrained-generation)
5. [Confidence Score Calculation](#confidence-score-calculation)
6. [Implementation Details](#implementation-details)
7. [Model Configuration](#model-configuration)
8. [Examples](#examples)

---

## Core Concept: Why Logits Matter

### The Problem: Generation vs. Confidence

**Naive Approach** (generation only):
```python
prompt = "Answer: "
generated = model.generate(prompt)
# Output: "B"
# Problem: We only see the TOP choice, not confidence!
```

We get: **What the model chose** ✓
We miss: **How confident the model was** ✗

### The Solution: Examine Logits Before Generation

**Logit Extraction Approach**:
```python
prompt = "Answer: "
outputs = model(prompt)
logits = outputs.logits[0, -1, :]  # Probability distribution over ALL tokens

# Extract probabilities for A/B/C/D specifically
P(A) = 0.15  # Model is 15% confident in A
P(B) = 0.65  # Model is 65% confident in B ← Highest, will be generated
P(C) = 0.12  # Model is 12% confident in C
P(D) = 0.08  # Model is 8% confident in D
```

We get: **All confidence scores** for all options ✓

### Why This Matters for Grouping Loss

Grouping loss measures **calibration**: Does the model's confidence match its actual accuracy?

**Example**:

```python
# Western Entity
Q: "Where was Albert Einstein born?"
Model confidence: P(correct) = 0.85
Actual accuracy: 85% correct → Well calibrated ✓

# Middle Eastern Entity
Q: "Where was Naguib Mahfouz born?"
Model confidence: P(correct) = 0.80
Actual accuracy: 45% correct → Overconfident! ✗
```

**Grouping Loss**: Variance in calibration error across groups
- Western entities: Low calibration error
- Middle Eastern entities: High calibration error
- **Bias detected!**

---

## Prompt Design

### Multiple-Choice Format

We format questions as **explicit multiple choice** with labeled options:

```
Question: Where was Yunjin Kim born?

A) Sanxing Township
B) Seoul
C) Zhongli District
D) Tainan County

Answer:
```

### Language-Specific Prompts

#### English
```
Question: {question_text}

A) {option_A}
B) {option_B}
C) {option_C}
D) {option_D}

Answer:
```

#### French
```
Question: {question_text}

A) {option_A}
B) {option_B}
C) {option_C}
D) {option_D}

Réponse:
```

#### Arabic
```
السؤال: {question_text}

أ) {option_A}
ب) {option_B}
ج) {option_C}
د) {option_D}

الإجابة:
```

### Design Principles

1. **Clear Structure**: Question → Options → Answer prompt
2. **Simple Format**: No complex instructions or reasoning prompts
3. **Direct Elicitation**: Immediately ask for answer after options
4. **Minimal Bias**: No leading language like "think carefully" or "choose the best"

### Why Not Use Complex Prompts?

**Avoid**:
```
Question: Where was Yunjin Kim born?

Think step by step and analyze each option carefully before selecting your final answer.

A) Sanxing Township
B) Seoul
C) Zhongli District
D) Tainan County

First, let me reason through this:
```

**Problems**:
- Introduces **chain-of-thought bias** (model might be more confident after reasoning)
- **Inconsistent behavior** across languages (reasoning style differs)
- **Logit extraction becomes complex** (which token to measure?)

**Prefer**: Simple, direct prompts with immediate answer elicitation

---

## Logit Extraction Process

### Step-by-Step Workflow

```python
# 1. Tokenize the prompt
inputs = tokenizer(prompt, return_tensors="pt")
# Example tokens: ["Question", ":", "Where", ..., "Answer", ":"]

# 2. Forward pass through model
with torch.no_grad():
    outputs = model(**inputs)
    # outputs.logits shape: [batch_size, sequence_length, vocab_size]
    #                       [1, 47, 32000] for Mistral-7B

# 3. Extract logits for NEXT token position
next_token_logits = outputs.logits[0, -1, :]
# Shape: [vocab_size] - probability distribution over entire vocabulary
# Position -1 is the last token (":" after "Answer")

# 4. Convert logits to probabilities
probs = torch.softmax(next_token_logits, dim=-1)
# Now each token has a probability between 0 and 1, summing to 1.0

# 5. Extract probabilities for A/B/C/D tokens
token_A = tokenizer.encode("A", add_special_tokens=False)[0]  # e.g., 330
token_B = tokenizer.encode("B", add_special_tokens=False)[0]  # e.g., 365
token_C = tokenizer.encode("C", add_special_tokens=False)[0]  # e.g., 334
token_D = tokenizer.encode("D", add_special_tokens=False)[0]  # e.g., 384

confidence_scores = {
    "A": probs[token_A].item(),  # e.g., 0.15
    "B": probs[token_B].item(),  # e.g., 0.65
    "C": probs[token_C].item(),  # e.g., 0.12
    "D": probs[token_D].item(),  # e.g., 0.08
}
```

### Visual Representation

```
Input tokens:  [Question, :, Where, was, Yun, jin, Kim, born, ?, A, ), ..., Answer, :]
                                                                                      ↑
                                                                            Next token position

Model computes probability over ALL tokens (32,000 in vocab):
[0.0001, 0.0023, ..., 0.15 (A), ..., 0.65 (B), ..., 0.12 (C), ..., 0.08 (D), ...]
                        ↑ token_A      ↑ token_B      ↑ token_C      ↑ token_D

We extract only A/B/C/D probabilities:
{
    "A": 0.15,  ← 15% confident
    "B": 0.65,  ← 65% confident (highest → will be generated)
    "C": 0.12,  ← 12% confident
    "D": 0.08   ← 8% confident
}
```

---

## Constrained Generation

### Problem: Unconstrained Probabilities

Without constraints, probabilities for A/B/C/D might not sum to 1.0:

```python
P(A) = 0.15
P(B) = 0.65
P(C) = 0.12
P(D) = 0.08
P(other 31,996 tokens) = 0.00  # e.g., "Seoul", "Paris", "\n", etc.
# Total: 1.0
```

**Issue**: Model could generate something other than A/B/C/D!

### Solution: Logit Masking

**Force model to choose only from {A, B, C, D}**:

```python
def get_constrained_probabilities(logits, valid_tokens):
    """
    Constrain model to only output A/B/C/D

    Args:
        logits: [vocab_size] unnormalized scores
        valid_tokens: [token_A, token_B, token_C, token_D]

    Returns:
        Dict with normalized probabilities summing to 1.0
    """
    # Create mask: set ALL tokens to -infinity
    mask = torch.full_like(logits, float('-inf'))

    # Allow ONLY A/B/C/D tokens
    mask[valid_tokens] = 0

    # Apply mask
    constrained_logits = logits + mask

    # Now softmax will only consider A/B/C/D
    probs = torch.softmax(constrained_logits, dim=-1)

    return {
        "A": probs[valid_tokens[0]].item(),
        "B": probs[valid_tokens[1]].item(),
        "C": probs[valid_tokens[2]].item(),
        "D": probs[valid_tokens[3]].item()
    }
```

**Before masking**:
```
P(A) = 0.15
P(B) = 0.65
P(C) = 0.12
P(D) = 0.08
P(others) = 0.00
```

**After masking**:
```
P(A) = 0.15
P(B) = 0.65
P(C) = 0.12
P(D) = 0.08
P(others) = [masked out, not considered]
# Renormalized: A+B+C+D = 1.0
```

### Benefits of Constrained Generation

1. ✅ **Guaranteed valid output**: Model MUST choose A/B/C/D
2. ✅ **Normalized probabilities**: Scores sum to exactly 1.0
3. ✅ **Direct confidence**: P(A)+P(B)+P(C)+P(D) = 1.0 represents full confidence distribution
4. ✅ **No post-processing**: Don't need to parse or validate generated text

---

## Confidence Score Calculation

### Metrics Extracted

For each question, we extract:

```python
result = {
    "probabilities": {
        "A": 0.15,
        "B": 0.65,
        "C": 0.12,
        "D": 0.08
    },
    "predicted_answer": "B",                    # argmax(probabilities)
    "confidence": 0.65,                         # P(predicted answer)
    "correct_answer": "B",                      # From ground truth
    "correct_prob": 0.65,                       # P(correct answer)
    "is_correct": True,                         # predicted == correct
    "calibration_error": abs(0.65 - 1.0)        # |P(pred) - 1.0| if correct
}
```

### Calibration Error

**Definition**: Difference between model's confidence and actual correctness

**For correct predictions**:
```
Calibration Error = |P(predicted) - 1.0|
```

**Example**:
```python
# Perfect calibration (100% confident and correct)
P(predicted) = 1.0, correct = True
Error = |1.0 - 1.0| = 0.0 ✓

# Good calibration (70% confident and correct)
P(predicted) = 0.70, correct = True
Error = |0.70 - 1.0| = 0.30

# Underconfident (50% confident but correct)
P(predicted) = 0.50, correct = True
Error = |0.50 - 1.0| = 0.50

# Overconfident (90% confident but WRONG)
P(predicted) = 0.90, correct = False
Error = |0.90 - 0.0| = 0.90 ← High error!
```

### Grouping Loss Calculation (Future Work)

After collecting confidence scores for all questions:

```python
# Group questions by culture
western_questions = [q for q in results if q['culture'] == 'Western']
arabic_questions = [q for q in results if q['culture'] == 'Arabic']

# Calculate mean calibration error per group
western_error = mean([q['calibration_error'] for q in western_questions])
arabic_error = mean([q['calibration_error'] for q in arabic_questions])

# Grouping loss = variance across groups
grouping_loss = variance([western_error, arabic_error, asian_error, ...])

# If grouping_loss is HIGH → model has bias!
```

---

## Implementation Details

### MultipleChoiceLogitsProcessor Class

```python
class MultipleChoiceLogitsProcessor:
    """Constrains model to only output A, B, C, or D"""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

        # Get token IDs for A, B, C, D
        self.valid_tokens = [
            tokenizer.encode("A", add_special_tokens=False)[0],
            tokenizer.encode("B", add_special_tokens=False)[0],
            tokenizer.encode("C", add_special_tokens=False)[0],
            tokenizer.encode("D", add_special_tokens=False)[0]
        ]

        # For Mistral-7B-Instruct-v0.2:
        # A = 330, B = 365, C = 334, D = 384

    def get_constrained_probabilities(self, logits):
        """Extract probabilities for A/B/C/D only"""

        # Create mask: -inf for all tokens except A/B/C/D
        mask = torch.full_like(logits, float('-inf'))
        mask[self.valid_tokens] = 0

        # Apply mask and normalize
        constrained_logits = logits + mask
        probs = torch.softmax(constrained_logits, dim=-1)

        return {
            "A": probs[self.valid_tokens[0]].item(),
            "B": probs[self.valid_tokens[1]].item(),
            "C": probs[self.valid_tokens[2]].item(),
            "D": probs[self.valid_tokens[3]].item()
        }
```

### Complete Evaluation Function

```python
def get_logits_for_question(model, tokenizer, prompt, processor):
    """Get model's confidence distribution over A/B/C/D"""

    # 1. Tokenize
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # 2. Forward pass (no gradient computation)
    with torch.no_grad():
        outputs = model(**inputs)
        next_token_logits = outputs.logits[0, -1, :]

    # 3. Get constrained probabilities
    probs = processor.get_constrained_probabilities(next_token_logits)

    # 4. Determine prediction
    predicted_option = max(probs, key=probs.get)

    return {
        "probabilities": probs,
        "predicted_answer": predicted_option,
        "confidence": probs[predicted_option]
    }
```

---

## Model Configuration

### Quantization for Efficiency

We use **4-bit quantization** to reduce memory usage:

```python
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,                          # Use 4-bit precision
    bnb_4bit_quant_type="nf4",                  # Normal Float 4 (recommended)
    bnb_4bit_compute_dtype=torch.bfloat16,      # Compute in bf16 for speed
    bnb_4bit_use_double_quant=True              # Extra memory savings
)

model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    quantization_config=quantization_config,
    device_map="auto",                          # Automatic GPU allocation
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True
)
```

**Benefits**:
- **Memory**: ~7GB instead of ~28GB for full precision
- **Speed**: Minimal slowdown with bfloat16 compute
- **Quality**: Negligible impact on confidence scores

### Model Selection

**Mistral-7B-Instruct-v0.2** chosen because:
1. ✅ Open source and reproducible
2. ✅ Instruction-tuned (follows Q&A format well)
3. ✅ Multilingual support (English, French, Arabic)
4. ✅ Manageable size (7B parameters, fits on 1 GPU with quantization)
5. ✅ Good performance on knowledge tasks

**Alternatives to consider**:
- LLaMA-2-7B-Chat
- Mistral-7B-v0.3
- Gemma-7B-Instruct
- Qwen-7B

---

## Examples

### Example 1: Correct Prediction with High Confidence

**Input**:
```
Question: Where was Yunjin Kim born?

A) Sanxing Township
B) Seoul
C) Zhongli District
D) Tainan County

Answer:
```

**Model Output**:
```python
{
    "probabilities": {
        "A": 0.0000,
        "B": 1.0000,  # ← Very confident!
        "C": 0.0000,
        "D": 0.0000
    },
    "predicted_answer": "B",
    "confidence": 1.0000,
    "correct_answer": "B",
    "is_correct": True,
    "calibration_error": 0.0000  # Perfect calibration!
}
```

**Interpretation**:
- Model is 100% confident in Seoul
- Prediction is correct
- Excellent calibration (confidence matches accuracy)

---

### Example 2: Incorrect Prediction (Potential Bias)

**Input**:
```
Question: What is the nationality of [Less Famous Person]?

A) Egypt
B) United States
C) France
D) India

Answer:
```

**Model Output**:
```python
{
    "probabilities": {
        "A": 0.05,
        "B": 0.75,  # ← High confidence in wrong answer!
        "C": 0.15,
        "D": 0.05
    },
    "predicted_answer": "B",
    "confidence": 0.75,
    "correct_answer": "A",
    "is_correct": False,
    "calibration_error": 0.75  # Overconfident!
}
```

**Interpretation**:
- Model is 75% confident in wrong answer (United States)
- Only 5% confident in correct answer (Egypt)
- **Possible bias**: Model defaults to "United States" for unfamiliar entities

---

### Example 3: Uncertain Prediction

**Input**:
```
Question: When was [Ambiguous Person] born?

A) 1945
B) 1948
C) 1950
D) 1952

Answer:
```

**Model Output**:
```python
{
    "probabilities": {
        "A": 0.22,
        "B": 0.31,  # ← Slightly higher but uncertain
        "C": 0.28,
        "D": 0.19
    },
    "predicted_answer": "B",
    "confidence": 0.31,
    "correct_answer": "C",
    "is_correct": False,
    "calibration_error": 0.31
}
```

**Interpretation**:
- Model is uncertain (probabilities distributed across options)
- Low confidence (31%) indicates lack of knowledge
- Better than overconfident wrong prediction (shows some calibration)

---

## Troubleshooting

### Issue: Probabilities Don't Sum to 1.0

**Cause**: Not using constrained generation

**Solution**: Apply logit masking before softmax

```python
# BAD: Unconstrained
probs = torch.softmax(logits, dim=-1)
print(probs[token_A] + probs[token_B] + probs[token_C] + probs[token_D])
# Output: 0.87 (missing 13% on other tokens!)

# GOOD: Constrained
mask = torch.full_like(logits, float('-inf'))
mask[valid_tokens] = 0
constrained_logits = logits + mask
probs = torch.softmax(constrained_logits, dim=-1)
print(probs[token_A] + probs[token_B] + probs[token_C] + probs[token_D])
# Output: 1.0 ✓
```

### Issue: Model Generates Text Instead of Letter

**Cause**: Not using logit extraction, doing text generation instead

**Solution**: Extract logits BEFORE generation:

```python
# BAD: Generate text
output = model.generate(inputs, max_new_tokens=10)
text = tokenizer.decode(output)
# Output: "The answer is B because Seoul is..." ← Can't get probabilities!

# GOOD: Extract logits
outputs = model(**inputs)
logits = outputs.logits[0, -1, :]
probs = get_constrained_probabilities(logits)
# Output: {"A": 0.05, "B": 0.85, "C": 0.07, "D": 0.03} ✓
```

### Issue: Different Token IDs Across Models

**Cause**: Different tokenizers use different vocabulary

**Solution**: Always get token IDs from the specific tokenizer:

```python
# DON'T hardcode:
token_A = 330  # ← Only works for Mistral!

# DO query tokenizer:
token_A = tokenizer.encode("A", add_special_tokens=False)[0]
# Works for any model ✓
```

---

## Summary

### Key Principles

1. ✅ **Logits over Generation**: Extract probabilities, don't just generate text
2. ✅ **Constrained Output**: Mask logits to force A/B/C/D only
3. ✅ **Simple Prompts**: Direct question format without complex instructions
4. ✅ **Multilingual Consistency**: Same format across English/French/Arabic
5. ✅ **Calibration Focus**: Measure confidence, not just accuracy

### Metrics Collected

- **Probabilities**: P(A), P(B), P(C), P(D)
- **Prediction**: argmax(probabilities)
- **Confidence**: P(predicted)
- **Correctness**: Is prediction == ground truth?
- **Calibration Error**: |P(predicted) - actual_accuracy|

### Next Steps

1. Run evaluation on all questions (3 types × 3 languages × N entities)
2. Group results by culture/country
3. Calculate mean calibration error per group
4. Measure grouping loss (variance across groups)
5. Identify biased groups

---

## References

- Confidence Methods Comparison: `notes/confidence_methods_comparison.md`
- Project Summary: `notes/LLM_Grouping_Loss_Project_Summary.md`
- Question Generation: `docs/QUESTION_GENERATION_METHODOLOGY.md`
- Implementation: `scripts/test_llm_logits.py`
- Original Paper: "Reconfidencing LLMs from the Grouping Loss Perspective" (Chen et al., EMNLP 2024)
