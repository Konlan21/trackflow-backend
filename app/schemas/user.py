"""Mirrors accounts/serializers.py."""
import uuid

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.core.security import validate_password_complexity


class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords(self) -> "SignupRequest":
        errors: dict[str, list[str]] = {}

        complexity_errors = validate_password_complexity(self.password)
        if complexity_errors:
            errors["password"] = complexity_errors

        if self.confirm_password != self.password:
            errors["confirm_password"] = ["Passwords do not match"]

        if errors:
            # Raised as a plain ValueError; caught by RequestValidationError
            # handler in app/core/exceptions.py and reshaped into this dict.
            raise ValueError(errors)

        return self


class SignupResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    message: str = "User created successfully"

    model_config = {"from_attributes": True}


class UserProfileRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Used for both PUT (all fields expected) and PATCH (all optional)."""
    email: EmailStr | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access: str
    refresh: str
    id: uuid.UUID
    email: EmailStr
    message: str = "User logged in successfully"


class LogoutRequest(BaseModel):
    refresh: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

    @model_validator(mode="after")
    def check_passwords(self) -> "PasswordChangeRequest":
        errors: dict[str, list[str]] = {}

        complexity_errors = validate_password_complexity(self.new_password)
        if complexity_errors:
            errors["new_password"] = complexity_errors

        if self.confirm_new_password != self.new_password:
            errors["confirm_new_password"] = ["Passwords do not match"]

        if errors:
            raise ValueError(errors)

        return self


class AccountDeleteRequest(BaseModel):
    password: str