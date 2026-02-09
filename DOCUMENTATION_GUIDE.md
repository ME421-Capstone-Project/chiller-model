# Documentation Architecture Additions

This document describes the new architecture documentation added to the chiller-model project.

## New Documentation Files

### 1. `/docs/architecture.rst` - Complete Architecture Documentation

**Comprehensive technical documentation** covering:

- **System Overview**: High-level architecture diagram with all layers
- **Module Hierarchy**: Detailed breakdown of each module by layer
  - Core Layer (configs, constants)
  - Component Layer (wind, chiller, chiller_array)
  - Model Layer (base_interaction, gaussian_plume)
  - Simulation Layer (environment, optimizer)
- **Data Flow Diagrams**: Step-by-step data flow through the system
- **Key Design Patterns**: Composition, immutability, vectorization, type safety
- **Physics Implementation**: Detailed physics equations with code
- **Extension Points**: How to add custom models and optimizers
- **Performance Considerations**: Complexity analysis and optimization tips
- **Testing Architecture**: Test strategy and organization

**Target Audience**: Developers who need deep understanding of the system architecture.

### 2. `/docs/diagrams.md` - Interactive Mermaid Diagrams

**Visual diagrams in Mermaid format** for interactive viewing:

1. **System Architecture Diagram** - Layer-by-layer system structure
2. **Data Flow Diagram (Sequence)** - Step-by-step execution flow
3. **Module Dependency Graph** - Import relationships between modules
4. **Physics Calculation Flow** - Computation pipeline
5. **Greedy Optimization Algorithm** - Optimization strategy flowchart
6. **Class Relationships** - UML-style class diagram

**Features**:
- Viewable directly in GitHub (automatic rendering)
- Editable in [Mermaid Live Editor](https://mermaid.live/)
- Exportable as SVG/PNG for presentations
- Can be embedded in Sphinx docs with `sphinxcontrib-mermaid`

**Target Audience**: Visual learners, presentation creators, documentation viewers.

### 3. `/docs/visual-guide.rst` - Quick Visual Reference

**Lightweight quick reference** with ASCII diagrams for:

- System layers overview
- Module interaction map
- Key data structures summary
- Typical workflow example
- Quick module lookup table

**Target Audience**: Developers who need quick reference without deep dive.

### 4. Updated `/README.md`

Added **Architecture section** with:
- High-level ASCII architecture diagram
- Key design principles
- Link to detailed architecture docs

## How to Use These Docs

### For New Contributors

**Start here:**
1. Read `README.md` - Overview and quick architecture
2. Browse `docs/visual-guide.rst` - Quick visual reference
3. Study `docs/architecture.rst` - Deep dive when needed

### For Code Reviews

**Reference:**
- `docs/architecture.rst` - Check design pattern compliance
- `docs/diagrams.md` - Verify module dependencies
- Architecture sections: Key Design Patterns, Extension Points

### For Presentations

**Extract visuals from:**
- `docs/diagrams.md` - Export Mermaid diagrams as SVG/PNG
- `docs/architecture.rst` - Copy ASCII diagrams
- Use Mermaid Live Editor to customize colors/styles

### For Academic Papers

**Reference:**
- `docs/architecture.rst` - Architecture description text
- Physics Implementation section - Equations with citations
- Export Mermaid diagrams to PDF via SVG

## Building the Documentation

### Standard Build

```bash
cd docs
make html
```

Output: `docs/_build/html/index.html`

### With Mermaid Support (Optional)

Install Mermaid extension:

```bash
pip install sphinxcontrib-mermaid
```

Add to `docs/conf.py`:

```python
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinxcontrib.mermaid',  # Add this
]
```

Then build as normal.

### Preview During Development

```bash
cd docs
make html && open _build/html/index.html
```

## Documentation Structure

```
docs/
├── index.rst                 # Main entry point (UPDATED)
├── architecture.rst          # NEW: Complete architecture docs
├── visual-guide.rst          # NEW: Quick visual reference
├── diagrams.md              # NEW: Mermaid interactive diagrams
├── getting-started.rst      # Existing
├── user-guide.rst          # Existing
├── examples.rst            # Existing
├── api/                    # Existing API docs
│   └── index.rst
└── conf.py                 # Sphinx configuration
```

## Key Features of New Docs

### 1. Multi-Format Diagrams

- **ASCII art** in `.rst` files - Renders everywhere (terminal, PDF, HTML)
- **Mermaid diagrams** in `.md` files - Interactive in browsers
- Both formats show same information, different use cases

### 2. Progressive Disclosure

- `README.md` - 30-second overview
- `visual-guide.rst` - 5-minute quick reference
- `architecture.rst` - 30-minute deep dive

### 3. Multiple Learning Styles

- **Visual**: ASCII + Mermaid diagrams
- **Textual**: Detailed descriptions
- **Code**: Inline examples throughout
- **Mathematical**: Physics equations with LaTeX

### 4. Practical Focus

Every section includes:
- **Purpose**: Why this exists
- **Key Features**: What it does
- **Examples**: How to use it
- **References**: Where to learn more

## Maintenance

### When Adding New Modules

1. Update module hierarchy in `docs/architecture.rst`
2. Add to dependency graph in `docs/diagrams.md`
3. Update quick lookup table in `docs/visual-guide.rst`
4. Rebuild docs and verify rendering

### When Changing Architecture

1. Update system overview diagram
2. Update affected module sections
3. Update design patterns section if pattern changes
4. Rebuild and review all diagram renders

### When Refactoring

Before refactoring:
- Document current architecture
- Update diagrams to proposed state
- Review with team

After refactoring:
- Verify diagrams match implementation
- Update any changed API examples
- Rebuild docs

## Integration with Development Workflow

### Pre-Commit Hook (Recommended)

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if architecture docs exist for new modules
for file in $(git diff --cached --name-only --diff-filter=A | grep "^src/.*\.py$"); do
    echo "New module detected: $file"
    echo "Remember to update docs/architecture.rst if this is a new module!"
done
```

### CI/CD Integration

Add to `.github/workflows/docs.yml`:

```yaml
name: Documentation
on: [push, pull_request]
jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements-docs.txt
      - name: Build documentation
        run: |
          cd docs
          make html
      - name: Check for broken links
        run: |
          cd docs
          make linkcheck
```

## Design Principles Reflected in Docs

The documentation architecture mirrors the code architecture:

1. **Modularity**: Separate files for different concerns
2. **Composition**: Reference other docs rather than duplicating
3. **Immutability**: Versioned documentation (don't edit old versions)
4. **Type Safety**: Clear structure and linking
5. **Vectorization**: Efficient reading through visual diagrams

## Questions?

For questions about:
- **Content**: See the relevant doc file's purpose/target audience
- **Structure**: See this DOCUMENTATION_GUIDE.md
- **Building**: See "Building the Documentation" above
- **Contributing**: See the main project CONTRIBUTING.md

## Next Steps

Recommended enhancements for future versions:

1. **Interactive Examples**: Jupyter notebooks embedded in docs
2. **Video Tutorials**: Screen recordings for complex workflows  
3. **API Changelog**: Automated API diff between versions
4. **Performance Benchmarks**: Documented in architecture.rst
5. **Translation**: Multi-language support for broader accessibility

---

**Last Updated**: 2026-02-06  
**Documentation Version**: 1.0  
**Compatible with**: chiller-model v0.1.0+
