def urljoin(first: str, *urls) -> str:
    res = first
    for url in urls:
        if '//' in url:
            res = url
        else:
            res = res.rstrip('/') + '/' + url.lstrip('/')
    return res
