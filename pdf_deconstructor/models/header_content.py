from typing import Self, Generator

from pydantic import BaseModel


class HeaderContent(BaseModel):

    title: str  # header tile
    level: int  # header level (higher level = lower in hierarchy)
    content: str  # text content of the header (excepting content of subsections)
    subsections: list[
        Self
    ]  # subsections, headers within this header with their own content
    links: list[str]  # links found withing this header and its subcontents

    def tree(self) -> None:
        """Print the hierarchy tree for this header"""

        print(" " * self.level, self.title)
        for header in self.subsections:
            header.tree()

    def iterate(self) -> Generator[Self, None, None]:

        if len(self.subsections) < 1:
            return [self]
        else:
            items = []
            if len(self.content) > 1:
                items.append(self)
            for subsection in self.subsections:
                items.extend(subsection.iterate())

            return items
