from ulid import ULID


def make_uuid():
    """
    Returns a UUID V4 representation for ULID postgres based models

    Example:

    class User(models.Model):
        id = models.UUIDField(primary_key=True, default=make_uuid)
    """
    return ULID().to_uuid4()
