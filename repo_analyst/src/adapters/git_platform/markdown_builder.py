"""
Markdown corpus builder for creating prioritized code documentation.
Generates a single markdown file with repository structure and source code.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple

from domain.ports import MarkdownCorpusPort

logger = logging.getLogger(__name__)


class MarkdownCorpusBuilder(MarkdownCorpusPort):
    """
    Builds markdown corpus from repository source code.
    Prioritizes files and respects size limits.
    """

    # File extensions to include (whitelist)
    SOURCE_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.kt', '.scala', '.go', '.rb',
        '.php', '.rs', '.c', '.cpp', '.h', '.hpp', '.cs', '.xml', '.json', '.yml',
        '.yaml', '.ini', '.tf', '.sql', '.sh', '.bat', '.ps1', '.gradle', '.mk',
        '.md', '.html', '.css', '.toml', '.txt'
    }

    # Priority groups (higher priority = included first)
    PRIORITY_GROUPS = {
        1: {'README.md', 'README.MD', 'readme.md', 'LICENSE', 'CHANGELOG.md', 'CONTRIBUTING.md'},
        2: {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.kt', '.go', '.rs'},  # App code
        3: {'.yml', '.yaml', '.json', '.toml', '.xml'},  # Config
        4: {'.md', '.txt', '.sh', '.sql'},  # Documentation and scripts
        5: {'.html', '.css'},  # Frontend
    }

    # Directories to exclude
    EXCLUDE_DIRS = {
        '.git', 'node_modules', 'dist', 'build', 'target', 'venv', '.venv',
        '__pycache__', '.pytest_cache', '.idea', '.vscode', 'vendor',
        'coverage', '.coverage', 'htmlcov', '.tox', 'eggs', '.eggs'
    }

    def build_corpus(
        self,
        repo_path: Path,
        include_patterns: List[str],
        exclude_paths: List[str],
        max_bytes: int
    ) -> Path:
        """
        Build markdown corpus from repository.

        Args:
            repo_path: Path to repository
            include_patterns: File patterns to include (e.g., *.py)
            exclude_paths: Directories to exclude
            max_bytes: Maximum size in bytes (450KB limit)

        Returns:
            Path to generated markdown file
        """
        logger.info(f"Building markdown corpus for {repo_path}")

        # Merge exclude paths
        exclude_dirs = self.EXCLUDE_DIRS.union(set(exclude_paths))

        # Collect all eligible files
        all_files = self._collect_files(repo_path, exclude_dirs)
        logger.info(f"Found {len(all_files)} eligible files")

        # Prioritize files
        prioritized_files = self._prioritize_files(all_files, repo_path)
        logger.info(f"Prioritized {len(prioritized_files)} files")

        # Generate markdown with size limit
        output_path = self._generate_output_path(repo_path)
        file_count, total_size, is_complete = self._write_markdown(
            prioritized_files,
            repo_path,
            output_path,
            max_bytes
        )

        logger.info(
            f"Markdown corpus generated: {output_path} "
            f"({file_count} files, {total_size} bytes, complete={is_complete})"
        )

        return output_path

    def _collect_files(self, repo_path: Path, exclude_dirs: Set[str]) -> List[Path]:
        """Collect all eligible source files."""
        files = []

        for item in repo_path.rglob('*'):
            # Skip directories
            if item.is_dir():
                continue

            # Skip excluded directories
            if any(excluded in item.parts for excluded in exclude_dirs):
                continue

            # Check if file extension is in whitelist
            if item.suffix.lower() in self.SOURCE_EXTENSIONS or item.name in self.PRIORITY_GROUPS[1]:
                files.append(item)

        return files

    def _prioritize_files(self, files: List[Path], repo_path: Path) -> List[Path]:
        """
        Prioritize files based on importance.

        Priority order:
        1. README, LICENSE, root docs
        2. Application code (.py, .js, .java, etc.)
        3. Configuration files
        4. Documentation and scripts
        5. Frontend files
        """
        prioritized = []

        # Priority 1: Special files (README, LICENSE, etc.)
        priority_1 = [f for f in files if f.name in self.PRIORITY_GROUPS[1]]
        prioritized.extend(sorted(priority_1, key=lambda x: x.name))

        # Priority 2: Application code
        priority_2 = [f for f in files if f.suffix in self.PRIORITY_GROUPS[2] and f not in priority_1]
        prioritized.extend(sorted(priority_2, key=lambda x: (len(x.parts), x.name)))

        # Priority 3: Configuration
        priority_3 = [f for f in files if f.suffix in self.PRIORITY_GROUPS[3] and f not in priority_1]
        prioritized.extend(sorted(priority_3, key=lambda x: (len(x.parts), x.name)))

        # Priority 4: Documentation and scripts
        priority_4 = [f for f in files if f.suffix in self.PRIORITY_GROUPS[4] and f not in priority_1]
        prioritized.extend(sorted(priority_4, key=lambda x: (len(x.parts), x.name)))

        # Priority 5: Frontend
        priority_5 = [f for f in files if f.suffix in self.PRIORITY_GROUPS[5] and f not in priority_1]
        prioritized.extend(sorted(priority_5, key=lambda x: (len(x.parts), x.name)))

        # Remaining files
        remaining = [f for f in files if f not in prioritized]
        prioritized.extend(sorted(remaining, key=lambda x: (len(x.parts), x.name)))

        return prioritized

    def _generate_output_path(self, repo_path: Path) -> Path:
        """Generate output path with timestamp."""
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        filename = f"{repo_path.name}_corpus_{timestamp}.md"
        output_path = repo_path / filename
        return output_path

    def _write_markdown(
        self,
        files: List[Path],
        repo_path: Path,
        output_path: Path,
        max_bytes: int
    ) -> Tuple[int, int, bool]:
        """
        Write markdown corpus with size limit.

        Returns:
            Tuple of (file_count, total_size, is_complete)
        """
        current_size = 0
        file_count = 0
        is_complete = True

        with open(output_path, 'w', encoding='utf-8') as md_file:
            # Header
            header = f"# Repository: {repo_path.name}\n\n"
            header += f"Generated: {datetime.utcnow().isoformat()}\n\n"
            header += "## Directory Structure\n\n"
            md_file.write(header)
            current_size += len(header.encode('utf-8'))

            # Directory tree
            tree = self._generate_tree(files, repo_path)
            md_file.write(tree)
            md_file.write("\n\n")
            current_size += len(tree.encode('utf-8'))

            # File contents
            md_file.write("## File Contents\n\n")
            current_size += len("## File Contents\n\n".encode('utf-8'))

            for file_path in files:
                # Check size limit
                if current_size >= max_bytes:
                    is_complete = False
                    break

                try:
                    # Read file content
                    content = file_path.read_text(encoding='utf-8', errors='ignore')

                    # Generate markdown section
                    rel_path = file_path.relative_to(repo_path)
                    section = f"### {rel_path}\n\n"
                    section += f"```{file_path.suffix[1:]}\n"
                    section += content
                    section += "\n```\n\n"

                    section_size = len(section.encode('utf-8'))

                    # Check if adding this file would exceed limit
                    if current_size + section_size > max_bytes:
                        is_complete = False
                        break

                    md_file.write(section)
                    current_size += section_size
                    file_count += 1

                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")
                    continue

            # Add note if incomplete
            if not is_complete:
                note = "\n\n---\n**Note**: Size limit reached. Not all files included.\n"
                md_file.write(note)
                current_size += len(note.encode('utf-8'))

        return file_count, current_size, is_complete

    def _generate_tree(self, files: List[Path], repo_path: Path) -> str:
        """Generate simple directory tree."""
        tree_lines = ["```"]
        tree_lines.append(str(repo_path.name) + "/")

        # Group by directory
        dirs = set()
        for file_path in files:
            rel_path = file_path.relative_to(repo_path)
            for parent in rel_path.parents:
                if parent != Path('.'):
                    dirs.add(parent)

        # Sort directories
        sorted_dirs = sorted(dirs, key=lambda x: (len(x.parts), str(x)))

        for dir_path in sorted_dirs:
            indent = "  " * len(dir_path.parts)
            tree_lines.append(f"{indent}{dir_path.name}/")

        # Add files
        for file_path in sorted(files, key=lambda x: (x.parent, x.name)):
            rel_path = file_path.relative_to(repo_path)
            indent = "  " * len(rel_path.parts)
            tree_lines.append(f"{indent}{rel_path.name}")

        tree_lines.append("```")
        return "\n".join(tree_lines)
