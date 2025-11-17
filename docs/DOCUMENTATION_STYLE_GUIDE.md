# Documentation Style Guide

**Created:** 2025-11-17  
**Last Updated:** 2025-11-17  
**Version:** 1.0  
**Status:** ✅ Active

---

## Purpose

This style guide ensures consistency across all CLARA documentation. All documentation should follow these standards for maintainability, readability, and professionalism.

---

## Document Structure

### Required Metadata Header

Every documentation file MUST begin with this metadata block:

```markdown
# Document Title

**Created:** YYYY-MM-DD  
**Last Updated:** YYYY-MM-DD  
**Version:** X.Y (optional)  
**Status:** [Active/Draft/Archived/Deprecated]  
**Author:** [Name/Team] (optional)

---
```

**Example:**
```markdown
# API Reference

**Created:** 2025-11-17  
**Last Updated:** 2025-11-17  
**Version:** 1.0  
**Status:** ✅ Active

---
```

### Standard Section Order

1. **Purpose/Overview** - What this document covers
2. **Prerequisites** (if applicable) - What you need to know first
3. **Main Content** - Core documentation
4. **Examples** (if applicable) - Practical examples
5. **Troubleshooting** (if applicable) - Common issues
6. **Related Documentation** - Links to other docs
7. **References** (if applicable) - External resources

---

## Markdown Formatting Standards

### Headers

- **H1 (`#`):** Document title only (once per document)
- **H2 (`##`):** Major sections
- **H3 (`###`):** Subsections
- **H4 (`####`):** Sub-subsections (use sparingly)

**Example:**
```markdown
# Document Title

## Major Section

### Subsection

#### Detail (if needed)
```

### Lists

**Unordered Lists:** Use `-` for consistency
```markdown
- Item 1
- Item 2
  - Sub-item 2.1
  - Sub-item 2.2
```

**Ordered Lists:** Use `1.` for all items (auto-numbering)
```markdown
1. First step
1. Second step
1. Third step
```

**Task Lists:** Use for checklists
```markdown
- [x] Completed task
- [ ] Pending task
```

### Code Blocks

**Inline Code:** Use backticks for file names, commands, variables
```markdown
The `config.py` file contains the `training_port` variable.
```

**Code Blocks:** Use triple backticks with language identifier
```markdown
```python
def example():
    return "Hello World"
```
```

**Supported Languages:**
- `python` - Python code
- `bash` - Shell commands (Unix/Linux/macOS)
- `powershell` - PowerShell commands (Windows)
- `yaml` - YAML configuration
- `json` - JSON data
- `sql` - SQL queries
- `dockerfile` - Dockerfile
- `nginx` - Nginx configuration

**Shell Command Examples:**
```markdown
```bash
# Linux/macOS
python -m pytest tests/
```

```powershell
# Windows PowerShell
python -m pytest tests/
```
```

### Tables

Use tables for structured data. Always include header separator.

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

**Alignment:**
- Left-aligned (default): `|----------|`
- Center-aligned: `|:--------:|`
- Right-aligned: `|----------:|`

### Links

**Internal Links:** Use relative paths
```markdown
See [Architecture](ARCHITECTURE.md) for details.
See [Configuration Reference](CONFIGURATION_REFERENCE.md#port-configuration)
```

**External Links:** Use descriptive text
```markdown
See [Python Documentation](https://docs.python.org/) for more info.
```

**Link to Sections:** Use lowercase with hyphens
```markdown
[Jump to Quick Start](#quick-start)
```

### Emphasis

- **Bold (`**text**`):** For emphasis, important terms, section titles
- *Italic (`*text*`):** For subtle emphasis, introducing terms
- `Code (`code`)`: For technical terms, file names, commands

**Example:**
```markdown
The **main configuration** file is `config.py`. It contains the *default settings* for the application.
```

---

## Status Markers

Use emoji markers for visual clarity:

**Status Indicators:**
- ✅ **Completed/Active:** `✅`
- 🟢 **Working/Healthy:** `🟢`
- 🟡 **In Progress/Warning:** `🟡`
- 🔴 **Critical/Error:** `🔴`
- ⚠️ **Warning/Caution:** `⚠️`
- ❌ **Failed/Blocked:** `❌`
- ⏸️ **Paused/On Hold:** `⏸️`
- 🔄 **Processing:** `🔄`
- 📦 **Archived:** `📦`
- 🚀 **New/Released:** `🚀`

