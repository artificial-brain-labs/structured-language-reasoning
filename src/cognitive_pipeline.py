from dataclasses import dataclass

from .entity_resolver import EntityResolver
from .graph_builder import SemanticGraphBuilder
from .graph_reasoner import SemanticGraphReasoner
from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .semantic_projector import SemanticGraphProjector
from .tcm import TransientCommunicationMemory
from .user_memory import UserMemory


@dataclass(frozen=True)
class PipelineResult:
    """Result of one interaction through the SLRM cognitive pipeline."""

    text: str
    parse_status: str
    operation: str | None
    memory_ids: tuple[str, ...]
    observed_edge_count: int


class CognitivePipeline:
    """Coordinate the language, memory, graph, and reasoning layers.

    This class is orchestration only. Linguistic and domain knowledge remains
    in the data files consumed by the component layers. Explicit user facts
    enter UserMemory; observations remain observations; derived knowledge is
    produced transiently by the reasoner.
    """

    def __init__(self, user_memory=None, lexicon=None, ontology=None, tcm=None):
        self.lexicon = lexicon or Lexicon()
        self.ontology = ontology or Ontology()
        self.user_memory = user_memory or UserMemory()
        self.tcm = tcm or TransientCommunicationMemory()
        self.parser = Parser(self.lexicon)
        self.resolver = EntityResolver(self.lexicon, self.ontology, self.user_memory)
        self.projector = SemanticGraphProjector(getattr(self.user_memory.relations, "schemas", {}))
        self.builder = SemanticGraphBuilder(self.ontology)
        self.reasoner = SemanticGraphReasoner(self.ontology)

    def process(self, text, source="USER"):
        interaction = self.tcm.add(text)
        parsed = self.parser.parse(text)
        if parsed.parse_status != "DETERMINED":
            return PipelineResult(text, parsed.parse_status, None, (), 0)

        memory_ids = []
        if parsed.operation == "ASSERT_CLASSIFICATION":
            subject_id = self.resolver.resolve(parsed.subject_word)
            target = self.resolver.resolve_type(parsed.object_word)
            if target is not None:
                target_concept, target_id = target
                memory = self.user_memory.add_memory(
                    subject_id,
                    parsed.relation or "IS_A",
                    target_id,
                    source=source,
                )
                if memory is not None:
                    memory_ids.append(memory.subject + ":" + memory.predicate + ":" + memory.object)

        graph = self.projector.project(
            parsed.semantic_structure,
            source=f"{source}:{interaction.created_at}",
            support=(interaction.created_at,),
            entity_resolver=lambda token, concept: self._resolve_for_projection(token),
        )
        return PipelineResult(
            text=text,
            parse_status=parsed.parse_status,
            operation=parsed.operation,
            memory_ids=tuple(memory_ids),
            observed_edge_count=len(graph.edges),
        )

    def build_user_graph(self):
        return self.builder.build(self.user_memory)

    def reason_about_user(self):
        graph = self.build_user_graph()
        return graph, self.reasoner.reason(graph)

    def _resolve_for_projection(self, token):
        entity = self.user_memory.find_named_entity(token)
        return entity

    def query_is_a(self, subject_name, target_concept):
        graph = self.build_user_graph()
        subject_id = self.user_memory.find_named_entity(subject_name)
        if subject_id is None:
            return None
        from .reasoning_query import GraphQueryReasoner
        return GraphQueryReasoner(self.ontology).is_a(graph, subject_id, target_concept)
