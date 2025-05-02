# PDF Deconstructor
Decompose a PDF file based on its headers for RAG ingestion.

## What it does
It takes a PDF file and converts it into a hierarchy of sections and subsections based on the headers inside the file, as well as extract all the links.

## Main use
The intended use is to be part of a larger ingestion pipeline of unstructured data for RAG purposes.

## How to use
```py
from pdf_deconstructor import Deconstructor as PDFDeconstructor

output = PDFDeconstructor.parse("file.pdf", start_page=1)

# to see extracted tree
for header in output.content:
    print(header.tree())
```

Each header contains the raw text, markdown syntax text, and extracted links, as well as sub headers