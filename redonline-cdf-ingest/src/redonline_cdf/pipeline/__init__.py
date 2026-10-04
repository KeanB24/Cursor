"""Pipeline package."""

from redonline_cdf.pipeline.flatten import transform
from redonline_cdf.pipeline.ingest import IngestPipeline, IngestResult, run_ingest

__all__ = ["IngestPipeline", "IngestResult", "run_ingest", "transform"]