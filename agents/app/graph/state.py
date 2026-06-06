from typing import Annotated
from langgraph.graph.message import add_messages
from shared.schemas import GTMState as _GTMState

class GTMState(_GTMState):
    messages: Annotated[list, add_messages] = []
