# Changelog

## [1.3.0] - 2025-01-16

### Added
- Added English version support
  - Added whisper_sample_en.py
  - Added README_EN.md
  - Added CHANGELOG_EN.md
- Added bilingual comments in configuration file
- Added English version system prompt (prompt_en)

### Changed
- Optimized configuration file structure
  - Separated system_prompt from AI_CONFIG
  - Added bilingual comments
- Improved code comments
  - Added English translations for all comments
  - Unified comment format

### Documentation
- Updated configuration documentation with bilingual support
- Added English version documentation
- Improved environment variable configuration documentation


## [1.2.0] - 2025-01-10

### Added
- Added AI text processing functionality
  - Added text_processor.py module
  - Support for intelligent paragraph splitting
  - Support for spelling and word usage check
- Added AI_CONFIG configuration
  - Support for AI service provider configuration
  - Support for custom system prompts
  - Support for model parameters

### Changed
- Optimized configuration file structure
  - Renamed OpenAI configuration to more specific Whisper API configuration
  - Added separate AI service configuration section
- Improved text processing workflow
  - Automatic text processing after transcription
  - Processing only for text format output
- Updated environment variables
  - Added AI service related environment variables
  - Optimized environment variable naming and organization

### Documentation
- Updated configuration documentation
- Added text processing feature documentation
- Improved environment variable configuration documentation


## [1.1.0] - 2025-01-09

### Added
- Added support for multiple output formats (srt, text, json, verbose_json, vtt)
- Added response_format configuration in AUDIO_CONFIG
- Added automatic file extension matching based on output format

### Changed
- Restructured directory naming:
  - Renamed `segments_dir` to `audio_chunks_dir`
  - Renamed `srt_dir` to `trans_chunks_dir`
- Optimized timestamp handling logic, now only adjusts when necessary (srt/vtt formats)
- Improved segment text merging logic, added segment markers for non-subtitle formats

### Documentation
- Updated README.md with multiple format support
- Improved configuration item documentation
- Added timestamp adjustment feature scope documentation

### Code Optimization
- Added `needs_timestamp_adjustment` function for timestamp processing decision
- Improved code comments for better clarity

### Fixed
- Fixed timestamp adjustment being applied to non-subtitle formats


## [1.0.0] - 2025-01-03

Initial release. 