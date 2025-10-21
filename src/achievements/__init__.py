# Initialize achievements package and register built-in rules
# Importing rules modules will register them into the global registry
from .rules import diversity  # noqa: F401
from .rules import rank_up  # noqa: F401
from .rules import streaks  # noqa: F401
