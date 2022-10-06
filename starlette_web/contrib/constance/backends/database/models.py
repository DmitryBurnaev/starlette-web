from sqlalchemy import LargeBinary, Column, String

from starlette_web.common.database import ModelBase, ModelMixin


class Constance(ModelBase, ModelMixin):
    __tablename__ = "constance"

    key = Column(String(length=255), primary_key=True)
    value = Column(LargeBinary(), nullable=True, default="")

    def __str__(self):
        return self.key
