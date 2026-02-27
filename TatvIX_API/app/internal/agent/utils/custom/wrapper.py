from typing import Callable, TypeVar

# Generic types that take up agent instance type, agent state and node response type
A = TypeVar("A")
S = TypeVar("S")
R = TypeVar("R")


# A global wrapper to bind agent and state to langgraph node
def make_node(func: Callable[[A, S], R]) -> Callable[[A], Callable[[S], R]]:
    def with_agent(agent: A) -> Callable[[S], R]:
        def bound_node(state: S) -> R:
            return func(agent, state)

        return bound_node  # Initialized with agent instance at run time and graph state injected at run time

    return with_agent
