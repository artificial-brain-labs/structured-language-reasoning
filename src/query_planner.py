class QueryPlanner:
    """Translate parsed semantic intent into a declarative query plan.

    The planner does not contain linguistic knowledge. It consumes the
    question type and query policy loaded by QueryEngine and returns a small
    execution plan for the graph/query layer.
    """

    def __init__(self, policy):
        self.policy = policy

    def plan(self, parsed):
        policy = self.policy.get(parsed.question_type)
        if policy is None:
            return None

        return {
            "question_type": parsed.question_type,
            "result_kind": policy.get("result_kind"),
            "handler": policy.get("handler"),
            "unknown_result": policy.get("unknown_result"),
            "subject_slot": policy.get("subject_slot", "subject"),
            "object_slot": policy.get("object_slot", "object"),
            "predicate_slot": policy.get("predicate_slot", "verb"),
        }
