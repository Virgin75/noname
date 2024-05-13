# Data to retrieve from first scrap:
- Internal links
- Pages:
  - url
  - depth
  - sha256 (html + js)
  - sha_updated_at
  - title
  - description
  - status_code
  - first_crawled_at (model)
  - url_issue (non ascii char, params, space)
  - good usage of H tags (only one h1 and correct order)
  - Redirects
  - indexation choice:
    - Meta tag name=robots value
    - or http header 'X-Robots-Tag'
    - or sitemap
  - Usage of rel=canonical for pages with query string:
    - <link rel="canonical" href="">
    - or http header rel=canonical
  - Hreflang, either in:
    - <link rel="alternate" hreflang="en" href="">
    - or http header 'Link' with "rel=alternate;hreflang=en"
    - or sitemap
- Other:
  - Duplicate contents