class SemanticComposer:
    """Compose a structured semantic representation directly from a parse tree.

    The composer is grammar-driven: production metadata and lexical data determine
    the resulting structure. No sentence-specific linguistic knowledge is encoded
    in procedural code.
    """

    def __init__(self, lexicon, grammar_parser):
        self.lexicon = lexicon
        self.grammar_parser = grammar_parser

    def _lexical_features(self, token):
        entry = self.lexicon.get(token) if self.lexicon else None
        if not entry:
            return {}
        features = {}
        for name in ("base", "aspect", "tense"):
            if entry.get(name) is not None:
                features[name] = entry[name]
        return features

    def compose(self, node, tokens):
        production = self.grammar_parser.production_for(node)

        if node.production_name is None:
            token = tokens[node.start]
            senses = self.lexicon.senses(token) if hasattr(self.lexicon, "senses") else []
            result = {
                "category": node.category,
                "token": token,
                "concept": self.lexicon.concept(token),
                "pos": self.lexicon.pos(token),
                "relation": self.lexicon.relation(token),
                "senses": [
                    {
                        "id": sense.sense_id,
                        "concept": sense.concept,
                        "pos": sense.pos,
                        "definition": sense.definition,
                    }
                    for sense in senses
                ],
            }
            features = self._lexical_features(token)
            if features:
                result["features"] = features
            return result

        children = [self.compose(child, tokens) for child in node.children]
        result = {
            "category": node.category,
            "production": node.production_name,
            "children": children,
        }

        if node.head_index is not None:
            result["head"] = children[node.head_index]

        if production:
            roles = {}
            for role, role_path in production.get("roles", {}).items():
                if isinstance(role_path, list) and len(role_path) == 2 and role_path[1] == "head":
                    index = int(role_path[0])
                    if 0 <= index < len(children):
                        roles[role] = children[index]
            if roles:
                result["roles"] = roles

            semantic_features = production.get("semantic_features")
            if semantic_features:
                result["features"] = dict(semantic_features)

        return result
