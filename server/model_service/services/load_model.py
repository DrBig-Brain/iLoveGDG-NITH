import os
import json
import logging
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

# Try relative import first, then absolute import
try:
    from scripts.model import CustomModel
except ImportError:
    try:
        from ..scripts.model import CustomModel
    except ImportError:
        from server.model_service.scripts.model import CustomModel


def load_model():
    MODEL_ID = os.getenv("MODEL_ID", "nvidia/prompt-task-and-complexity-classifier")
    logger.info(f"Loading classifier model from HF: {MODEL_ID}")

    try:
        config_path = hf_hub_download(
            repo_id=MODEL_ID,
            filename="config.json",
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
        logger.info("Successfully loaded NVIDIA prompt classifier model!")
        return model, tokenizer
    except Exception as e:
        logger.warning(
            f"Could not load HuggingFace model ({MODEL_ID}): {e}. "
            "Will activate heuristic classifier fallback."
        )
        return None, None


if __name__ == "__main__":
    m, t = load_model()
    if m:
        print("Model loaded successfully")
    else:
        print("Model loading failed, fallback will be used")
