import re
from collections.abc import Generator
import warnings

import pymupdf
import pymupdf4llm
import validators

from .models import HeaderContent, DeconstructorOutput


class Deconstructor:

    def __init__(
        self,
        file_path: str,
        start_page: int = 0,
        heading_level: int = 1,
        external_links: list[tuple] = [],
    ) -> None:
        """
        Args:
            file_path (str): path to the pdf file
            start_page (int, optional): the page from where to start. Defaults to 0.
            heading_level (int, optional): if necessary, specify the maximum heading level
            (3 to get only from heading 2 down, 4 to get only from heading 3 down, etc.). Defaults to 1.
            external_links (list): list of external links to insert in a (link, text) format, the text
            being where to insert the links
        """

        # convert pdf to markdown
        self.md_text = "\n".join(
            pymupdf4llm.to_markdown(file_path).split("-----")[start_page:]
        )

        # extract links
        self.links = self._extract_links(self.md_text)

        # insert external links
        if external_links:
            links = set(self.links)
            for link in [link for link in external_links if link[0] not in links]:

                # if text belonging to link was found, insert link next to it in markdown
                index = self.md_text.find(link[1])
                if index > -1:
                    self.md_text = (
                        self.md_text[: index + len(link[1])]
                        + f" ({link[0]}) "
                        + self.md_text[index + len(link[1]) :]
                    )
                    self.links.append(link[0])

        # remove white lines
        self.md_text = self._format(self.md_text)

        # create hierarchy object
        self.content = self._parse_content(
            self.md_text.split("\n"),
            heading_level=heading_level,
            # external_links=external_links,
        )

        # ! LEGACY
        # divide text into topics
        # self.md_topics = self.md_text.split("###")

        # extract all links
        # self.links = re.findall(r'https://[^\s,"]+', self.md_text)
        # for i in range(len(self.links)):
        #     self.links[i] = self.links[i].removesuffix(")")

    @classmethod
    def parse(
        cls,
        file_path: str,
        start_page: int = 0,
        heading_level: int = 1,
        external_links: list[tuple] = [],
    ) -> DeconstructorOutput:

        object = cls(
            file_path=file_path,
            start_page=start_page,
            heading_level=heading_level,
            external_links=external_links,
        )

        # found nothing, assuming the pdf is too complex
        # and return just the text
        if not object.content:
            warnings.warn("Could not identify a hierarchy of contents")
            return cls.extract(file_path)

        return DeconstructorOutput(
            markdown=object.md_text, headers=object.content, links=object.links
        )

    def _parse_content(
        self,
        text: str,
        heading_level: int = 1,
    ) -> list[HeaderContent]:
        content = []
        pattern = rf"^({'#'*heading_level} .*)"
        regex = re.compile(pattern, re.MULTILINE)
        headings = []
        for index, line in enumerate(text):
            for match in regex.finditer(line):
                headings.append(index)

        # if there are no headings, search a level lower
        if len(headings) < 1:
            if heading_level > 8:
                # after heading 8, return
                return []
            return self._parse_content(text, heading_level + 1)

        for i in range(len(headings)):
            # content structure: {title: TITLE, content: CONTENT, subsections: [{title:TITLE, ...}, ...], links: LINKS}
            heading_content: dict[str, str | dict] = {}

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
                    heading_content["subsections"] = self._parse_content(
                        lines[j:],
                        heading_level + 1,
                    )
                    j = j + len(heading_content["subsections"][-1].content)
                    break

                # if it reaches a higher heading, go up
                elif heading_level > 1 and "#" * (heading_level - 1) in lines[j]:
                    break
                else:
                    heading_content["content"] = (
                        heading_content["content"] + "\n" + lines[j]
                    )

            heading_content["links"] = self._extract_links(text="\n".join(lines))

            # convert header data to HeaderContent instance
            heading = HeaderContent(**heading_content, level=heading_level)
            # append heading data to content list
            content.append(heading)

        return content

    @staticmethod
    def _extract_links(text: str) -> list[str]:
        """Extract all valid links from text

        Args:
            text (str): text

        Returns:
            list[str]: list of links
        """

        # get links
        links = re.findall(r'https://[^\s,"]+', text)

        # remove parenthesis at the end of links
        for i in range(len(links)):

            # in case link is malformed with md syntax
            index = links[i].find("](http")
            if index > -1:
                links[i] = links[i][index:]

            index = links[i].find(")")
            if index > -1:
                links[i] = links[i][:index]

        links = list(set(filter(validators.url, links)))

        return links

    @staticmethod
    def _format(text: str) -> str:
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

    @classmethod
    def extract(cls, file_path: str) -> DeconstructorOutput:
        """Extract all text from a pdf, bypassing parsing it

        Args:
            file_path (str): path to pdf

        Returns:
            DeconstructorOutput: only has 1 header with all the
            content in the file
        """

        # extract text
        with pymupdf.open(file_path) as doc:
            text = "\n".join([page.get_text() for page in doc])

        # extract links
        links = cls._extract_links(text)

        return DeconstructorOutput(
            markdown=text,
            headers=[
                HeaderContent(
                    title="Content",
                    level=1,
                    content=text,
                    subsections=[],
                    links=links,
                )
            ],
            links=links,
        )

    # ! DEPRECATED
    def feed_topic(self, max_lines: int) -> Generator[str, None, None]:
        """DEPRECATED\n
        Provide a topic for LLM processing. If a topic is too big,
        it will get split into separate chunks

        Args:
            max_lines (int): number of maximum lines allowed

        Yields:
            str: text for LLM
        """

        raise DeprecationWarning(
            "I do not remember what this was for but it is no \
            longer maintained"
        )
        for topic in self.md_topics:
            lines = topic.split("\n")

            # if the topic is too big, it splits it into chunks
            if len(lines) > max_lines:
                for i in range(0, len(lines), max_lines):
                    yield "\n".join(lines[i : i + max_lines])

            # if not, yield the whole topic
            else:
                yield topic
