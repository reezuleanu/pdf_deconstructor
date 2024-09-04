import pymupdf4llm
import re
from collections.abc import Generator


class Deconstructor:

    def __init__(self, file_path: str) -> None:
        # convert pdf to markdown
        self.md_text = pymupdf4llm.to_markdown(file_path)

        # remove white lines
        self.md_text = self._format(self.md_text)

        # divide text into pages and topics, as well as extract links
        self.md_pages = self.md_text.split("-----")
        self.md_topics = self.md_text.split("###")
        self.md_links = re.findall(r'https://[^\s,"]+', self.md_text)

    def _format(self, text: str) -> str:
        """Remove white lines from markdown text

        Args:
            text (str): text with white lines

        Returns:
            str: text without white lines
        """
        lines = []
        for line in text.split("\n"):
            if len(line) > 0:
                lines.append(line)

        return "\n".join(lines)

    def feed_topic(self, max_lines: int) -> Generator[str]:
        """Provide a topic for LLM processing

        Args:
            max_lines (int): number of maximum lines allowed

        Yields:
            str: text for LLM
        """
        for topic in self.md_topics:
            lines = topic.split("\n")

            # if the topic is too big, it splits it into chunks
            if len(lines) > max_lines:
                for i in range(0, len(lines), max_lines):
                    yield "\n".join(lines[i : i + max_lines])

            # if not, yield the whole topic
            else:
                yield topic

        return None

    def feed_pages(self) -> Generator[str]:
        """Provide a page for LLM processing

        Yields:
            Generator[str]: text for the LLM
        """

        for page in self.md_pages:
            yield page

    def feed_links(self) -> Generator[str]:
        """Provide a link for web scraping

        Yields:
            Generator[str]: link for web scraper
        """

        for link in self.md_links:
            yield link
