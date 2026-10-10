from pydantic import BaseModel, Field
from typing import Optional, Literal

class PromptInputSchema(BaseModel):
    prompt : str = Field(description="The user prompt which needs to be classified")

class ComplexityOutputSchema(BaseModel):
    pass