**Priority Indicators:**
- 🔴 **CRITICAL:** Must be done immediately
- 🟠 **HIGH:** Important, should be done soon
- 🟡 **MEDIUM:** Normal priority
- 🟢 **LOW:** Nice to have

**Example:**
```markdown
### Task Status

- ✅ Database migration completed
- 🟡 API documentation in progress
- 🔴 Critical bug needs fixing
- ⚠️ Warning: Configuration needs update
```

---

## Code Examples

### Best Practices

1. **Always include context**
   ```python
   # Good: Context provided
   from config import config
   
   # Start the training backend
   port = config.training_port  # Default: 45680
   ```

2. **Use comments for clarity**
   ```python
   # Calculate training metrics
   metrics = {
       "loss": 0.045,  # Lower is better
       "accuracy": 0.95  # Percentage (0-1)
   }
   ```

3. **Show expected output**
   ```bash
   $ python backend.py
   # Output:
   # Starting backend on port 45680...
   # ✓ Server ready
   ```

4. **Include error handling**
   ```python
   try:
       result = api_call()
   except ConnectionError as e:
       print(f"Error: {e}")
       # Fallback to cached data
   ```

### Command Examples

**Use realistic examples:**
```bash
# Good: Specific and actionable
curl -X POST http://localhost:45680/api/training/jobs \
  -H "Content-Type: application/json" \
  -d '{"config_path": "/data/config.yaml"}'

# Bad: Too generic
curl <URL>
```

**Show both success and failure:**
```bash
# Successful response (200 OK)
{
  "job_id": "abc123",
  "status": "queued"
}

# Error response (400 Bad Request)
{
  "error": "Invalid config path",
  "details": "File not found: /data/config.yaml"
}
```

---

## Documentation Types

### Guides

Purpose: Teach users how to accomplish tasks

**Structure:**
1. Overview
2. Prerequisites
3. Step-by-step instructions
4. Examples
5. Troubleshooting
6. Next steps

**Example:** DEPLOYMENT_GUIDE.md, TESTING_GUIDE.md

### References

Purpose: Document APIs, configurations, commands

**Structure:**
1. Overview
2. Complete reference (alphabetical or logical order)
3. Examples for each item
4. Related references

**Example:** API_REFERENCE.md, CONFIGURATION_REFERENCE.md

### Overviews

Purpose: High-level understanding of systems/features

**Structure:**
1. Executive summary
2. Architecture/components
3. Key concepts
4. Links to detailed docs

**Example:** ARCHITECTURE.md, SYSTEM_OVERVIEW.md

### Troubleshooting

Purpose: Help users solve problems

**Structure:**
1. Quick diagnostic commands
2. Issues organized by category
3. Symptoms → Diagnosis → Solution
4. Related documentation

**Example:** TROUBLESHOOTING_GUIDE.md

---

## Conventions

### File Names

- Use `UPPER_SNAKE_CASE.md` for documentation files
- Examples: `API_REFERENCE.md`, `DEPLOYMENT_GUIDE.md`
- Exception: `README.md` (standard convention)

### Directory Structure

```
docs/
├── README.md                  # Documentation index
├── DOCUMENTATION_STYLE_GUIDE.md  # This file
├── [TOPIC]_GUIDE.md          # User guides
├── [TOPIC]_REFERENCE.md      # Reference documentation
├── archive/                  # Historical documentation
│   ├── frontend/
│   ├── implementation/
│   └── milestones/
```

### Versioning

Use semantic versioning for major documentation:
- **Major (1.0 → 2.0):** Breaking changes, complete rewrites
- **Minor (1.0 → 1.1):** New sections, significant additions
- **Patch (1.0.0 → 1.0.1):** Typo fixes, minor clarifications

**Example:**
```markdown
**Version:** 1.2.0
- 1.0.0 (2025-10-01): Initial release
- 1.1.0 (2025-10-15): Added deployment section
- 1.2.0 (2025-11-17): Added Docker deployment
```

