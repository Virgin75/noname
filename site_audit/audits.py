

def crawl_depth(url: str = None, page_title: str = None, page_content: str = None, **kwargs) -> float:
    """Return the depth of the page."""
    return kwargs.get("depth", 0)


def has_url_issues(url: str = None, page_title: str = None, page_content: str = None, **kwargs) -> float:
    """Check if the URL has issues."""
    if "err" in url:
        return 0.0
    return 1.0


def has_only_one_h1(url: str = None, page_title: str = None, page_content: str = None, **kwargs) -> float:
    """Check if the HTML has only one H1 tag."""
    if page_content.count("<h1>") == 1:
        return 1.0
    return 0.0
