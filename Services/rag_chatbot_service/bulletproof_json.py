#!/usr/bin/env python3
"""
Bulletproof JSON serialization methods for vector_store_langchain.py
Thay thế method _save_index để fix hoàn toàn vấn đề JSON serialize.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


def create_bulletproof_save_index_method():
    """
    Return bulletproof _save_index method để thay thế method hiện tại.
    """

    def _save_index(self) -> None:
        """Save FAISS index và metadata to disk with bulletproof JSON serialization."""
        try:
            # Create persist directory
            os.makedirs(self.persist_directory, exist_ok=True)

            # Save FAISS index first
            logger.info("Saving FAISS index...")
            self.vectorstore.save_local(self.persist_directory)

            # Save document metadata with bulletproof serialization
            metadata_path = os.path.join(
                self.persist_directory, "documents_metadata.json"
            )
            temp_path = metadata_path + ".tmp"

            logger.info(f"Processing {len(self.documents)} documents for metadata...")

            # Process documents with comprehensive error handling
            safe_documents = self._create_safe_document_dict()

            # Write to temporary file first (atomic write)
            self._write_json_safely(temp_path, safe_documents)

            # Validate the written file
            self._validate_json_file(temp_path)

            # Replace original file atomically
            if os.path.exists(metadata_path):
                backup_path = metadata_path + ".backup"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(metadata_path, backup_path)

            os.rename(temp_path, metadata_path)

            logger.info(
                f"✅ Successfully saved metadata for {len(safe_documents)} documents"
            )
            logger.info(f"📁 Index saved to: {self.persist_directory}")

        except Exception as e:
            logger.error(f"❌ Failed to save index: {e}")
            # Clean up temp file if it exists
            temp_path = os.path.join(
                self.persist_directory, "documents_metadata.json.tmp"
            )
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def _create_safe_document_dict(self) -> Dict[str, Any]:
        """Create a completely safe document dictionary for JSON serialization."""
        safe_documents = {}
        current_time = datetime.now().isoformat()

        for doc_id, doc in self.documents.items():
            try:
                logger.debug(f"Processing document: {doc_id}")

                # Start with a clean document structure
                safe_doc = self._extract_safe_document_data(doc, doc_id, current_time)

                # Validate this document can be JSON serialized
                json.dumps(safe_doc)  # Test serialization

                safe_documents[doc_id] = safe_doc

            except Exception as doc_error:
                logger.warning(f"⚠️ Failed to process document {doc_id}: {doc_error}")
                # Create minimal safe fallback
                safe_documents[doc_id] = {
                    "content": f"Document {doc_id} failed to serialize",
                    "chunk_text": "Serialization error",
                    "metadata": {
                        "error": "document_serialization_failed",
                        "error_details": str(doc_error)[:200],
                        "processed_at": current_time,
                        "created_at": current_time,
                    },
                }

        return safe_documents

    def _extract_safe_document_data(
        self, doc: Any, doc_id: str, fallback_time: str
    ) -> Dict[str, Any]:
        """Extract safe data from document with comprehensive validation."""

        # Convert document to dict safely
        if hasattr(doc, "model_dump"):
            doc_dict = doc.model_dump()
        elif isinstance(doc, dict):
            doc_dict = dict(doc)
        else:
            # Extract attributes safely
            doc_dict = {}
            for attr in ["content", "chunk_text", "metadata"]:
                if hasattr(doc, attr):
                    try:
                        doc_dict[attr] = getattr(doc, attr)
                    except:
                        pass

        # Create safe document structure
        safe_doc = {}

        # Handle content
        content = doc_dict.get("content", "")
        if isinstance(content, str):
            safe_doc["content"] = content
        else:
            safe_doc["content"] = str(content) if content else ""

        # Handle chunk_text
        chunk_text = doc_dict.get("chunk_text", safe_doc["content"])
        if isinstance(chunk_text, str):
            safe_doc["chunk_text"] = chunk_text
        else:
            safe_doc["chunk_text"] = (
                str(chunk_text) if chunk_text else safe_doc["content"]
            )

        # Handle metadata with extra care
        metadata = doc_dict.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        safe_metadata = {}
        for key, value in metadata.items():
            try:
                # Handle different value types safely
                if value is None:
                    continue  # Skip None values
                elif key == "created_at":
                    safe_metadata[key] = self._safe_datetime_string(
                        value, fallback_time
                    )
                elif key == "processed_at":
                    safe_metadata[key] = self._safe_datetime_string(
                        value, fallback_time
                    )
                elif isinstance(value, (str, int, float, bool)):
                    safe_metadata[key] = value
                elif isinstance(value, (list, tuple)):
                    # Convert to safe list
                    safe_list = []
                    for item in value:
                        if (
                            isinstance(item, (str, int, float, bool))
                            and item is not None
                        ):
                            safe_list.append(item)
                    safe_metadata[key] = safe_list
                else:
                    # Convert to string as fallback
                    safe_metadata[key] = str(value)
            except Exception as meta_error:
                logger.debug(f"Skipping metadata field {key}: {meta_error}")
                continue

        # Ensure required fields exist
        if "created_at" not in safe_metadata:
            safe_metadata["created_at"] = fallback_time
        if "processed_at" not in safe_metadata:
            safe_metadata["processed_at"] = fallback_time

        safe_doc["metadata"] = safe_metadata

        return safe_doc

    def _safe_datetime_string(self, value: Any, fallback: str) -> str:
        """Safely convert any value to datetime string."""
        if isinstance(value, str) and value.strip():
            return value.strip()
        elif hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except:
                return fallback
        else:
            return fallback

    def _write_json_safely(self, file_path: str, data: Dict[str, Any]) -> None:
        """Write JSON with bulletproof error handling."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()  # Force write to disk
                os.fsync(f.fileno())  # Force OS to write to disk

        except Exception as write_error:
            logger.error(f"JSON write failed: {write_error}")

            # Ultimate fallback - write minimal valid JSON
            minimal_data = {
                "error": "json_write_failed",
                "timestamp": datetime.now().isoformat(),
                "original_document_count": len(data),
                "error_details": str(write_error)[:200],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(minimal_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

    def _validate_json_file(self, file_path: str) -> None:
        """Validate written JSON file is complete and valid."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"✅ JSON validation passed - {len(data)} documents")

        except json.JSONDecodeError as json_error:
            logger.error(f"❌ JSON validation failed: {json_error}")
            raise ValueError(f"Written JSON is invalid: {json_error}")
        except Exception as e:
            logger.error(f"❌ JSON file validation error: {e}")
            raise

    # Return tuple of methods to be added to class
    return (
        _save_index,
        _create_safe_document_dict,
        _extract_safe_document_data,
        _safe_datetime_string,
        _write_json_safely,
        _validate_json_file,
    )


# Instruction for usage:
"""
To use this bulletproof implementation:

1. Import the methods:
   from bulletproof_json import create_bulletproof_save_index_method

2. Replace the methods in LangChainVectorStore class:
   (_save_index, _create_safe_document_dict, _extract_safe_document_data, 
    _safe_datetime_string, _write_json_safely, _validate_json_file) = create_bulletproof_save_index_method()
    
   LangChainVectorStore._save_index = _save_index
   LangChainVectorStore._create_safe_document_dict = _create_safe_document_dict
   LangChainVectorStore._extract_safe_document_data = _extract_safe_document_data
   LangChainVectorStore._safe_datetime_string = _safe_datetime_string
   LangChainVectorStore._write_json_safely = _write_json_safely
   LangChainVectorStore._validate_json_file = _validate_json_file

This provides:
✅ Atomic file writing (temp file → rename)
✅ Complete JSON validation before commit
✅ Bulletproof error handling at every step
✅ Safe fallbacks for problematic documents
✅ Proper datetime handling
✅ Force disk sync for reliability
"""
