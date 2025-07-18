# Changelog

## Recent Changes (as of 2025-06-29)

- Refactored `multinpainter.py` into smaller, more modular files (`image_utils.py`, `prompt_utils.py`, `detection_utils.py`, `inpainting_core.py`, and `core.py`).
- Updated imports and docstrings to reflect the new module structure.
- Fixed "Homan prompt" typo in `core.py`.
- Confirmed correct naming of `detect_humans_yolo` in `models.py`.

- Auto-commit: Save local changes
- Removed requirements.txt file
- Updated multinpainter.py
- Refactoring: First step for the ability of custom models
- Added optional Huggingface prompt inference capability
- Implemented async functionality for API calls
- Added type annotations
- Documentation improvements

## Version 0.1 (development)

- Initial public version
- Core functionality for iterative image outpainting using OpenAI DALL-E API
- Support for human detection and prompt adaptation
- Huggingface integration for image description
- CLI interface using Fire
- Basic documentation and setup configuration
