---
id: "python-stdlib-xml-elementtree"
title: "XML Parsing with ElementTree"
language: "python"
category: "stdlib"
subcategory: "file-formats"
tags: ["xml", "elementtree", "parse", "xpath", "namespace", "etree"]
version: "3.10+"
retrieval_hint: "XML ElementTree parse XPath namespace find findall iter"
last_verified: "2026-05-24"
confidence: "high"
---

# XML Parsing with ElementTree

## When to Use
- Parsing XML configuration files, RSS feeds, or SOAP responses
- Processing XML data from legacy systems or enterprise APIs
- Reading SVG, SVG, XSLT, or other XML-based formats
- Extracting data from XML documents with known structure

## Standard Pattern

```python
import xml.etree.ElementTree as ET
from pathlib import Path


# --- Parse from string ---
xml_string = """
<catalog>
    <book id="1">
        <title>Python Cookbook</title>
        <author>David Beazley</author>
        <price>45.99</price>
    </book>
    <book id="2">
        <title>Fluent Python</title>
        <author>Luciano Ramalho</author>
        <price>54.99</price>
    </book>
</catalog>
"""

root = ET.fromstring(xml_string)

# --- Find elements ---
for book in root.findall("book"):
    book_id = book.get("id")  # Attribute
    title = book.find("title").text  # Child element text
    price = float(book.find("price").text)
    print(f"[{book_id}] {title}: ${price}")

# --- XPath-like queries ---
expensive = root.findall(".//book[price>50]")  # Books over $50
all_titles = [elem.text for elem in root.iter("title")]  # All title elements

# --- Parse from file ---
tree = ET.parse("data.xml")
root = tree.getroot()

# --- Namespaces ---
ns = {"atom": "http://www.w3.org/2005/Atom"}
feed = ET.parse("feed.xml").getroot()
entries = feed.findall("atom:entry", ns)

# --- Build XML ---
new_catalog = ET.Element("catalog")
book = ET.SubElement(new_catalog, book, attrib={"id": "3"})
ET.SubElement(book, "title").text = "New Book"
ET.SubElement(book, "author").text = "Author Name"

# Write to file
tree = ET.ElementTree(new_catalog)
ET.indent(tree, space="  ")  # Pretty print (Python 3.9+)
tree.write("output.xml", encoding="unicode", xml_declaration=True)
```

## Common Mistakes

```python
# WRONG: Parsing untrusted XML (XXE vulnerability)
tree = ET.parse("user_upload.xml")  # Can read local files, SSRF, etc.

# CORRECT: Defuse XML security risks
import defusedxml.ElementTree as ET
tree = ET.parse("user_upload.xml")

# WRONG: Using .//<tag> when you mean ./<tag>
books = root.findall(".//book")  # Searches ALL descendants (deep)

# CORRECT: Use ./<tag> for direct children only
books = root.findall("./book")  # Only direct children

# WRONG: Not handling missing elements
title = book.find("title").text  # AttributeError if <title> doesn't exist

# CORRECT: Check for None before accessing .text
title_elem = book.find("title")
title = title_elem.text if title_elem is not None else "Unknown"

# WRONG: Iterating with .iter() when you want specific elements
for elem in root.iter():  # Gets ALL elements, including root
    print(elem.tag)

# CORRECT: Use .findall() or .iter("tag") for specific elements
for book in root.findall("book"):
    print(book.find("title").text)
```

## Gotchas
- `findall()` returns direct children only; `iter()` returns all descendants
- Use `.//tag` in XPath to search all descendants, `./tag` for direct children
- Namespace handling requires passing a dict: `find("atom:entry", {"atom": "http://..."})`
- `ET.fromstring()` returns the root element; `ET.parse()` returns an ElementTree
- `element.text` is `None` if the element has no text, not empty string
- `element.get("attr")` returns `None` if attribute doesn't exist (no KeyError)
- Use `defusedxml` for parsing untrusted XML — standard ElementTree is vulnerable to XXE
- `ET.indent()` (Python 3.9+) pretty-prints XML for readable output

## Related
- python/stdlib/json-nested.md
- python/stdlib/file-io.md
- python/web/fastapi/request-validation.md
