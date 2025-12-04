#!/usr/bin/env python3
"""
Apply bulletproof JSON serialization fix to vector_store_langchain.py
"""

import os
import sys


def apply_bulletproof_fix():
    """Apply bulletproof JSON fix to vector_store_langchain.py"""

    print("🔧 Applying bulletproof JSON serialization fix...")

    # Read the bulletproof implementation
    bulletproof_path = "bulletproof_json.py"
    vector_store_path = "vector_store_langchain.py"

    if not os.path.exists(bulletproof_path):
        print(f"❌ {bulletproof_path} not found!")
        return False

    if not os.path.exists(vector_store_path):
        print(f"❌ {vector_store_path} not found!")
        return False

    # Read current vector_store_langchain.py
    print("📄 Reading vector_store_langchain.py...")
    with open(vector_store_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Add import for bulletproof methods at the top
    import_line = "from bulletproof_json import create_bulletproof_save_index_method"
    if import_line not in content:
        # Find the import section and add our import
        lines = content.split("\n")
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_index = i + 1

        lines.insert(import_index, import_line)
        content = "\n".join(lines)
        print("✅ Added bulletproof import")

    # Add method replacement in __init__ method
    init_patch = """
        # Apply bulletproof JSON serialization fix
        try:
            (_save_index, _create_safe_document_dict, _extract_safe_document_data, 
             _safe_datetime_string, _write_json_safely, _validate_json_file) = create_bulletproof_save_index_method()
            
            # Replace methods
            self._save_index = _save_index.__get__(self, self.__class__)
            self._create_safe_document_dict = _create_safe_document_dict.__get__(self, self.__class__)
            self._extract_safe_document_data = _extract_safe_document_data.__get__(self, self.__class__)
            self._safe_datetime_string = _safe_datetime_string.__get__(self, self.__class__)
            self._write_json_safely = _write_json_safely.__get__(self, self.__class__)
            self._validate_json_file = _validate_json_file.__get__(self, self.__class__)
        except Exception as e:
            logger.warning(f"Failed to apply bulletproof JSON fix: {e}")
"""

    # Find the __init__ method and add the patch
    if "# Apply bulletproof JSON serialization fix" not in content:
        # Find the end of __init__ method
        lines = content.split("\n")
        in_init = False
        init_end_index = 0

        for i, line in enumerate(lines):
            if "def __init__(self" in line:
                in_init = True
            elif (
                in_init
                and line.strip()
                and not line.startswith(" ")
                and not line.startswith("\t")
            ):
                # Found end of __init__ method
                init_end_index = i - 1
                break

        if init_end_index > 0:
            # Insert the patch before the end of __init__
            patch_lines = init_patch.strip().split("\n")
            for j, patch_line in enumerate(patch_lines):
                lines.insert(init_end_index + j, patch_line)

            content = "\n".join(lines)
            print("✅ Added method replacement patch to __init__")

    # Create backup
    backup_path = vector_store_path + ".backup"
    if not os.path.exists(backup_path):
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📋 Created backup: {backup_path}")

    # Write the patched content
    with open(vector_store_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Bulletproof JSON fix applied successfully!")
    print("\n🎯 Benefits:")
    print("  ✅ Atomic file writing (temp → rename)")
    print("  ✅ Complete JSON validation")
    print("  ✅ Bulletproof error handling")
    print("  ✅ Safe datetime serialization")
    print("  ✅ Disk sync for reliability")

    return True


def test_import():
    """Test if the fix can be imported"""
    try:
        print("\n🧪 Testing bulletproof import...")
        from bulletproof_json import create_bulletproof_save_index_method

        methods = create_bulletproof_save_index_method()
        print(f"✅ Import successful - {len(methods)} methods available")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


if __name__ == "__main__":
    print("🛡️ Bulletproof JSON Serialization Fix")
    print("=" * 50)

    # Test import first
    if not test_import():
        print("❌ Cannot proceed - fix import failed")
        sys.exit(1)

    # Apply the fix
    if apply_bulletproof_fix():
        print("\n🎉 Fix applied successfully!")
        print("💡 Next steps:")
        print("   1. Restart API server")
        print("   2. Test /admin/rebuild-index endpoint")
        print("   3. Verify JSON metadata is properly formed")
    else:
        print("❌ Failed to apply fix")
        sys.exit(1)
