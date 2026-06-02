import os
import re
import datetime
from typing import Dict, Any

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

class WikiIngestor:
    """
    Ingests external resources (files) into the Memory system by wrapping
    them in Wiki-friendly Markdown with YAML frontmatter. This output
    is compatible with the indexing pipeline (Component 3).
    """
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.sources_dir = os.path.join(workspace_dir, "memory", "wiki", "sources")
        os.makedirs(self.sources_dir, exist_ok=True)

    def ingest_file(self, file_path: str, title: str = None) -> Dict[str, Any]:
        """
        Reads an external file, asserts it is text, and saves it into the wiki.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        with open(file_path, "rb") as f:
            buffer = f.read()

        if b'\x00' in buffer[:4096]:
            raise ValueError(f"Cannot ingest binary file as markdown source: {file_path}")

        try:
            content = buffer.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"Source file must be utf-8 encoded: {file_path}")

        if not title:
            base = os.path.basename(file_path)
            title = os.path.splitext(base)[0].replace("-", " ").replace("_", " ").title()

        slug = slugify(title)
        page_id = f"source.{slug}"
        relative_path = os.path.join("sources", f"{slug}.md")
        page_path = os.path.join(self.sources_dir, f"{slug}.md")
        
        created = not os.path.exists(page_path)
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # Construct wiki-compliant markdown with frontmatter
        markdown_lines = [
            "---",
            "pageType: source",
            f"id: {page_id}",
            f"title: \"{title}\"",
            "sourceType: local-file",
            f"sourcePath: \"{file_path}\"",
            f"ingestedAt: {timestamp}",
            "status: active",
            "---",
            f"# {title}",
            "",
            "## Source Metadata",
            "- Type: `local-file`",
            f"- Path: `{file_path}`",
            f"- Bytes: {len(buffer)}",
            f"- Updated: {timestamp}",
            "",
            "## Content",
            "```text",
            content,
            "```",
            "",
            "## Notes",
            "<!-- openclaw:human:start -->",
            "<!-- openclaw:human:end -->",
            ""
        ]

        with open(page_path, "w", encoding="utf-8") as out_f:
            out_f.write("\n".join(markdown_lines))

        return {
            "sourcePath": file_path,
            "pageId": page_id,
            "pagePath": relative_path,
            "title": title,
            "bytes": len(buffer),
            "created": created
        }
