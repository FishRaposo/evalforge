"""Compatibility engine facade over the judge registry."""

from evalforge.core.judging import RegistryJudgeEngine

JudgeEngine = RegistryJudgeEngine

__all__ = ["JudgeEngine", "RegistryJudgeEngine"]
