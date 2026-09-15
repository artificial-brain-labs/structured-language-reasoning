class OperationRegistry:
    """Registry mapping mechanism-level operation names to executor handlers.

    Operation names are interface identifiers, not domain knowledge. Domain
    concepts and relations are supplied by the operation data and memory
    schemas; this registry only selects execution mechanisms.
    """

    def __init__(self):
        self._handlers = {}

    def register(self, name, handler):
        self._handlers[name] = handler

    def get(self, name):
        return self._handlers.get(name)
