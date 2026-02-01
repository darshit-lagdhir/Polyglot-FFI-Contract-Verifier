"""
Representation Layer Module
Handles IR normalization and canonical type representation.
"""

from .ir_normalizer import IRNormalizer
from .type_resolver import TypeResolver
from .qualifier_normalizer import QualifierNormalizer
from .layout_normalizer import LayoutNormalizer

__all__ = [
    'IRNormalizer',
    'TypeResolver',
    'QualifierNormalizer',
    'LayoutNormalizer'
]
