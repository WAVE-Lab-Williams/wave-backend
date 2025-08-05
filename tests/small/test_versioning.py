"""
Tests for versioning utilities and middleware.
"""

import pytest

from wave_backend.utils.versioning import (
    API_VERSION,
    get_compatibility_warning,
    is_compatible_version,
    parse_version,
)


class TestVersionParsing:
    """Test version parsing functionality."""

    def test_parse_valid_versions(self):
        """Test parsing valid semantic versions."""
        assert parse_version("1.0.0") == (1, 0, 0)
        assert parse_version("2.3.4") == (2, 3, 4)
        assert parse_version("v1.0.0") == (1, 0, 0)
        assert parse_version("1.0.0-beta.1") == (1, 0, 0)
        assert parse_version("1.0.0+build.123") == (1, 0, 0)

    def test_parse_invalid_versions(self):
        """Test parsing invalid versions raises ValueError."""
        with pytest.raises(ValueError):
            parse_version("")

        with pytest.raises(ValueError):
            parse_version("1.0")

        with pytest.raises(ValueError):
            parse_version("1.0.0.0")

        with pytest.raises(ValueError):
            parse_version("invalid")


class TestVersionCompatibility:
    """Test version compatibility checking."""

    def test_semantic_version_compatibility(self):
        """Test semantic version compatibility logic."""
        # Same major version should be compatible
        assert is_compatible_version("1.0.0", "1.0.0") is True
        assert is_compatible_version("1.0.0", "1.0.1") is True
        assert is_compatible_version("1.0.0", "1.1.0") is True
        assert is_compatible_version("1.5.0", "1.6.0") is True
        assert is_compatible_version("2.0.0", "2.1.0") is True

        # Different major version should be incompatible
        assert is_compatible_version("1.0.0", "2.0.0") is False
        assert is_compatible_version("2.0.0", "1.0.0") is False
        assert is_compatible_version("1.5.0", "3.0.0") is False

    def test_invalid_version_compatibility(self):
        """Test handling of invalid versions."""
        assert is_compatible_version("invalid", "1.0.0") is False
        assert is_compatible_version("1.0.0", "invalid") is False


class TestCompatibilityWarnings:
    """Test compatibility warning generation."""

    def test_no_warning_for_compatible_versions(self):
        """Test no warning for compatible versions."""
        # Test compatible versions (same major version)
        assert get_compatibility_warning("1.0.0", "1.0.0") is None
        assert get_compatibility_warning("1.0.0", "1.0.1") is None
        assert get_compatibility_warning("1.0.0", "1.1.0") is None
        assert get_compatibility_warning("1.5.0", "1.2.0") is None
        assert get_compatibility_warning("2.0.0", "2.5.1") is None

    def test_warning_for_major_version_mismatch(self):
        """Test warning for major version mismatches."""
        warning = get_compatibility_warning("1.0.0", "2.0.0")
        assert warning is not None
        assert "Major version mismatch" in warning
        assert "1.0.0" in warning
        assert "2.0.0" in warning

        # Test different combinations of major version mismatches
        warning = get_compatibility_warning("2.1.0", "1.9.0")
        assert warning is not None
        assert "Major version mismatch" in warning

    def test_warning_for_invalid_versions(self):
        """Test warning for invalid version formats."""
        warning = get_compatibility_warning("invalid", "1.0.0")
        assert warning is not None
        assert "Invalid version format" in warning


class TestAPIVersionConstant:
    """Test API version constant."""

    def test_api_version_format(self):
        """Test API version follows semantic versioning."""
        # Should not raise exception
        major, minor, patch = parse_version(API_VERSION)
        assert isinstance(major, int)
        assert isinstance(minor, int)
        assert isinstance(patch, int)
        assert major >= 0
        assert minor >= 0
        assert patch >= 0
