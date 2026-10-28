"""Demo FastAPI application showcasing SpecForge interactive client and boundary testing."""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from specforge import SpecForge

app = FastAPI(
    title="Luminara & SpecForge Pet Store API",
    version="1.0.0",
    description="A modern demo API showing automated boundary testing and API exploration.",
)

# One-liner SpecForge mount: replaces default Swagger with modern testing studio
SpecForge(app, path="/docs", theme="dark", title="SpecForge Quality Studio")


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="Unique account username")
    age: int = Field(..., ge=18, le=120, description="User age in years (minimum 18)")
    email: str = Field(..., description="Valid user contact email")
    bio: Optional[str] = Field(None, max_length=150, description="Short bio biography")


@app.post("/api/v1/users", tags=["Users"])
def create_user(user: UserCreate):
    """Create a new user account with strict contract validation."""
    # Demonstrating real-world whitespace bug check:
    # If the user sends pure whitespace "   ", Pydantic accepts it unless custom stripped!
    if user.username.strip() == "":
        raise HTTPException(
            status_code=422,
            detail="Validation Error: 'username' cannot be composed entirely of whitespace characters.",
        )

    return {
        "status": "success",
        "message": f"User '{user.username}' created successfully.",
        "user_id": "usr_99824",
        "email": user.email,
        "age": user.age,
    }


@app.get("/api/v1/users/{user_id}", tags=["Users"])
def get_user(user_id: str):
    """Retrieve user details by user ID."""
    return {
        "user_id": user_id,
        "username": "alice_dev",
        "email": "alice@example.com",
        "age": 28,
        "bio": "Open source API builder",
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting SpecForge Demo at http://localhost:8000/docs ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
