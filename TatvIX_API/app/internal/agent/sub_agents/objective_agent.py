from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import START, END, StateGraph
from langgraph.types import RetryPolicy
from app.internal.agent.utils.states.objective import ObjectiveSchema, ObjectiveAgentSchema, ObjectiveAgentOutputSchema
from app.internal.agent.utils.nodes.objective_agent.build_objective import build_objective

class ObjectiveAgent:
    def __init__(self, llm: ChatGroq | ChatOllama | ChatGoogleGenerativeAI):
        self.retries = 3
        self.objective_llm = llm.with_structured_output(ObjectiveSchema, method='json_schema')
        self.agent_graph: CompiledStateGraph = self._build_agent()
        
    def _build_agent(self) -> CompiledStateGraph:
        """ builds agent graph for execution """
        try:
            if not self.objective_llm:
                raise Exception("Agent initialization Incomplete!")
            
            builder = StateGraph(
                state_schema=ObjectiveAgentSchema,
                output_schema=ObjectiveAgentOutputSchema
            )
            
            builder.add_node(
                "build_objective",
                build_objective(self),
                retry_policy=RetryPolicy(
                    max_attempts=self.retries,
                    initial_interval=1.0,
                    backoff_factor=2.0
                ) # 5 second delay per node retry
            )
            builder.add_edge(START, "build_objective")
            builder.add_edge("build_objective", END)

            graph = builder.compile(checkpointer=True)
            return graph
        except Exception as e:
            raise e
