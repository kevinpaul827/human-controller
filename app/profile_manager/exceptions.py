class ProfileError(Exception):
    """Base error for profile storage operations."""


class ProfileNotFoundError(ProfileError):
    """Raised when a requested profile file does not exist."""


class ProfileValidationError(ProfileError):
    """Raised when profile data fails schema validation."""


class ProfileAlreadyExistsError(ProfileError):
    """Raised when creating a profile whose patient_id is already taken."""


class ProfileConflictError(ProfileError):
    """Raised when a profile mutation conflicts with existing data."""