### Dates

Always use ISO 8601 format: `YYYY-MM-DD`
- **Good:** 2025-11-17
- **Bad:** 17/11/2025, Nov 17 2025

---

## Language and Tone

### Writing Style

1. **Be concise and clear**
   - Good: "Run `pytest` to execute tests."
   - Bad: "In order to execute the test suite, you should run the pytest command."

2. **Use active voice**
   - Good: "The system validates the configuration."
   - Bad: "The configuration is validated by the system."

3. **Be direct and actionable**
   - Good: "Install dependencies with `pip install -r requirements.txt`"
   - Bad: "You might want to consider installing the dependencies..."

4. **Use present tense**
   - Good: "The backend starts on port 45680."
   - Bad: "The backend will start on port 45680."

### Terminology

**Consistent Terms:**
- **Backend** (not "server" or "API")
- **Frontend** (not "GUI" or "client")
- **Configuration** (not "config file" or "settings")
- **Dataset** (not "data set")
- **Job** (for training jobs, not "task")
- **Endpoint** (for API endpoints, not "route" or "path")

**Capitalization:**
- CLARA (project name - all caps)
- PostgreSQL (not "Postgres" or "postgres")
- Docker (capital D)
- JWT (all caps)
- Python (capital P)

---

## Examples Section

Every guide should include an **Examples** section with:

1. **Complete, working examples**
2. **Expected output**
3. **Common variations**
4. **Error cases**

**Template:**
```markdown
## Examples

### Basic Example

Description of what this example demonstrates.

```python
# Code example
result = function_call()
print(result)
```

**Output:**
```
Expected output here
```

### Advanced Example

Description of advanced usage.

```python
# More complex example
```

### Common Errors

**Error:** Description of error
```
Error message
```

**Solution:** How to fix it
```

---

## Troubleshooting Section

Format for troubleshooting entries:

```markdown
### Issue: [Brief description]

**Symptoms:**
- Symptom 1
- Symptom 2

**Diagnosis:**
```bash
# Commands to diagnose
command1
command2
```

**Solution:**
```bash
# Commands to fix
fix_command1
fix_command2
```

**Related:** [Link to related documentation]
```

---

## Maintenance

### Review Frequency

- **Guides:** Quarterly review
- **References:** Review on each release
- **Troubleshooting:** Review on each major issue
- **Architecture:** Review on each major change

### Update Process

1. Update document content
2. Update "Last Updated" date
3. Increment version if significant
4. Update changelog (if present)
5. Review cross-references

### Deprecation

When deprecating documentation:

1. Add deprecation notice at top:
   ```markdown
   > **⚠️ DEPRECATED:** This document is deprecated as of YYYY-MM-DD.  
   > See [New Document](NEW_DOC.md) instead.
   ```

2. Update **Status** to `⚠️ Deprecated`
3. Keep document for 6 months minimum
4. Move to `docs/archive/deprecated/` after 6 months

---

## Checklist for New Documentation

Before publishing new documentation:

- [ ] Metadata header present (Created, Updated, Status)
- [ ] Clear purpose/overview section
- [ ] Consistent formatting (headers, lists, code blocks)
- [ ] All code examples tested and working
- [ ] Links to related documentation
- [ ] Examples section included (if applicable)
- [ ] Troubleshooting section included (if applicable)
- [ ] Proofread for typos and clarity
- [ ] File name follows convention
- [ ] Added to docs/README.md index
- [ ] Version number if applicable

---

## Related Documentation

- [Documentation Index](README.md) - Complete documentation listing
- [DOCUMENTATION_TODO.md](DOCUMENTATION_TODO.md) - Ongoing documentation tasks
- [DOCUMENTATION_INVENTORY.md](DOCUMENTATION_INVENTORY.md) - Documentation catalog
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute

---

## References

- [Markdown Guide](https://www.markdownguide.org/)
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Write the Docs](https://www.writethedocs.org/)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)

---

**Document Status:** This is the official style guide for all CLARA documentation. All new documentation must follow these standards. Existing documentation should be updated to conform during regular maintenance cycles.
