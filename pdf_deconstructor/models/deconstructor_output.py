from typing import Generator

from pydantic import BaseModel

from . import HeaderContent


class DeconstructorOutput(BaseModel):

    markdown: str  # unparsed text
    headers: list[HeaderContent]  # parsed text
    links: list[str]  # links found within the whole document

    def tree(self) -> None:
        """Print the hierarchy tree for all the content"""

        for header in self.headers:
            header.tree()

    def iterate(self) -> Generator[HeaderContent, None, None]:

        items = []
        for header in self.headers:
            items.extend(header.iterate())

        for item in items:
            yield item
