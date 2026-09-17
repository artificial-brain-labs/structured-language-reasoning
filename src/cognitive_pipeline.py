from dataclasses import dataclass

from .entity_resolver import EntityResolver
from .graph_builder import SemanticGraphBuilder
from .graph_reasoner import SemanticGraphReasoner
from .lexicon import Lexicon
from .ontology import Ontology
from .parser import Parser
from .reasoning_query import GraphQueryReasoner
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
    produced transiently by the single semantic-graph reasoning kernel.
    """

    def __init__(self, user_memory=None, lexicon=None, ontology=None, tcm=None):
        self.lexicon = lexicon or Lexicon()
        self.ontology = ontology or Ontology()
        self.user_memory = user_memory or UserMemory()
        self.tcm = tcm or TransientCommunicationMemory()
        self.parser = Parser(self.lexicon)
        self.resolver = EntityResolver(self.lexicon, self.ontology, self.user_memory)
        relation_schemas = getattr(self.user_memory.relations, "schemas", {})
        self.projector = SemanticGraphProjector(relation_schemas)
        self.builder = SemanticGraphBuilder(self.ontology)
        self.reasoner = SemanticGraphReasoner(self.ontology, relation_schemas)
        self.query_reasoner = GraphQueryReasoner(self.ontology, relation_schemas)

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
                    parsed.relation or self._taxonomic_relation(),
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
        return self.user_memory.find_named_entity(token)

    def _taxonomic_relation(self):
        candidates = [
            (schema.get("priority", 0), name)
            for name, schema in self.user_memory.relations.schemas.items()
            if schema.get("role") == "canonical_taxonomic"
        ]
        if not candidates:
            return None
        highest = max(priority for priority, _ in candidates)
        matches = [name for priority, name in candidates if priority == highest]
        return matches[0] if len(matches) == 1 else None

    def query_is_a(self, subject_name, target_concept):
        graph = self.build_user_graph()
        subject_id = self.user_memory.find_named_entity(subject_name)
        if subject_id is None:
            return None
        return self.query_reasoner.is_a(graph, subject_id, target_concept)
