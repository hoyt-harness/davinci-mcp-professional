# DaVinci MCP Professional — API Documentation

This directory contains the comprehensive API documentation for DaVinci MCP
Professional, generated using Doxygen.

## What's Included

- **HTML Documentation**: Browse `html/index.html` for the complete API reference
- **Class Diagrams**: Visual representations of class hierarchies and relationships
- **Module Documentation**: Detailed documentation for each Python module
- **Source Code Browser**: Cross-referenced source code with syntax highlighting
- **Search Functionality**: Fast search across all documentation

## Main Components Documented

### Core Classes
- **DaVinciMCPServer**: The main MCP server implementation
- **DaVinciResolveClient**: Client wrapper for DaVinci Resolve API
- **Exception Classes**: Specialized error handling classes

### Modules
- **Tools**: MCP tool definitions and implementations
- **Resources**: MCP resource definitions and handlers
- **Utils**: Platform detection and environment setup utilities
- **CLI**: Command-line interface module

## Viewing the Documentation

### Option 1: Local File Browser
Open `html/index.html` in any web browser to view the documentation locally.

### Option 2: Local Web Server (Recommended)
For the best experience with search functionality:

```bash
# Navigate to the docs directory
cd docs/html

# Start a local web server
uv run python -m http.server 8000

# Then open http://localhost:8000 in your browser
```

## Regenerating Documentation

To update the documentation after code changes:

```bash
# From the project root directory
doxygen Doxyfile
```

The documentation will be regenerated in this directory.

## Documentation Standards

This documentation follows professional software documentation standards:
- All public APIs are documented
- Type hints are properly extracted and displayed
- Python docstrings are converted to formatted documentation
- Code examples and usage patterns are included where applicable
- Visual diagrams show system architecture and relationships

---

*Generated with Doxygen for DaVinci MCP Professional*
