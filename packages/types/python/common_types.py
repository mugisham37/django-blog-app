"""
Common Python type definitions
"""

from enum import Enum
from typing import TypeVar, Generic, Optional, Dict, Any, List, Union
from datetime import datetime
from dataclasses import dataclass


# Generic type variables
T = TypeVar('T')
ID = TypeVar('ID', int, str)


# Base enums
class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Visibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"
    DRAFT = "draft"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NIN = "nin"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    STARTSWITH = "startswith"
    ENDSWITH = "endswith"
    ISNULL = "isnull"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ContentType(str, Enum):
    JSON = "application/json"
    XML = "application/xml"
    HTML = "text/html"
    PLAIN = "text/plain"
    FORM_DATA = "multipart/form-data"
    FORM_URLENCODED = "application/x-www-form-urlencoded"


# Language and locale types
class LanguageCode(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    RU = "ru"
    ZH = "zh"
    JA = "ja"
    KO = "ko"


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"


class CountryCode(str, Enum):
    US = "US"
    CA = "CA"
    GB = "GB"
    DE = "DE"
    FR = "FR"
    IT = "IT"
    ES = "ES"
    JP = "JP"
    AU = "AU"
    BR = "BR"


class TimezoneId(str, Enum):
    UTC = "UTC"
    NEW_YORK = "America/New_York"
    CHICAGO = "America/Chicago"
    DENVER = "America/Denver"
    LOS_ANGELES = "America/Los_Angeles"
    LONDON = "Europe/London"
    PARIS = "Europe/Paris"
    BERLIN = "Europe/Berlin"
    TOKYO = "Asia/Tokyo"
    SHANGHAI = "Asia/Shanghai"
    SYDNEY = "Australia/Sydney"


# Base dataclasses
@dataclass
class BaseEntity:
    """Base entity with common fields"""
    id: int
    created_at: datetime
    updated_at: datetime


@dataclass
class Timestamps:
    """Timestamp fields for entities"""
    created_at: datetime
    updated_at: datetime


@dataclass
class SoftDelete:
    """Soft delete fields"""
    deleted_at: Optional[datetime]
    is_deleted: bool


@dataclass
class PaginationMeta:
    """Pagination metadata"""
    page: int
    pages: int
    per_page: int
    total: int
    has_next: bool
    has_prev: bool


@dataclass
class Sort:
    """Sort configuration"""
    field: str
    order: SortOrder


@dataclass
class Filter:
    """Filter configuration"""
    field: str
    operator: FilterOperator
    value: Any


@dataclass
class SearchParams:
    """Search parameters"""
    q: Optional[str] = None
    page: int = 1
    per_page: int = 20
    sort: Optional[List[Sort]] = None
    filters: Optional[List[Filter]] = None


@dataclass
class FileUpload:
    """File upload information"""
    file: Any  # File object
    name: str
    size: int
    type: str
    url: Optional[str] = None


@dataclass
class ImageDimensions:
    """Image dimensions"""
    width: int
    height: int


@dataclass
class ImageUpload(FileUpload):
    """Image upload with dimensions"""
    dimensions: Optional[ImageDimensions] = None
    alt_text: Optional[str] = None


@dataclass
class KeyValuePair(Generic[T]):
    """Generic key-value pair"""
    key: str
    value: T


# Utility types
Dictionary = Dict[str, Any]
Nullable = Optional[T]
ArrayOrSingle = Union[T, List[T]]


# Validation result
@dataclass
class ValidationResult(Generic[T]):
    """Validation result with data and errors"""
    success: bool
    data: Optional[T] = None
    errors: Optional[List[Dict[str, str]]] = None


# Configuration base class
@dataclass
class BaseConfig:
    """Base configuration class"""
    environment: Environment
    debug: bool
    log_level: LogLevel
    
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    def is_staging(self) -> bool:
        return self.environment == Environment.STAGING


# Error handling
class BusinessLogicError(Exception):
    """Base exception for business logic errors"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BusinessLogicError):
    """Validation-specific errors"""
    pass


class AuthenticationError(BusinessLogicError):
    """Authentication-specific errors"""
    pass


class AuthorizationError(BusinessLogicError):
    """Authorization-specific errors"""
    pass


class NotFoundError(BusinessLogicError):
    """Resource not found errors"""
    pass


class ConflictError(BusinessLogicError):
    """Resource conflict errors"""
    pass


class RateLimitError(BusinessLogicError):
    """Rate limiting errors"""
    pass


# Response wrapper
@dataclass
class Response(Generic[T]):
    """Generic response wrapper"""
    success: bool
    data: Optional[T] = None
    message: str = ""
    errors: Optional[Dict[str, List[str]]] = None
    meta: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_response(cls, data: T, message: str = "Success") -> 'Response[T]':
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_response(cls, message: str, errors: Optional[Dict[str, List[str]]] = None) -> 'Response[None]':
        return cls(success=False, message=message, errors=errors)


# Paginated response
@dataclass
class PaginatedResponse(Generic[T]):
    """Paginated response wrapper"""
    success: bool
    data: List[T]
    pagination: PaginationMeta
    message: str = ""
    errors: Optional[Dict[str, List[str]]] = None
    
    @classmethod
    def create(
        cls,
        data: List[T],
        page: int,
        per_page: int,
        total: int,
        message: str = "Success"
    ) -> 'PaginatedResponse[T]':
        pages = (total + per_page - 1) // per_page
        pagination = PaginationMeta(
            page=page,
            pages=pages,
            per_page=per_page,
            total=total,
            has_next=page < pages,
            has_prev=page > 1
        )
        return cls(
            success=True,
            data=data,
            pagination=pagination,
            message=message
        )