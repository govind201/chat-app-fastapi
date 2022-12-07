import datetime
from typing import List
from pydantic import BaseModel
from enum import Enum


class UserRequest(BaseModel):
    username: str
    email: str

class UserAuth(BaseModel):
  id: int
  username: str
  email: str



class UserDisplay(BaseModel):
    username: str
    email: str
    date_created: datetime.datetime

    class Config():
        orm_mode = True