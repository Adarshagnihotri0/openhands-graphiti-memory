# Contributing

How to contribute to OpenHands Graphiti Memory.

---

## Development Setup

```bash
# Clone repository
git clone https://github.com/Adarshagnihotri0/openhands-graphiti-memory.git
cd openhands-graphiti-memory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dev dependencies
pip install -e ".[dev]"

# Start Neo4j
docker-compose up -d

# Run tests
pytest
```

---

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest src/test_knowledge_admission.py -v

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest src/test_knowledge_admission.py::TestAdmissionPolicy::test_secrets_blocked -v
```

---

## Code Style

We use:
- **ruff** for linting
- **black** for formatting
- **mypy** for type checking

```bash
# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

### Guidelines

1. **Type hints**: All functions must have type hints
2. **Docstrings**: Use Google-style docstrings
3. **Testing**: New code requires tests
4. **No marketing language**: See README rules

---

## Pull Request Process

1. **Fork and branch**: Create a branch from `main`
2. **Test**: Ensure all tests pass
3. **Document**: Update docs if needed
4. **PR description**: Use template

### PR Template

```markdown
## What
[One sentence describing the change]

## Why
[Why is this change needed?]

## How
[Brief implementation details]

## Testing
[How was this tested?]

## Checklist
- [ ] Tests pass
- [ ] Documentation updated (if needed)
- [ ] Type hints added
- [ ] No marketing language
```

---

## Types of Contributions

### Bug Fixes

- Create issue first if not exists
- Add test case that reproduces bug
- Fix the issue
- Ensure all tests pass

### Features

- Discuss in issue first
- Implement with tests
- Update documentation
- Add to CHANGELOG

### Documentation

- Fix errors/typos
- Add clarifications
- Improve examples
- No marketing language

### Benchmarks

High priority:
- Entity extraction quality
- Retrieval quality
- Admission precision
- Scale performance
- Long-running behavior

See `ROADMAP.md` for benchmark specifications.

---

## Code Guidelines

### No Marketing Language

❌ Don't write:
```python
"""World-class entity extraction with enterprise-grade performance."""
```

✅ Do write:
```python
"""Entity extraction using Graphiti's LLM-based extraction.

Average latency: 150ms per entity (measured on M2 Pro, Neo4j local)."""
```

### Prefer Facts Over Adjectives

❌ Bad:
```python
# Fast retrieval
def retrieve(query):
    pass
```

✅ Good:
```python
# Retrieval using Graphiti semantic search
# Benchmarked: 85ms average latency at 10K episodes
def retrieve(query: str, group_id: str) -> List[Entity]:
    pass
```

### Separate Implemented from Planned

❌ Bad:
```python
"""Supports semantic search and reflection."""
```

✅ Good:
```python
"""Semantic search via Graphiti.

Reflection engine planned - see ROADMAP.md for details.
"""
```

---

## Project-Specific Rules

### Dependencies

- Minimize external dependencies
- Pin versions in `pyproject.toml`
- Document version requirements

### Error Handling

- Always handle Graphiti failures gracefully
- Log errors, don't crash agent
- Return None on failure (not exceptions)

### Testing

- Mandatory for new features
- 80%+ coverage target
- Test edge cases

---

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Documentation clarifications
- General questions

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
