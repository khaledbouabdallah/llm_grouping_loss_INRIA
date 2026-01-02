# Grouping Loss Calculation Methodology

## Overview

This document describes how to **calculate grouping loss** from LLM confidence scores to measure **algorithmic bias** across different cultural/linguistic groups.

---

## Table of Contents

1. [What is Grouping Loss?](#what-is-grouping-loss)
2. [Calibration Error](#calibration-error)
3. [Group-Level Analysis](#group-level-analysis)
4. [Grouping Loss Formula](#grouping-loss-formula)
5. [Binned Calibration](#binned-calibration)
6. [Implementation Guide](#implementation-guide)
7. [Interpretation](#interpretation)
8. [Examples](#examples)

---

## What is Grouping Loss?

### Definition

**Grouping Loss** measures the **heterogeneity in calibration quality** across different subgroups of a dataset.

**Key Idea**: Even if a model appears well-calibrated **overall**, it may show **catastrophic miscalibration** for specific groups (e.g., Middle Eastern entities, unpopular figures, historical events).

### Intuition

```
Overall Accuracy: 75% ✓
Overall Calibration: Good ✓

But looking closer:

Western Entities:
  - Confidence: 80%
  - Accuracy: 78%
  - Error: |0.80 - 0.78| = 0.02 ✓ Well calibrated

Middle Eastern Entities:
  - Confidence: 80%
  - Accuracy: 42%
  - Error: |0.80 - 0.42| = 0.38 ✗ Overconfident!

→ Grouping Loss is HIGH (large variance across groups)
→ Model shows BIAS toward Western entities
```

### Brier Score Decomposition (from paper)

The paper shows that total error can be decomposed:

```
Brier Score = Calibration Loss + Grouping Loss + Irreducible Loss
```

Where:
- **Calibration Loss**: Overall average miscalibration
- **Grouping Loss**: Variance in calibration across groups
- **Irreducible Loss**: Inherent task difficulty

**Key insight**: You can have **low calibration loss** (good on average) but **high grouping loss** (biased across groups)!

---

## Calibration Error

### Individual Question Level

For a single question:

```python
calibration_error = abs(predicted_confidence - actual_correctness)

# Example 1: Correct prediction
confidence = 0.85
correct = True (1.0)
error = |0.85 - 1.0| = 0.15

# Example 2: Incorrect prediction
confidence = 0.75
correct = False (0.0)
error = |0.75 - 0.0| = 0.75
```

### Expected Calibration Error (ECE)

Average calibration error across all questions:

```python
def expected_calibration_error(results):
    """
    Calculate average calibration error

    Args:
        results: List of question results with confidence and correctness

    Returns:
        Float: ECE value
    """
    total_error = 0

    for result in results:
        confidence = result['confidence']
        correct = 1.0 if result['is_correct'] else 0.0
        error = abs(confidence - correct)
        total_error += error

    ece = total_error / len(results)
    return ece

# Example
results = [
    {"confidence": 0.85, "is_correct": True},   # error = 0.15
    {"confidence": 0.60, "is_correct": True},   # error = 0.40
    {"confidence": 0.90, "is_correct": False},  # error = 0.90
    {"confidence": 0.30, "is_correct": False},  # error = 0.30
]

ece = (0.15 + 0.40 + 0.90 + 0.30) / 4 = 0.4375
```

### Interpretation of ECE

- **ECE = 0.0**: Perfect calibration (confidence always matches accuracy)
- **ECE < 0.1**: Well calibrated
- **ECE = 0.1-0.3**: Moderate calibration error
- **ECE > 0.3**: Poor calibration (overconfident or underconfident)

---

## Group-Level Analysis

### Defining Groups

Groups can be defined by various attributes:

#### 1. **Culture/Region** (Primary focus)
```python
groups = {
    "Western": ["USA", "France", "Germany", "UK", ...],
    "Arabic": ["Egypt", "Syria", "Saudi Arabia", ...],
    "East Asian": ["China", "Japan", "South Korea", ...],
    "South Asian": ["India", "Pakistan", "Bangladesh", ...],
    "Southeast Asian": ["Thailand", "Vietnam", "Indonesia", ...],
    "African": ["Nigeria", "South Africa", "Ethiopia", ...],
    "Latin American": ["Brazil", "Argentina", "Mexico", ...]
}
```

#### 2. **Language**
```python
groups = ["en", "fr", "ar"]
```

#### 3. **Popularity** (if available)
```python
# Based on Wikipedia pageviews or number of languages
groups = {
    "High": entities with >50 Wikipedia languages,
    "Medium": entities with 10-50 Wikipedia languages,
    "Low": entities with <10 Wikipedia languages
}
```

#### 4. **Question Type**
```python
groups = ["birth_place", "nationality", "birth_date"]
```

### Calculate ECE Per Group

```python
def calculate_group_ece(results, group_key):
    """
    Calculate ECE for each group separately

    Args:
        results: List of all question results
        group_key: Attribute to group by (e.g., 'culture', 'language')

    Returns:
        Dict: {group_name: ece_value}
    """
    groups = {}

    # Group results
    for result in results:
        group = result[group_key]
        if group not in groups:
            groups[group] = []
        groups[group].append(result)

    # Calculate ECE per group
    group_eces = {}
    for group_name, group_results in groups.items():
        group_eces[group_name] = expected_calibration_error(group_results)

    return group_eces

# Example
results = [
    {"confidence": 0.90, "is_correct": True, "culture": "Western"},
    {"confidence": 0.85, "is_correct": True, "culture": "Western"},
    {"confidence": 0.80, "is_correct": False, "culture": "Arabic"},
    {"confidence": 0.75, "is_correct": False, "culture": "Arabic"},
]

group_eces = calculate_group_ece(results, "culture")
# Output: {"Western": 0.125, "Arabic": 0.775}
```

---

## Grouping Loss Formula

### Simple Grouping Loss (Variance)

**Definition**: Variance of ECE across groups

```python
def grouping_loss_simple(group_eces):
    """
    Calculate grouping loss as variance of group ECEs

    Args:
        group_eces: Dict of {group_name: ece_value}

    Returns:
        Float: Grouping loss value
    """
    import numpy as np

    eces = list(group_eces.values())
    mean_ece = np.mean(eces)

    # Variance: E[(ECE - mean)²]
    variance = np.mean([(ece - mean_ece)**2 for ece in eces])

    return variance

# Example
group_eces = {
    "Western": 0.10,
    "Arabic": 0.45,
    "Asian": 0.38,
    "African": 0.42
}

gl = grouping_loss_simple(group_eces)
# Mean ECE = (0.10 + 0.45 + 0.38 + 0.42) / 4 = 0.3375
# Variance = [(0.10-0.34)², (0.45-0.34)², (0.38-0.34)², (0.42-0.34)²] / 4
#          = [0.0576, 0.0121, 0.0016, 0.0064] / 4
#          = 0.0194

# High grouping loss indicates bias!
```

### Interpretation

- **GL ≈ 0**: Uniform calibration across groups (fair)
- **GL < 0.01**: Low heterogeneity (minor differences)
- **GL = 0.01-0.05**: Moderate heterogeneity (noticeable bias)
- **GL > 0.05**: High heterogeneity (significant bias)

### Max Gap Metric (Alternative)

```python
def grouping_loss_maxgap(group_eces):
    """
    Calculate grouping loss as maximum difference between groups

    Simpler interpretation than variance
    """
    eces = list(group_eces.values())
    return max(eces) - min(eces)

# Example
group_eces = {"Western": 0.10, "Arabic": 0.45}
gap = grouping_loss_maxgap(group_eces)
# Output: 0.45 - 0.10 = 0.35

# Interpretation: 35% difference in calibration error!
```

---

## Binned Calibration

### Why Binning?

**Problem**: Comparing ECE across groups can be misleading if confidence distributions differ

**Example**:
```
Group A: All predictions at 90% confidence
Group B: All predictions at 50% confidence

Even with same accuracy, ECE will differ due to confidence levels!
```

**Solution**: Bin by confidence FIRST, then measure within-bin variance

### Binned Calibration Procedure

```python
def binned_grouping_loss(results, num_bins=10):
    """
    Calculate grouping loss within confidence bins

    Args:
        results: List of all question results
        num_bins: Number of confidence bins (default 10)

    Returns:
        Dict with binned metrics
    """
    import numpy as np

    bin_edges = np.linspace(0, 1, num_bins + 1)
    total_gl = 0

    for i in range(num_bins):
        # Define bin
        bin_min = bin_edges[i]
        bin_max = bin_edges[i + 1]

        # Filter results in this confidence bin
        bin_results = [
            r for r in results
            if bin_min <= r['confidence'] < bin_max
        ]

        if len(bin_results) < 2:
            continue  # Skip bins with too few samples

        # Group results by culture within bin
        groups = {}
        for r in bin_results:
            group = r['culture']
            if group not in groups:
                groups[group] = []
            groups[group].append(r)

        # Calculate accuracy per group within bin
        group_accuracies = {}
        for group_name, group_results in groups.items():
            accuracy = sum(r['is_correct'] for r in group_results) / len(group_results)
            group_accuracies[group_name] = accuracy

        # Variance of accuracy across groups (grouping loss for this bin)
        accuracies = list(group_accuracies.values())
        bin_gl = np.var(accuracies)

        total_gl += bin_gl

    return total_gl / num_bins

# Example interpretation:
# Within each confidence bin (e.g., [0.7-0.8]):
# - Western entities: 75% accurate
# - Arabic entities: 45% accurate
# - Variance: high → grouping loss detected!
```

### Benefits of Binned Approach

1. ✅ **Controls for confidence level**: Compares apples to apples
2. ✅ **Detects non-uniform bias**: E.g., bias only at high confidence
3. ✅ **Follows paper methodology**: Direct implementation of Chen et al.
4. ✅ **More robust**: Less sensitive to outliers

---

## Implementation Guide

### Complete Pipeline

```python
import pandas as pd
import numpy as np
from typing import List, Dict

def analyze_grouping_loss(results: List[Dict]) -> Dict:
    """
    Complete grouping loss analysis pipeline

    Args:
        results: List of question results with keys:
            - entity_id
            - culture
            - language
            - question_type
            - confidence
            - is_correct
            - predicted_answer
            - correct_answer

    Returns:
        Dict with comprehensive grouping loss metrics
    """
    df = pd.DataFrame(results)

    # 1. Overall metrics
    overall_accuracy = df['is_correct'].mean()
    overall_ece = calculate_ece(results)

    # 2. Group-level ECE (by culture)
    culture_eces = {}
    for culture in df['culture'].unique():
        culture_results = df[df['culture'] == culture].to_dict('records')
        culture_eces[culture] = calculate_ece(culture_results)

    # 3. Grouping loss metrics
    gl_variance = np.var(list(culture_eces.values()))
    gl_maxgap = max(culture_eces.values()) - min(culture_eces.values())
    gl_binned = binned_grouping_loss(results)

    # 4. By language (multilingual bias)
    language_eces = {}
    for lang in df['language'].unique():
        lang_results = df[df['language'] == lang].to_dict('records')
        language_eces[lang] = calculate_ece(lang_results)

    # 5. By question type
    qtype_eces = {}
    for qtype in df['question_type'].unique():
        qtype_results = df[df['question_type'] == qtype].to_dict('records')
        qtype_eces[qtype] = calculate_ece(qtype_results)

    return {
        "overall": {
            "accuracy": overall_accuracy,
            "ece": overall_ece,
            "num_questions": len(df)
        },
        "culture": {
            "eces": culture_eces,
            "grouping_loss_variance": gl_variance,
            "grouping_loss_maxgap": gl_maxgap,
            "grouping_loss_binned": gl_binned
        },
        "language": {
            "eces": language_eces,
            "grouping_loss_variance": np.var(list(language_eces.values()))
        },
        "question_type": {
            "eces": qtype_eces,
            "grouping_loss_variance": np.var(list(qtype_eces.values()))
        }
    }

def calculate_ece(results):
    """Helper to calculate ECE"""
    errors = [
        abs(r['confidence'] - (1.0 if r['is_correct'] else 0.0))
        for r in results
    ]
    return np.mean(errors)
```

### Usage Example

```python
# After running LLM evaluation on all questions
results = []

for entity_id in entity_ids:
    for question_type in ['birth_place', 'nationality', 'birth_date']:
        for language in ['en', 'fr', 'ar']:
            result = test_question(entity_id, question_type, language)
            results.append(result)

# Analyze grouping loss
analysis = analyze_grouping_loss(results)

# Print report
print(f"Overall Accuracy: {analysis['overall']['accuracy']:.2%}")
print(f"Overall ECE: {analysis['overall']['ece']:.4f}")
print(f"\nCulture-Level ECE:")
for culture, ece in analysis['culture']['eces'].items():
    print(f"  {culture}: {ece:.4f}")
print(f"\nGrouping Loss (Variance): {analysis['culture']['grouping_loss_variance']:.4f}")
print(f"Grouping Loss (Max Gap): {analysis['culture']['grouping_loss_maxgap']:.4f}")
```

---

## Interpretation

### What Different Values Mean

#### Overall ECE

```python
ECE = 0.05  → "Model is well calibrated overall"
ECE = 0.20  → "Model is moderately miscalibrated"
ECE = 0.40  → "Model is poorly calibrated (overconfident)"
```

#### Grouping Loss

```python
GL = 0.001  → "No bias detected (uniform across groups)"
GL = 0.02   → "Minor bias (small differences between groups)"
GL = 0.08   → "Significant bias (large differences between groups)"
GL = 0.15   → "Severe bias (catastrophic for some groups)"
```

#### Max Gap

```python
Gap = 0.05  → "5% difference between best/worst group (minor)"
Gap = 0.20  → "20% difference (moderate bias)"
Gap = 0.40  → "40% difference (severe bias)"
```

### Decision Criteria

**Is there significant grouping loss?**

```python
if grouping_loss_variance > 0.01 or grouping_loss_maxgap > 0.15:
    print("⚠️  Significant bias detected!")
    print("   Model shows different calibration across groups")
    print("   → Further investigation required")
else:
    print("✅ No significant bias")
    print("   Model is uniformly calibrated")
```

---

## Examples

### Example 1: No Bias (Low Grouping Loss)

```python
results = [
    # Western entities (50 questions)
    *[{"confidence": 0.80, "is_correct": True, "culture": "Western"}] * 40,
    *[{"confidence": 0.80, "is_correct": False, "culture": "Western"}] * 10,

    # Arabic entities (50 questions)
    *[{"confidence": 0.80, "is_correct": True, "culture": "Arabic"}] * 39,
    *[{"confidence": 0.80, "is_correct": False, "culture": "Arabic"}] * 11,
]

# Western: 40/50 = 80% accuracy, 80% confidence → ECE ≈ 0.0
# Arabic: 39/50 = 78% accuracy, 80% confidence → ECE ≈ 0.02

# Grouping Loss = variance([0.0, 0.02]) ≈ 0.0001 ← Very low!
# Interpretation: ✅ No bias, model performs similarly on both groups
```

---

### Example 2: Significant Bias (High Grouping Loss)

```python
results = [
    # Western entities (50 questions)
    *[{"confidence": 0.85, "is_correct": True, "culture": "Western"}] * 42,
    *[{"confidence": 0.85, "is_correct": False, "culture": "Western"}] * 8,

    # Arabic entities (50 questions)
    *[{"confidence": 0.85, "is_correct": True, "culture": "Arabic"}] * 22,
    *[{"confidence": 0.85, "is_correct": False, "culture": "Arabic"}] * 28,
]

# Western: 42/50 = 84% accuracy, 85% confidence → ECE ≈ 0.01 ✓
# Arabic: 22/50 = 44% accuracy, 85% confidence → ECE ≈ 0.41 ✗

# Grouping Loss = variance([0.01, 0.41]) = 0.04 ← High!
# Max Gap = 0.41 - 0.01 = 0.40 ← Very high!

# Interpretation: ⚠️ Severe bias!
# Model is well-calibrated for Western entities
# But OVERCONFIDENT (41% error) for Arabic entities
```

---

### Example 3: Language Bias

```python
results = [
    # English questions
    *[{"confidence": 0.90, "is_correct": True, "language": "en"}] * 45,
    *[{"confidence": 0.90, "is_correct": False, "language": "en"}] * 5,

    # Arabic questions (same entities!)
    *[{"confidence": 0.90, "is_correct": True, "language": "ar"}] * 30,
    *[{"confidence": 0.90, "is_correct": False, "language": "ar"}] * 20,
]

# English: 45/50 = 90% accuracy, 90% confidence → ECE = 0.0 ✓
# Arabic: 30/50 = 60% accuracy, 90% confidence → ECE = 0.30 ✗

# Grouping Loss = 0.0225 ← Moderate-to-high

# Interpretation: ⚠️ Language bias detected!
# Same questions, same entities, different language
# Model performs worse in Arabic despite same confidence
```

---

## Visualization

### Calibration Plot

```python
import matplotlib.pyplot as plt

def plot_calibration_by_group(results, group_key='culture'):
    """Plot calibration curves for each group"""

    groups = {}
    for r in results:
        group = r[group_key]
        if group not in groups:
            groups[group] = {'confidences': [], 'accuracies': []}
        groups[group]['confidences'].append(r['confidence'])
        groups[group]['accuracies'].append(1.0 if r['is_correct'] else 0.0)

    plt.figure(figsize=(10, 6))

    for group_name, data in groups.items():
        # Bin by confidence
        bins = np.linspace(0, 1, 11)
        bin_confidences = []
        bin_accuracies = []

        for i in range(len(bins) - 1):
            mask = [(bins[i] <= c < bins[i+1]) for c in data['confidences']]
            if sum(mask) > 0:
                bin_conf = np.mean([c for c, m in zip(data['confidences'], mask) if m])
                bin_acc = np.mean([a for a, m in zip(data['accuracies'], mask) if m])
                bin_confidences.append(bin_conf)
                bin_accuracies.append(bin_acc)

        plt.plot(bin_confidences, bin_accuracies, 'o-', label=group_name)

    # Perfect calibration line
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')

    plt.xlabel('Confidence')
    plt.ylabel('Accuracy')
    plt.title('Calibration by Group')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('calibration_plot.png', dpi=300, bbox_inches='tight')
    plt.show()
```

---

## Summary

### Key Metrics to Report

1. **Overall ECE**: Average calibration error across all questions
2. **Group ECEs**: ECE for each cultural/linguistic group
3. **Grouping Loss (Variance)**: Variance of ECEs across groups
4. **Grouping Loss (Max Gap)**: Difference between best and worst group
5. **Binned Grouping Loss**: Variance within confidence bins

### Steps to Calculate

1. Collect LLM confidence scores for all questions
2. Calculate calibration error for each question
3. Group questions by culture/language/type
4. Calculate ECE per group
5. Compute variance of group ECEs (grouping loss)
6. Optional: Apply binned calibration for robustness

### Interpretation Guidelines

- **Low GL (<0.01)**: Model is fair, no significant bias
- **Medium GL (0.01-0.05)**: Some bias exists, investigate further
- **High GL (>0.05)**: Significant bias, model unreliable for some groups

### Action Items Based on Results

**If grouping loss is high**:
1. Identify which groups have highest ECE
2. Analyze question types where bias is strongest
3. Consider group-specific calibration
4. Document bias in model limitations
5. Investigate root causes (training data imbalance, language bias, etc.)

---

## References

- Original Paper: "Reconfidencing LLMs from the Grouping Loss Perspective" (Chen et al., EMNLP 2024)
- Project Summary: `notes/LLM_Grouping_Loss_Project_Summary.md`
- Confidence Methods: `notes/confidence_methods_comparison.md`
- Question Generation: `docs/QUESTION_GENERATION_METHODOLOGY.md`
- LLM Prompting: `docs/LLM_PROMPTING_METHODOLOGY.md`
