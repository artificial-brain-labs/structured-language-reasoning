from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class Memory:
    subject: str
    predicate: str
    object: str
    status: str = "ASSERTED"
    confidence: float = 1.0
    source: str = "USER"
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    support: list = field(default_factory=list)
    contradictions: list = field(default_factory=list)


class DynamicMemory:
    def __init__(self):
        self.entities = {}
        self.memories = []

    def create_entity(self, concept):
        """Create a new entity for a concept."""
        base = concept.lower()

        count = sum(
            1
            for entity in self.entities.values()
            if entity["concept"] == concept
        ) + 1

        entity_id = f"{base}_{count:03d}"

        self.entities[entity_id] = {
            "concept": concept
        }

        return entity_id

    def find_entity(self, concept):
        """Find an existing entity for a concept or create one."""
        for entity_id, data in self.entities.items():
            if data["concept"] == concept:
                return entity_id

        return self.create_entity(concept)

    def add_memory(
        self,
        subject,
        predicate,
        object_,
        source="USER",
        confidence=1.0,
    ):
        """
        Add a memory to the world model.

        If the exact memory already exists, return the existing memory.

        If an opposite memory exists, mark both memories as conflicted.
        """

        # Check whether this exact memory already exists.
        for memory in self.memories:
            if (
                memory.subject == subject
                and memory.predicate == predicate
                and memory.object == object_
            ):
                return memory

        # Check for contradiction.
        opposite = self.opposite(predicate)

        for index, memory in enumerate(self.memories):
            if (
                memory.subject == subject
                and memory.predicate == opposite
                and memory.object == object_
            ):
                # Mark the existing memory as conflicted.
                memory.status = "CONFLICTED"

                # Create the new conflicting memory.
                new_memory = Memory(
                    subject=subject,
                    predicate=predicate,
                    object=object_,
                    status="CONFLICTED",
                    confidence=confidence,
                    source=source,
                )

                # Record the relationship between contradictory memories.
                memory.contradictions.append(len(self.memories))

                self.memories.append(new_memory)

                return new_memory

        # No contradiction: create a normal asserted memory.
        new_memory = Memory(
            subject=subject,
            predicate=predicate,
            object=object_,
            status="ASSERTED",
            confidence=confidence,
            source=source,
        )

        self.memories.append(new_memory)

        return new_memory

    def opposite(self, predicate):
        """Return the opposite predicate."""
        if predicate == "EATS":
            return "NOT_EATS"

        if predicate == "NOT_EATS":
            return "EATS"

        return f"NOT_{predicate}"

    def query(
        self,
        subject=None,
        predicate=None,
        object_=None,
    ):
        """Return memories matching the supplied criteria."""
        results = []

        for memory in self.memories:
            if subject is not None and memory.subject != subject:
                continue

            if predicate is not None and memory.predicate != predicate:
                continue

            if object_ is not None and memory.object != object_:
                continue

            results.append(memory)

        return results