# Contributing Guidelines - CLARA AI System

Thank you for your interest in contributing to this project!

**Last Updated:** 2025-11-17

---

## 🤝 How Can I Contribute?

### Bug Reports

If you find a bug:
1. Check if the bug has already been reported
2. Create a new issue with the label `bug`
3. Describe:
   - Expected behavior
   - Actual behavior
   - Steps to reproduce
   - Environment (OS, Python version, etc.)
   - Error messages and logs

### Feature Requests

For new features:
1. Create an issue with the label `enhancement`
2. Describe:
   - The problem to be solved
   - Proposed solution
   - Alternative solutions
   - Potential impact

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. **Implement your changes:**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation
   - Follow code style guidelines

4. **Commit your changes:**
   ```bash
   git commit -m 'feat: Add some AmazingFeature'
   ```

5. **Open a Pull Request**
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers

---

## 📋 Code Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use Type Hints consistently
- Document with Docstrings (Google style)
- Maximum line length: 100 characters
- Use `black` for formatting
- Run `flake8` for linting

### Code Quality

- Write unit tests for new code
- Maintain >80% test coverage
- Handle errors gracefully
- Log appropriately (use `logging` module)
- No hardcoded values (use configuration)

### Testing

- Run tests before submitting PR:
  ```bash
  pytest tests/ -v
  ```
- Add tests for bug fixes
- Ensure all tests pass
- Update test documentation

See [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) for details.

---

## 📝 Documentation Standards

### When to Update Documentation

Update documentation when you:
- Add new features or APIs
- Change existing behavior
- Fix bugs that affect usage
- Add configuration options
- Modify deployment procedures

### Documentation Style Guide

**Follow official standards:** [docs/DOCUMENTATION_STYLE_GUIDE.md](docs/DOCUMENTATION_STYLE_GUIDE.md)

**Key requirements:**
- Add required metadata (Created, Last Updated, Status)
- Use consistent status markers (✅, 🟡, 🔴, etc.)
- Include code examples with proper language tags
- Test all code examples before submitting
- Link to related documentation
- Follow file naming conventions (UPPER_SNAKE_CASE.md)

### Documentation Types

1. **Guides** - How-to tutorials (e.g., DEPLOYMENT_GUIDE.md)
2. **References** - API/configuration docs (e.g., API_REFERENCE.md)
3. **Overviews** - Architecture/system docs (e.g., ARCHITECTURE.md)
4. **Troubleshooting** - Problem-solving guides (e.g., TROUBLESHOOTING_GUIDE.md)

### Documentation Review Process

Before submitting documentation changes:

1. **Self-review** using [DOCUMENTATION_REVIEW_CHECKLIST.md](docs/DOCUMENTATION_REVIEW_CHECKLIST.md)
2. **Test all examples** - verify code blocks work
3. **Check all links** - ensure no broken references
4. **Update index** - add to docs/README.md if new document
5. **Update TODO** - mark tasks complete in DOCUMENTATION_TODO.md

### Documentation PR Template

```markdown
## Documentation Changes

**Type:** [New Doc / Update / Fix / Archive]
**Files Changed:** [List]

### Changes Summary
- What changed and why

### Checklist
- [ ] Follows DOCUMENTATION_STYLE_GUIDE.md
- [ ] All code examples tested
- [ ] Links verified
- [ ] Metadata updated
- [ ] Index updated (docs/README.md)

### Review Checklist
[Link to completed DOCUMENTATION_REVIEW_CHECKLIST.md]
```

---

## 📝 Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

### Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Formatting, no code change
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build, config changes
- `perf:` - Performance improvements

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Examples

```bash
feat(api): Add dataset export endpoint

Implements POST /api/datasets/{id}/export with support for
JSONL, Parquet, and CSV formats.

Closes #123
```

```bash
docs: Update API Reference with new endpoint

- Added dataset export endpoint documentation
- Included cURL and Python examples
- Updated error codes table
```

---

## 🔄 Development Workflow

### Setup Development Environment

1. **Clone repository:**
   ```bash
   git clone https://github.com/makr-code/VCC-Clara.git
   cd VCC-Clara
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_api.txt
   ```

4. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

### Before Submitting PR

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Commits follow convention
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts

### PR Review Process

1. **Automated checks** run (tests, linting)
2. **Reviewer assigned** by maintainers
3. **Feedback addressed** by author
4. **Approved and merged** by maintainer

---

## 🏗️ Project Structure

```
VCC-Clara/
├── backend/          # Backend services
│   ├── training/    # Training backend (port 45680)
│   └── datasets/    # Dataset backend (port 45681)
├── frontend/        # Frontend applications
│   ├── admin.py
│   ├── training.py
│   └── data_prep.py
├── shared/          # Shared utilities
│   ├── auth/       # Authentication
│   └── database/   # Database adapters
├── config/          # Configuration
├── tests/           # Test suite
└── docs/            # Documentation
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

---

## 📚 Helpful Resources

### Documentation

- [README.md](README.md) - Project overview
- [docs/README.md](docs/README.md) - Documentation index
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [API_REFERENCE.md](docs/API_REFERENCE.md) - API documentation
- [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - Deployment instructions
- [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) - Testing documentation

### Quick Start Guides

- [QUICK_START.md](QUICK_START.md) - Quick setup guide
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup

### Standards & Guidelines

- [docs/DOCUMENTATION_STYLE_GUIDE.md](docs/DOCUMENTATION_STYLE_GUIDE.md) - Documentation standards
- [docs/DOCUMENTATION_REVIEW_CHECKLIST.md](docs/DOCUMENTATION_REVIEW_CHECKLIST.md) - Review checklist

---

## 🆘 Getting Help

### Questions?

- **GitHub Discussions:** Ask in the appropriate category
- **Issues:** Create an issue with label `question`
- **Documentation:** Check docs/ directory first

### Report Security Issues

**Do not open public issues for security vulnerabilities.**

Email: [security contact - to be added]

---

## 📜 Code of Conduct

### Our Standards

- **Be respectful** and inclusive
- **Provide constructive** feedback
- **Focus on what is best** for the community
- **Show empathy** towards others

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks
- Spam or trolling
- Publishing others' private information

### Enforcement

Violations may result in:
- Warning
- Temporary ban
- Permanent ban

Report violations to project maintainers.

---

## 🎯 Contribution Areas

### High Priority

- Bug fixes
- Documentation improvements
- Test coverage increases
- Performance optimizations

### Medium Priority

- New features (with discussion first)
- Refactoring existing code
- UI/UX improvements

### Low Priority

- Code style cleanups
- Comment improvements
- Minor tweaks

---

## ✅ Acceptance Criteria

### For Code Changes

- [ ] Follows coding standards
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Reviewed and approved

### For Documentation Changes

- [ ] Follows DOCUMENTATION_STYLE_GUIDE.md
- [ ] Examples tested and verified
- [ ] Links checked and working
- [ ] Metadata complete
- [ ] Index updated

### For Bug Fixes

- [ ] Root cause identified
- [ ] Test reproducing bug added
- [ ] Fix implemented
- [ ] Test now passes
- [ ] No regressions

---

**Thank you for your contributions!** 🎉

**Questions?** Open a GitHub Discussion or create an issue with label `question`.

**Ready to contribute?** Fork the repository and start coding!
