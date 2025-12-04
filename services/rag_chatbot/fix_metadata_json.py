#!/usr/bin/env python3
"""
Fix corrupted documents_metadata.json file.
Sửa file JSON bị lỗi format.
"""

import json
import os
from datetime import datetime


def fix_metadata_json():
    """Fix corrupted metadata JSON file."""

    metadata_path = "faiss_db_mongodb/documents_metadata.json"
    backup_path = "faiss_db_mongodb/documents_metadata.json.backup"

    print("🔧 Starting JSON fix process...")

    # Create backup first
    if os.path.exists(metadata_path):
        print(f"📋 Creating backup: {backup_path}")
        with open(metadata_path, "r", encoding="utf-8") as src:
            content = src.read()
        with open(backup_path, "w", encoding="utf-8") as dst:
            dst.write(content)
        print(f"✅ Backup created - {len(content)} chars")

    # Read file content
    print(f"📄 Reading corrupted file...")
    with open(metadata_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"📊 File size: {len(content)} characters")

    # Find the corrupted part
    print("🔍 Analyzing corruption...")

    # Look for the pattern "created_at": at the end
    if content.endswith('"created_at":'):
        print("❌ Found incomplete created_at field at end")
        # Remove the incomplete field and add proper closing
        fixed_content = content.rstrip('"created_at":').rstrip(",\n      ")
        fixed_content += "\n    }\n  }\n}"
    elif content.endswith('"created_at": '):
        print("❌ Found incomplete created_at field with space")
        fixed_content = content.rstrip('"created_at": ').rstrip(",\n      ")
        fixed_content += "\n    }\n  }\n}"
    else:
        # Try to find the last complete document and truncate after it
        print("🔍 Looking for last complete document...")

        # Find the pattern of complete document endings
        import re

        # Look for pattern: "created_at": "datetime value"
        matches = list(re.finditer(r'"created_at":\s*"[^"]*"', content))
        if matches:
            last_match = matches[-1]
            end_pos = last_match.end()

            # Find the closing braces after this
            remaining = content[end_pos:]
            brace_pattern = re.search(r"\s*}\s*}\s*,?\s*", remaining)
            if brace_pattern:
                final_pos = end_pos + brace_pattern.end()
                # Take content up to this point and add proper JSON closing
                fixed_content = content[:final_pos].rstrip(",\n ")
                if not fixed_content.endswith("}"):
                    fixed_content += "\n  }"
                fixed_content += "\n}"
            else:
                # Fallback: create minimal valid JSON
                print("⚠️ Could not find proper structure, creating fallback")
                fixed_content = (
                    '{\n  "error": "corrupted_metadata_fixed",\n  "timestamp": "'
                    + datetime.now().isoformat()
                    + '",\n  "note": "Original file was corrupted and fixed"\n}'
                )
        else:
            print("⚠️ No valid created_at fields found, creating minimal JSON")
            fixed_content = (
                '{\n  "error": "no_valid_documents",\n  "timestamp": "'
                + datetime.now().isoformat()
                + '"\n}'
            )

    # Validate the fixed JSON
    print("✅ Validating fixed JSON...")
    try:
        parsed = json.loads(fixed_content)
        print(f"✅ JSON is valid! Contains {len(parsed)} entries")

        # Write the fixed content
        print("💾 Writing fixed JSON...")
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        print("🎉 JSON file fixed successfully!")
        print(f"📊 Original size: {len(content)} chars")
        print(f"📊 Fixed size: {len(fixed_content)} chars")

        # Test final validation
        with open(metadata_path, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        print(f"✅ Final validation passed - {len(test_data)} documents")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ Fixed JSON still invalid: {e}")
        print("🔄 Trying alternative fix...")

        # Alternative: create completely new minimal JSON
        minimal_json = {
            "error": "metadata_reconstruction_needed",
            "timestamp": datetime.now().isoformat(),
            "original_size": len(content),
            "note": "Original metadata was corrupted. Rebuild index to regenerate.",
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(minimal_json, f, indent=2, ensure_ascii=False)

        print("✅ Created minimal valid JSON as fallback")
        return False


if __name__ == "__main__":
    try:
        success = fix_metadata_json()
        if success:
            print("\n🎯 SUCCESS: Metadata JSON fixed!")
        else:
            print("\n⚠️ PARTIAL: Created fallback JSON. Please run rebuild-index.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
