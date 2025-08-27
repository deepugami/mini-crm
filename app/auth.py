from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

STATIC_TOKEN = "demo-token"
security = HTTPBearer(auto_error=False)


class TokenResponse(BaseModel):
	token: str
	token_type: str = "bearer"


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
	if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != STATIC_TOKEN:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
	return "admin"


async def issue_token(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
	# For demo: ignore username/password and return static token
	return TokenResponse(token=STATIC_TOKEN)
