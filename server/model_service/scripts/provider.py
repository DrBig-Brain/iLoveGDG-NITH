import json
from transformers import AutoTokenizer
from huggingface_hub import hf_hub_download
from .model import CustomModel

# create functions for data validation and inference

MODEL_ID = "nvidia/prompt-task-and-complexity-classifier"

# Download NVIDIA's custom config.json
config_path = hf_hub_download(
    repo_id=MODEL_ID,
    filename="config.json"
)

with open(config_path, "r") as f:
    config = json.load(f)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

model = CustomModel(
    target_sizes=config["target_sizes"],
    task_type_map=config["task_type_map"],
    weights_map=config["weights_map"],
    divisor_map=config["divisor_map"],
).from_pretrained(MODEL_ID)

model.eval()

prompt = ["Prompt: Write a Python script that uses a for loop."]

encoded_texts = tokenizer(
    prompt,
    return_tensors="pt",
    add_special_tokens=True,
    max_length=512,
    padding="max_length",
    truncation=True,
)

result = model(encoded_texts)
print(result)
# {'task_type_1': ['Code Generation'], 'task_type_2': ['Text Generation'], 'task_type_prob': [0.767], 'creativity_scope': [0.0826], 'reasoning': [0.0632], 'contextual_knowledge': [0.056], 'number_of_few_shots': [0], 'domain_knowledge': [0.9803], 'no_label_reason': [0.0], 'constraint_ct': [0.5578], 'prompt_complexity_score': [0.27822]}
