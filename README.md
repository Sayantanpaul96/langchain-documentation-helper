# Important learnings during the development:

## Tavily tools mainly crawl and map, extract and their usage :D
    - TavilyCrawl does not completely invalidate TavilyMap and TavilyExtract—it combines their functionalities into a single tool, but you may still want to use the separate tools when you only need one part of the workflow or desire finer‑grained control.

    - TavilyMap → returns just a site map (list of discovered URLs) without extracting page content.
    Useful if you only want to know what URLs exist on a domain (e.g., for indexing, link analysis) and don’t need the actual page text.
    - TavilyExtract → takes a list of URLs you provide and returns the extracted text/content from each.
    Useful when you already have a specific set of URLs (e.g., from a sitemap, database, or manual list) and just need to pull the content.
    - TavilyCrawl → performs both steps automatically: it crawls a domain (like Map) to discover URLs up to your depth/breadth limits, then extracts the content from each discovered URL (like Extract).
    The output is a JSON object containing the base URL, crawled results (each with url, raw_content, favicon, etc.), response time, usage credits, and a request ID.

    When to prefer each:

    - Use TavilyCrawl when you want to explore a site and get the text content of all reachable pages within your limits—it replaces a Map → Extract sequence.
    - Use TavilyMap alone when you only need the URL structure (e.g., to feed another process, check for broken links, or build a URL list without downloading content).
    - Use TavilyExtract alone when you already have a URL list and just want to pull the text—avoids the overhead of re‑crawling.

    In short: TavilyCrawl is a convenient all‑in‑one option for crawling + extraction, but the separate Map and Extract tools remain valuable for more targeted or modular workflows.

    Sources:
    - Tavily Crawl output (JSON with base URL, results containing url and raw_content): https://docs.tavily.com/documentation/api-reference/endpoint/crawl
    - Tavily Map (returns site map/URL list): https://docs.tavily.com/documentation/api-reference/endpoint/map
    - Tavily Extract (takes URLs, returns extracted content): https://docs.tavily.com/documentation/api-reference/endpoint/extract
    - LangChain TavilyCrawl reference: https://reference.langchain.com/python/langchain-tavily/tavily_crawl/TavilyCrawl
    - LangChain TavilyMap reference: https://reference.langchain.com/python/langchain-tavily/tavily_map/TavilyMap
    - LangChain TavilyExtract reference: https://reference.langchain.com/python/langchain-tavily/tavily_extract/TavilyExtract