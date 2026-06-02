import pytest
import os
import tempfile
from src.wiki.ingest import WikiIngestor, slugify

def test_slugify():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("some_file_name.txt") == "some-file-name-txt"

def test_ingest_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        ingestor = WikiIngestor(tmpdir)
        
        # Create dummy source
        source_path = os.path.join(tmpdir, "test_doc.txt")
        with open(source_path, "w") as f:
            f.write("This is a test document.")
            
        res = ingestor.ingest_file(source_path)
        assert res["title"] == "Test Doc"
        assert res["created"] is True
        assert res["pageId"] == "source.test-doc"
        
        expected_path = os.path.join(tmpdir, "memory", "wiki", "sources", "test-doc.md")
        assert os.path.exists(expected_path)
        
        with open(expected_path, "r") as f:
            content = f.read()
            
        assert "pageType: source" in content
        assert "This is a test document." in content
        assert "<!-- openclaw:human:start -->" in content

def test_binary_rejection():
    with tempfile.TemporaryDirectory() as tmpdir:
        ingestor = WikiIngestor(tmpdir)
        
        source_path = os.path.join(tmpdir, "test.bin")
        with open(source_path, "wb") as f:
            f.write(b'\x00\x01\x02\x03')
            
        with pytest.raises(ValueError, match="Cannot ingest binary file"):
            ingestor.ingest_file(source_path)
