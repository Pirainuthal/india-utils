# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - unreleased

### Added
- `format_inr`, `format_indian_number`, `format_inr_compact` (lakh/crore grouping, K/L/Cr).
- `number_to_words` and `amount_in_words` in English and Tamil (`sandhi` and `spaced` styles).
- GSTIN parsing with state codes and Luhn mod-36 check digit; `gstin_check_digit`.
- PAN parsing with holder type, IFSC parsing with bank code.
- PIN code validation with postal region; mobile normalisation to `+91` E.164.
- `india-utils` command-line tool.
