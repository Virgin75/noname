

@dataclass
class InternalLink:
    """
    Represents an internal link found in a webpage.

    Kwargs for initialization:
    -------------------------
      from_page (str): The URL of the page where the link was found.
      to_page (str): The URL of the page the link points to.
      anchor_text (str): The anchor text of the link.
      from_page_depth (int):  Depth of the page on which the link was found.
    """
    from_page: str
    to_page: str
    anchor_text: str = ""
    from_page_anchor_text: int = 0


@dataclass
class Page:
    """
    Represents a webpage discovered by a Crawler.
    """

    url: str
    page_depth: int
    meta_title: str
    meta_description: str

    def __eq__(self, other):
        """Consider two Pages are equal if their URLs are equal."""
        return self.url == other.url

    def __hash__(self):
        """Return the hash of the URL."""
        return hash(self.url)


