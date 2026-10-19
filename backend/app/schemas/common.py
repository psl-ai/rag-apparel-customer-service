from pydantic import BaseModel


class ApiResponse[DataT](BaseModel):
    request_id: str
    code: str
    message: str
    data: DataT

    @classmethod
    def ok(cls, *, request_id: str, data: DataT) -> "ApiResponse[DataT]":
        return cls(request_id=request_id, code="OK", message="success", data=data)


class HealthStatus(BaseModel):
    status: str
