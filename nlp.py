from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "google/mt5-small"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    use_fast=False
)

model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

summarizer = pipeline(
    "summarization",
    model=model,
    tokenizer=tokenizer
)

sentiment_model = pipeline(
    "sentiment-analysis",
    model="CAMeL-Lab/bert-base-arabic-camelbert-da-sentiment"
)

def summarize(text, max_len=120):
    if not text or len(text) < 200:
        return text
    return summarizer(
        text,
        max_length=max_len,
        min_length=40,
        do_sample=False
    )[0]["summary_text"]

def sentiment(text):
    if not text:
        return {"label": "NEUTRAL", "score": 0.0}
    return sentiment_model(text[:512])[0]