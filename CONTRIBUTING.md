# Contributing to Intelligent Memory System

Thank you for your interest in contributing! This project is under active development and welcomes contributions.

## Project Status

This project is currently ~70% complete. The core architecture is solid, but several features are still being refined. Check the [README](README.md) roadmap for areas that need work.

## How to Contribute

### Reporting Issues

- Check if the issue already exists
- Provide clear reproduction steps
- Include your environment (OS, Python version, Ollama version)
- Share relevant logs or error messages

### Submitting Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and concise
- Write tests for new features

### Testing

Run tests before submitting:
```bash
pytest tests/
```

### Areas Needing Help

- Test coverage improvement
- Multi-language support
- Performance optimization
- Documentation
- Web UI interface
- Plugin system design

## Development Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/intelligent-memory.git
cd intelligent-memory

# Run setup
./setup.sh  # or setup.ps1 on Windows

# Run tests
pytest tests/
```

## Questions?

Open an issue for discussion or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
