class MockLLM:
    """Deterministic mock LLM for TEST_MODE supporting generation, rewrite, and evaluation.

    This mock tracks invocation counts per normalized question to simulate regeneration.
    """

    invocation_counts = {}

    def _norm_q(self, prompt: str) -> str:
        return str(prompt).strip().lower()

    def invoke(self, prompt):
        q = self._norm_q(prompt)

        # Increment invocation count for this prompt to simulate retries/regenerations
        self.invocation_counts[q] = self.invocation_counts.get(q, 0) + 1
        count = self.invocation_counts[q]

        # Rewriting prompt detection
        if "rewrite" in q or "rewrit" in q or "rewriting" in q:

            class R:
                pass

            r = R()
            # Very small heuristic mapping
            if "what is the policy" in q or "what is the policy?" in q:
                r.rewritten_query = "What is the work from home policy?"
            else:
                r.rewritten_query = q
            return r

        # Evaluation prompt detection
        if "evaluate" in q or "answer score" in q or "documents" in q:

            class E:
                def __init__(self, total):
                    self.total_score = total

                def model_dump(self):
                    return {"total_score": self.total_score}

            # For first evaluation return low score to trigger regeneration, then high
            if count == 1:
                return E(40)
            return E(90)

        # Generation prompt
        class G:
            pass

        g = G()
        # If the prompt/question explicitly asks for work from home, return canonical answer
        if "work from home" in q or "what is the work from home policy" in q:
            g.content = "Employees may work remotely three days per week."
            g.total_score = 95
            g.hallucination_result = "supported"
        else:
            # Simulate regeneration improving the response after the first invocation
            if count == 1:
                g.content = "A short low-quality answer."
                g.total_score = 40
                g.hallucination_result = "uncertain"
            else:
                g.content = "Employees may work remotely three days per week."
                g.total_score = 92
                g.hallucination_result = "supported"

        return g
