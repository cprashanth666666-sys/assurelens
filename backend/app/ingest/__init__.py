"""Document intake: upload/URL submission, storage, extraction, classification.

Raw bytes are never written to Postgres — see the docstring on migration 0006
for why. This package is the boundary that enforces it: everything that
touches a file's actual bytes lives here, behind `DocumentStorage`.
"""
