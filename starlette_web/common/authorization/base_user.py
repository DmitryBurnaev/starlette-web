class BaseUser:
    @property
    def is_authenticated(self) -> bool:
        raise NotImplementedError


class AnonymousUser(BaseUser):
    @property
    def is_authenticated(self) -> bool:
        raise False
