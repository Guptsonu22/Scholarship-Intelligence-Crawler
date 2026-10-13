from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall service status (ok/error)")
    app_name: str = Field(..., description="Name of the backend service")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Active runtime environment")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="UTC server timestamp")


class SystemInfoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str
