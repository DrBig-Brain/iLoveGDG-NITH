import re
from typing import Dict, Any, List


def heuristic_classify_prompt(prompt: str) -> Dict[str, Any]:
    """
    Fast, reliable rule-based classifier used as an instant fallback
    when HuggingFace weights are downloading or running offline.
    Matches the schema of nvidia/prompt-task-and-complexity-classifier.
    """
    clean_p = prompt.strip().lower()
    word_count = len(clean_p.split())
    has_code_syntax = bool(re.search(r"```|def |class |import |function|return |var |let |const |SELECT |WHERE ", prompt))
    has_math_syntax = bool(re.search(r"\\frac|\\int|proof|theorem|lemma|matrix|\+|\-|\*|\/|=|\^", prompt)) and any(w in clean_p for w in ["prove", "solve", "calculate", "derivative", "integral", "equation"])

    # Task type detection
    if has_code_syntax or any(w in clean_p for w in ["code", "script", "algorithm", "debug", "refactor", "implement", "function"]):
        task_1 = "Code Generation"
        task_2 = "Text Generation"
        task_prob = [0.85, 0.12]
        domain_knowledge = 0.85
        reasoning = 0.65
        creativity = 0.15
        constraint = 0.60
    elif has_math_syntax or any(w in clean_p for w in ["prove", "theorem", "lemma", "step-by-step logic", "logical reasoning", "deduce"]):
        task_1 = "Reasoning"
        task_2 = "Problem Solving"
        task_prob = [0.90, 0.08]
        domain_knowledge = 0.88
        reasoning = 0.92
        creativity = 0.10
        constraint = 0.70
    elif any(w in clean_p for w in ["write a story", "write a poem", "brainstorm", "compose", "creative writing", "dialogue", "roleplay"]):
        task_1 = "Creative Writing"
        task_2 = "Brainstorming"
        task_prob = [0.88, 0.10]
        domain_knowledge = 0.20
        reasoning = 0.25
        creativity = 0.90
        constraint = 0.30
    elif any(w in clean_p for w in ["summarize", "tldr", "synopsis", "key takeaways", "extract"]):
        task_1 = "Summarization"
        task_2 = "Information Extraction"
        task_prob = [0.82, 0.15]
        domain_knowledge = 0.35
        reasoning = 0.40
        creativity = 0.10
        constraint = 0.45
    else:
        # Default question answering / information lookup
        task_1 = "Question Answering"
        task_2 = "Information Extraction"
        task_prob = [0.89, 0.08]
        domain_knowledge = 0.15 if word_count < 15 else 0.45
        reasoning = 0.10 if word_count < 15 else 0.35
        creativity = 0.05
        constraint = 0.05 if word_count < 15 else 0.25

    # Contextual knowledge & few shots
    contextual_knowledge = 0.10 if word_count < 30 else 0.50
    number_of_few_shots = 0.0

    # Complexity score calculation (similar to NVIDIA formula)
    # NVIDIA formula: 0.35 * creativity + 0.25 * reasoning + 0.15 * constraint + 0.15 * domain_knowledge + 0.05 * contextual + 0.05 * few_shots
    # Length adjustment
    length_penalty = min(0.35, word_count / 150.0)
    base_complexity = (
        0.35 * creativity
        + 0.25 * reasoning
        + 0.15 * constraint
        + 0.15 * domain_knowledge
        + 0.05 * contextual_knowledge
        + 0.05 * number_of_few_shots
    )
    final_complexity = min(0.99, round(base_complexity + (length_penalty * 0.2), 4))

    return {
        "task_type_1": [task_1],
        "task_type_2": [task_2],
        "task_type_prob": task_prob,
        "creativity_scope": [round(creativity, 4)],
        "reasoning": [round(reasoning, 4)],
        "contextual_knowledge": [round(contextual_knowledge, 4)],
        "number_of_few_shots": [round(number_of_few_shots, 4)],
        "domain_knowledge": [round(domain_knowledge, 4)],
        "no_label_reason": [0.0],
        "constraint_ct": [round(constraint, 4)],
        "prompt_complexity_score": [final_complexity],
    }
