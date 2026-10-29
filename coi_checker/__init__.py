"""Detect potential reviewer conflicts of interest from co-authorship and affiliation records."""
from .core import name_key, load_papers, coauthor_index, check_reviewers

__version__ = "0.1.0"
__all__ = ["name_key", "load_papers", "coauthor_index", "check_reviewers"]
