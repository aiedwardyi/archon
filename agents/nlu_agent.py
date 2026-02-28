from __future__ import annotations
import os
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, KeywordsOptions, SentimentOptions, CategoriesOptions
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


class NLUAgent:
    def __init__(self):
        api_key = os.getenv("WATSON_NLU_API_KEY")
        url = os.getenv("WATSON_NLU_URL")
        self.enabled = bool(api_key and url)
        if self.enabled:
            authenticator = IAMAuthenticator(api_key)
            self.nlu = NaturalLanguageUnderstandingV1(
                version="2022-04-07",
                authenticator=authenticator,
            )
            self.nlu.set_service_url(url)

    def analyze(self, text: str) -> dict:
        fallback = {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "keywords": [],
            "categories": [],
            "domain": "general",
            "frustrated": False,
        }
        if not self.enabled:
            return fallback
        # Watson NLU requires at least 50 chars
        padded = text if len(text) >= 50 else text + " " * (50 - len(text))
        try:
            response = self.nlu.analyze(
                text=padded,
                features=Features(
                    keywords=KeywordsOptions(limit=5),
                    sentiment=SentimentOptions(),
                    categories=CategoriesOptions(limit=3),
                ),
            ).get_result()
            sentiment = response.get("sentiment", {}).get("document", {})
            sentiment_label = sentiment.get("label", "neutral")
            sentiment_score = sentiment.get("score", 0.0)
            keywords = [k["text"] for k in response.get("keywords", [])]
            categories = [
                c["label"].strip("/").split("/")[0]
                for c in response.get("categories", [])
            ]
            domain = categories[0] if categories else "general"
            return {
                "sentiment": sentiment_label,
                "sentiment_score": sentiment_score,
                "keywords": keywords,
                "categories": categories,
                "domain": domain,
                "frustrated": sentiment_score < -0.5,
            }
        except Exception as e:
            print(f"[NLU] Analysis failed (non-fatal): {e}")
            return fallback
