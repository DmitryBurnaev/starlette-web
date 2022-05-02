class BaseUserMixin:
    @property
    def is_authenticated(self) -> bool:
        raise NotImplementedError


class AnonymousUser(BaseUserMixin):
    @property
    def is_authenticated(self) -> bool:
        raise False
