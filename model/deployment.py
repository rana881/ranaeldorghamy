from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel
import torch
import os

# Define device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define input format
class InputText(BaseModel):
    text: str

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load model and tokenizer once on startup
tokenizer_dir = os.path.join(BASE_DIR,"injection_detection_model", "tokenizer")
model_dir = os.path.join(BASE_DIR,"injection_detection_model", "final_model")

tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
base_model = AutoModelForSequenceClassification.from_pretrained("microsoft/codebert-base", num_labels=2)
model = PeftModel.from_pretrained(base_model, model_dir)
model.to(device)
model.eval()

label_map = {0: "Normal", 1: "Code Injection"}

def predict(text: str) -> dict:
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        pred = torch.argmax(logits, dim=1).item()

    return {
        "prediction": label_map[pred],
        "label_id": pred
    }
