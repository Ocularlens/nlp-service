from pydantic import BaseModel, Field

class ReviewRequest(BaseModel):
    text: str = Field(min_length=3, max_length=120)
    productName: str = Field(min_length=1, max_length=64)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "This product is amazing! It exceeded my expectations.",
                "productName": "SuperWidget 3000"
            }
        }
        
class ReviewResponse(BaseModel):
    message: str
    analysis_result: dict
    review_id: str