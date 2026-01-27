"""
Clear ChromaDB Collections
清空ChromaDB中的所有collections，准备重新导入
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb

print("=" * 60)
print("Clear ChromaDB Collections")
print("=" * 60)

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_data")

# Get all collections
collections = client.list_collections()
print(f"\n📋 Found {len(collections)} collections:")
for coll in collections:
    print(f"   - {coll.name} ({coll.count()} items)")

# Ask for confirmation
print(f"\n⚠️  WARNING: This will delete ALL data in ChromaDB!")
confirm = input("\nType 'yes' to confirm deletion: ")

if confirm.lower() == 'yes':
    print("\n🗑️  Deleting collections...")
    for coll in collections:
        client.delete_collection(coll.name)
        print(f"   ✅ Deleted {coll.name}")
    
    print("\n✅ All collections cleared!")
    print("   You can now re-import your LinkedIn connections.")
else:
    print("\n❌ Cancelled. No data was deleted.")

print("\n" + "=" * 60)
