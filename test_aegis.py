import os
import shutil
import numpy as np
from pathlib import Path
from index.node import VaultNode, MemoryTier, RelationType
from memory_tiers import MemoryTierManager

test_dir = Path("./test_aegis_tmp")
if test_dir.exists():
    shutil.rmtree(test_dir)
os.makedirs(test_dir)

print("Testing AegisLog integration in MemoryTierManager...")
try:
    manager = MemoryTierManager(data_dir=test_dir)
    
    vec = np.random.rand(1024).astype(np.float32)
    node = VaultNode(
        id=VaultNode.generate_id(),
        text="Test payload per memory tier integration",
        vector=vec,
        metadata={"source": "test_script", "val": 42},
        tier=MemoryTier.WORKING
    )
    node.add_edge("target_123", RelationType.CITES, 0.9)
    manager.put(node)
    
    print(f"Node written to manager. Working cache len: {len(manager.working._cache)}")
    
    manager.working.invalidate(node.id)
    print("Invalidated from working memory.")

    retrieved = manager.get(node.id)
    assert retrieved is not None, "Node should exist in episodic memory!"
    assert retrieved.text == "Test payload per memory tier integration", "Text corrupted"
    assert retrieved.metadata["val"] == 42, "Metadata corrupted"
    assert np.allclose(retrieved.vector, node.vector), "Vector corrupted"
    assert len(retrieved.edges) == 1, "Edges corrupted"
    assert retrieved.edges[0].target_id == "target_123", "Edge target corrupted"
    
    # Test scan_recent
    recent = manager.get_all_recent(limit=10)
    assert len(recent) == 1, f"Expected 1 recent node, got {len(recent)}"
    assert recent[0].id == node.id, "Corrupted ID in scan_recent"

    print("Success! No bugs found in CRUD.")
finally:
    manager.close()
    if test_dir.exists():
         shutil.rmtree(test_dir)
