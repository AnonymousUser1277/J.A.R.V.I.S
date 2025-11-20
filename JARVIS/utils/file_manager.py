"""
File management utility for handling selected files in prompts
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import os
import logging
logger = logging.getLogger(__name__)


@dataclass

class SelectedFile:
    """Enhanced with streaming for large files"""
    
    MAX_CONTENT_BYTES: int = 5 * 1024 * 1024  # 5 MB
    CHUNK_SIZE: int = 1024 * 1024  # 1 MB chunks
    
    def _load_content(self):
        """Load file content with streaming for large files"""
        if not self.is_valid:
            self.content = None
            return
        
        # For small files, load fully
        if self.size <= self.MAX_CONTENT_BYTES:
            self._load_full_content()
        else:
            # For large files, load summary
            self._load_summary()
    
    def _load_full_content(self):
        """Load full file content (for small files)"""
        try:
            # Try text mode first
            with open(self.path, 'r', encoding='utf-8', errors='strict') as f:
                self.content = f.read()
                self.content_is_binary = False
                return
        except UnicodeDecodeError:
            pass
        
        # Binary fallback
        try:
            import base64
            with open(self.path, 'rb') as f:
                raw = f.read()
            self.content = base64.b64encode(raw).decode('ascii')
            self.content_is_binary = True
        except Exception:
            self.content = None
    
    def _load_summary(self):
        """Load file summary (first/last chunks for large files)"""
        try:
            # Read first 2MB and last 2MB
            with open(self.path, 'rb') as f:
                # First chunk
                first_chunk = f.read(2 * 1024 * 1024)
                
                # Last chunk
                f.seek(-2 * 1024 * 1024, 2)  # Seek from end
                last_chunk = f.read()
            
            # Try to decode as text
            try:
                first_text = first_chunk.decode('utf-8', errors='ignore')
                last_text = last_chunk.decode('utf-8', errors='ignore')
                
                self.content = (
                    f"[FILE TOO LARGE - Showing first and last portions]\n\n"
                    f"=== BEGINNING ===\n{first_text}\n\n"
                    f"=== END ===\n{last_text}"
                )
                self.content_is_binary = False
                self.truncated = True
            except:
                # Binary file
                import base64
                self.content = (
                    f"[BINARY FILE - Size: {self._format_size(self.size)}]\n"
                    f"First 2MB (base64): {base64.b64encode(first_chunk).decode('ascii')[:1000]}...\n"
                    f"(Content truncated)"
                )
                self.content_is_binary = True
                self.truncated = True
        
        except Exception as e:
            logger.error(f"Failed to load summary for {self.path}: {e}")
            self.content = f"[ERROR: Could not read file - {e}]"
    
    def stream_content(self, chunk_size: int = None):
        """
        Generator to stream file content in chunks
        Useful for processing large files without loading into memory
        """
        if not self.is_valid:
            return
        
        chunk_size = chunk_size or self.CHUNK_SIZE
        
        try:
            with open(self.path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            logger.error(f"Stream error: {e}")

class FileManager:
    """Manages selected files for AI prompts"""
    
    def __init__(self):
        self.selected_files: List[SelectedFile] = []
    
    def add_file(self, file_path: str) -> bool:
        """Add a file to selection if it exists and isn't already selected"""
        # Normalize path
        file_path = os.path.abspath(file_path)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            return False
        
        # Check if already selected
        if any(f.path == file_path for f in self.selected_files):
            return False
        
        # Create SelectedFile object
        file_name = os.path.basename(file_path)
        selected_file = SelectedFile(path=file_path, name=file_name)
        
        if selected_file.is_valid:
            self.selected_files.append(selected_file)
            return True
        return False
    
    def add_multiple_files(self, file_paths: List[str]) -> tuple[int, int]:
        """
        Add multiple files at once
        Returns (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            if self.add_file(file_path):
                successful += 1
            else:
                failed += 1
        
        return successful, failed
    
    def remove_file(self, file_path: str) -> bool:
        """Remove a file from selection"""
        file_path = os.path.abspath(file_path)
        initial_count = len(self.selected_files)
        self.selected_files = [f for f in self.selected_files if f.path != file_path]
        return len(self.selected_files) < initial_count
    
    def remove_all(self):
        """Clear all selected files"""
        self.selected_files.clear()
    
    def get_valid_files(self) -> List[SelectedFile]:
        """Get only valid (existing) files"""
        return [f for f in self.selected_files if f.is_valid]
    
    def get_invalid_files(self) -> List[SelectedFile]:
        """Get files that no longer exist"""
        return [f for f in self.selected_files if not f.is_valid]
    
    def refresh_validity(self):
        """Check if all files still exist"""
        for file_obj in self.selected_files:
            file_obj.is_valid = os.path.exists(file_obj.path)
            if file_obj.is_valid:
                file_obj.size = os.path.getsize(file_obj.path)
    
    def get_paths_string(self, valid_only: bool = True) -> str:
        """
        Get a formatted string of file paths for the prompt
        
        Returns: Formatted string like:
        ```
        Selected Files:
        1. C:\\path\\to\\file1.txt
        2. C:\\path\\to\\file2.pdf
        ```
        """
        files = self.get_valid_files() if valid_only else self.selected_files
        
        if not files:
            return ""
        
        lines = ["Selected Files:"]
        for idx, file_obj in enumerate(files, 1):
            lines.append(f"{idx}. {file_obj.path}")
        
        return "\n".join(lines)
    
    def get_file_reading_instructions(self) -> str:
        """
        Generate instruction text for the AI to read selected files
        
        Returns: Instruction snippet to include in the prompt
        """
        if not self.selected_files:
            return ""
        
        valid_files = self.get_valid_files()
        if not valid_files:
            return "\n\n⚠️ Selected files are no longer available."

        # Build detailed section with path + content for each valid file
        parts = []
        parts.append("\n\n## Selected Files and Contents\n")
        parts.append("The user provided the following files. For each file the absolute path is given followed by the full file content (or base64 if binary). Use these contents directly when answering the user's request.")

        for idx, fobj in enumerate(valid_files, 1):
            parts.append(f"\n{idx}. Path: {fobj.path}")
            parts.append("Content:")
            if fobj.content is None:
                parts.append("<Could not read file content or file is empty>")
            else:
                if fobj.content_is_binary:
                    parts.append("<BASE64_ENCODED_BINARY_CONTENT>")
                    parts.append(fobj.content)
                else:
                    parts.append("<TEXT_CONTENT_START>")
                    parts.append(fobj.content)
                    parts.append("<TEXT_CONTENT_END>")

        parts.append("\nIMPORTANT: The contents above are the authoritative contents of the files. Use the provided content and access filesystem if required for fulfilling the task.")

        return "\n".join(parts)
    
    @property
    def file_count(self) -> int:
        """Return count of selected files"""
        return len(self.selected_files)
    
    @property
    def valid_file_count(self) -> int:
        """Return count of valid (existing) files"""
        return len(self.get_valid_files())
    
    def to_dict(self) -> dict:
        """Convert manager state to dictionary"""
        return {
            'total_files': self.file_count,
            'valid_files': self.valid_file_count,
            'files': [f.to_dict() for f in self.selected_files]
        }
