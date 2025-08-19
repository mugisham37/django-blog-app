"""
API-related Python type definitions
"""

from enum import Enum, IntEnum
from typing import Optional, Dict, Any, List, Generic, TypeVar
from dataclasses import dataclass

from .common_types import PaginationMeta, HttpMethod

T = TypeVar('T')


class HTTPStatus(IntEnum):
    """HTTP status codes"""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


@dataclass
class APIResponse(Generic[T]):
    """Generic API response wrapper"""
    success: bool
    data: T
    message: str
    errors: Optional[Dict[str, List[str]]] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass
class PaginatedResponse(Generic[T]):
    """Paginated API response"""
    success: bool
    data: List[T]
    pagination: PaginationMeta
    message: str
    errors: Optional[Dict[str, List[str]]] = None


@dataclass
class APIError:
    """API error response"""
    success: bool = False
    message: str = ""
    errors: Dict[str, List[str]] = None
    code: Optional[str] = None
    status: Optional[int] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = {}


@dataclass
class APIRequestConfig:
    """API request configuration"""
    method: HttpMethod
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None
    timeout: int = 30
    retries: int = 3


@dataclass
class APIClientConfig:
    """API client configuration"""
    base_url: str
    timeout: int = 30
    retries: int = 3
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class TokenResponse:
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: Optional[str] = None


@dataclass
class TokenRefreshRequest:
    """Token refresh request"""
    refresh_token: str


class APIVersion(str, Enum):
    """API versioning"""
    V1 = "v1"
    V2 = "v2"


@dataclass
class APIEndpoints:
    """API endpoint paths"""
    auth: Dict[str, str]
    blog: Dict[str, str]
    comments: Dict[str, str]
    analytics: Dict[str, str]
    newsletter: Dict[str, str]


@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    limit: int
    remaining: int
    reset: int
    retry_after: Optional[int] = None


@dataclass
class HealthCheckResponse:
    """API health check response"""
    status: str  # healthy, unhealthy, degraded
    checks: Dict[str, bool]
    timestamp: str
    version: str
    uptime: int


@dataclass
class BulkOperationRequest(Generic[T]):
    """Bulk operation request"""
    operation: str  # create, update, delete
    items: List[T]
    options: Optional[Dict[str, Any]] = None


@dataclass
class BulkOperationResult(Generic[T]):
    """Bulk operation result item"""
    item: T
    success: bool
    error: Optional[str] = None


@dataclass
class BulkOperationResponse(Generic[T]):
    """Bulk operation response"""
    success: bool
    processed: int
    failed: int
    results: List[BulkOperationResult[T]]


@dataclass
class SearchRequest:
    """Search request"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[List[Dict[str, str]]] = None
    page: int = 1
    per_page: int = 20
    highlight: bool = False
    facets: Optional[List[str]] = None


@dataclass
class SearchFacet:
    """Search facet result"""
    value: str
    count: int


@dataclass
class SearchResponse(Generic[T]):
    """Search response"""
    results: List[T]
    total: int
    took: int
    facets: Optional[Dict[str, List[SearchFacet]]] = None
    highlights: Optional[Dict[str, List[str]]] = None


@dataclass
class ExportRequest:
    """Export request"""
    format: str  # json, csv, xlsx, pdf
    filters: Optional[Dict[str, Any]] = None
    fields: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None


@dataclass
class ExportResponse:
    """Export response"""
    file_url: str
    file_name: str
    file_size: int
    expires_at: str
    format: str


@dataclass
class ImportRequest:
    """Import request"""
    file_url: str
    format: str  # json, csv, xlsx
    options: Optional[Dict[str, Any]] = None


@dataclass
class ImportResponse:
    """Import response"""
    job_id: str
    status: str  # pending, processing, completed, failed
    processed: int
    total: int
    errors: Optional[List[str]] = None