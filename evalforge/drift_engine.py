"""Compatibility engine facade over drift detection."""

from evalforge.core.judging import RegistryDriftEngine

DriftEngine = RegistryDriftEngine

__all__ = ["DriftEngine", "RegistryDriftEngine"]
