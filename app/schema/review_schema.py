from deep_translator import GoogleTranslator
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Load once at startup, not on every request
SUPPORTED_LANGS = set(GoogleTranslator().get_supported_languages(as_dict=True).values())

class Translation(BaseModel):
    source_language: str = Field(min_length=2, max_length=5)
    
    @field_validator("source_language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        print(f"Validating language code: {v}")
        print(f"Supported languages: {SUPPORTED_LANGS}")
        if v != "auto" and v not in SUPPORTED_LANGS:
            print(f"Unsupported language code: {v}")
            raise ValueError(f"'{v}' is not a supported language code")
        return v

class ReviewRequest(BaseModel):
    text: str = Field(min_length=3, max_length=120)
    productName: str = Field(min_length=1, max_length=64)
    translation: Optional[Translation] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "This product is amazing! It exceeded my expectations.",
                "productName": "SuperWidget 3000",
                "translation": {
                    "source_language": "en"
                }
            }
        }
        
class ReviewResponse(BaseModel):
    message: str
    analysis_result: dict
    review_id: str