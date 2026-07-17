"""
Milestone 4: IntentClassifier
"""
import re
from enum import Enum


class Intent(Enum):
    GREETING = "greeting"
    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    IMPLEMENTATION = "implementation"
    PLANNING = "planning"
    CONVERSATION = "conversation"


class IntentClassifier:
    def should_query_memory(self, intent: Intent) -> bool:
        """Return True if memory retrieval needed."""
        return intent in {
            Intent.ARCHITECTURE,
            Intent.BUG_FIX,
            Intent.IMPLEMENTATION,
            Intent.PLANNING,
        }
    
    def classify(self, task: str) -> Intent:
        """Classify task intent (fast rule-based)."""
        task_lower = task.lower()
        
        # Greeting patterns
        if re.match(r"^(hi|hello|hey|thanks|thank you|please|sorry)", task_lower):
            return Intent.GREETING
        
        # Architecture patterns
        if any(word in task_lower for word in ["architecture", "design", "structure", "component", "how does"]):
            return Intent.ARCHITECTURE
        
        # Bug fix patterns
        if any(word in task_lower for word in ["bug", "fix", "error", "crash", "debug", "issue", "broken"]):
            return Intent.BUG_FIX
        
        # Implementation patterns
        if any(word in task_lower for word in ["implement", "create", "build", "develop", "add", "write"]):
            return Intent.IMPLEMENTATION
        
        # Planning patterns
        if any(word in task_lower for word in ["plan", "organize", "refactor", "design"]):
            return Intent.PLANNING
        
        return Intent.CONVERSATION


if __name__ == "__main__":
    print("Testing Milestone 4: IntentClassifier")
    
    classifier = IntentClassifier()
    
    # Test greetings - should SKIP memory
    assert classifier.classify("Hi there") == Intent.GREETING
    assert classifier.classify("Thanks!") == Intent.GREETING
    assert not classifier.should_query_memory(Intent.GREETING)
    print("✅ Skips greetings")
    
    # Test architecture - should QUERY memory
    assert classifier.classify("Explain the auth architecture") == Intent.ARCHITECTURE
    assert classifier.should_query_memory(Intent.ARCHITECTURE)
    print("✅ Enables for architecture")
    
    # Test bug fix - should QUERY memory
    assert classifier.classify("Fix the authentication bug") == Intent.BUG_FIX
    assert classifier.should_query_memory(Intent.BUG_FIX)
    print("✅ Enables for bug fixes")
    
    # Test implementation - should QUERY memory
    assert classifier.classify("Implement OAuth") == Intent.IMPLEMENTATION
    assert classifier.should_query_memory(Intent.IMPLEMENTATION)
    print("✅ Enables for implementation")
    
    # Test planning - should QUERY memory
    assert classifier.classify("Plan the refactoring") == Intent.PLANNING
    assert classifier.should_query_memory(Intent.PLANNING)
    print("✅ Enables for planning")
    
    # Test conversation - should SKIP memory
    assert classifier.classify("What's the weather?") == Intent.CONVERSATION
    assert not classifier.should_query_memory(Intent.CONVERSATION)
    print("✅ Skips general conversation")
    
    # Test edge cases
    tests = [
        ("Can you help me understand the design?", Intent.ARCHITECTURE),
        ("The test is broken", Intent.BUG_FIX),
        ("Create a new endpoint", Intent.IMPLEMENTATION),
        ("How does this work?", Intent.ARCHITECTURE),
    ]
    
    for task, expected_intent in tests:
        intent = classifier.classify(task)
        assert intent == expected_intent, f"Failed: {task} -> {intent} (expected {expected_intent})"
    
    print(f"✅ Edge cases handled correctly")
    
    print("\n✅ MILESTONE 4 COMPLETE")
