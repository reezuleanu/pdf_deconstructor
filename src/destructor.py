import pymupdf4llm
import re
from collections.abc import Generator


class Deconstructor:

    def __init__(
        self, file_path: str, start_page: int = 0, heading_level: int = 1
    ) -> None:

        # convert pdf to markdown
        self.md_text = "\n".join(
            pymupdf4llm.to_markdown(file_path).split("-----")[start_page:]
        )

        # remove white lines
        self.md_text = self._format(self.md_text)

        # heading level
        self.heading_level = heading_level

        # create hierarchy object
        self.content = self._parse_content(self.md_text.split("\n"))

        # ! LEGACY
        # divide text into pages and topics
        self.md_pages = self.md_text.split("-----")
        self.md_topics = self.md_text.split("###")

        # extract all links
        self.links = re.findall(r'https://[^\s,"]+', self.md_text)

    # TODO fix this mess and find the bug
    def _parse_content(self, text: str) -> list[dict]:
        """Parse markdown content into a hierarchy of items

        Args:
            text (str): markdown text

        Returns:
            dict[str, dict]: object representing contents hierarchly
        """

        def split_headings(
            text: str, heading_level: int = self.heading_level
        ) -> dict[str, str | dict]:

            content = []
            pattern = rf"^({'#'*heading_level} .*)"
            regex = re.compile(pattern, re.MULTILINE)
            headings = []
            for index, line in enumerate(text):
                for match in regex.finditer(line):
                    headings.append(index)

            # if there are no headings
            if len(headings) == 0:
                if heading_level > 8:
                    return
                print("nothing found at level ", heading_level)
                split_headings(text, heading_level + 1)

            for i in range(len(headings)):
                heading_content = {}

                lines = (
                    text[headings[i] : headings[i + 1]]
                    if len(headings) > i + 1
                    else text[headings[i] :]
                )

                # get title
                heading_content["title"] = lines[0].lstrip("# ")

                # get content and subsections
                heading_content["content"] = ""
                heading_content["subsections"] = []
                for j in range(1, len(lines)):

                    # skip empty lines if any
                    if len(lines[j]) < 1:
                        continue
                    # if it reaches a lower headings, go depth first
                    if "#" * (heading_level + 1) in lines[j]:
                        heading_content["subsections"] = split_headings(
                            lines[j:], heading_level + 1
                        )
                        j = j + len(heading_content["subsections"][-1]["content"])
                        break

                    # if it reaches a higher heading, go up
                    elif heading_level > 1 and "#" * (heading_level - 1) in lines[j]:
                        break
                    else:
                        heading_content["content"] = (
                            heading_content["content"] + "\n" + lines[j]
                        )

                # get links
                heading_content["links"] = re.findall(
                    r'https://[^\s,"]+', "\n".join(lines)
                )

                content.append(heading_content)

            return content

        return split_headings(text)

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

    # ! DEPRECATED
    def feed_topic(self, max_lines: int) -> Generator[str]:
        """Provide a topic for LLM processing. If a topic is too big,
        it will get split into separate chunks

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
