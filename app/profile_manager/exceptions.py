class ProfileError(Exception):
    pass

class ProfileNotFoundError(ProfileError):
    pass

class ProfileValidationError(ProfileError):
    pass

class ProfileAlreadyExistsError(ProfileError):
    pass

class ProfileConflictError(ProfileError):
    pass
