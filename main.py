import asyncio
import sys
from crawl import crawl_site_async
from json_report import write_json_report


async def main():
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    if len(sys.argv) < 3:
        print("no maximum concurrency provided")
        sys.exit(1)
    if len(sys.argv) < 4:
        print("no maximum number of pages provided")
        sys.exit(1)
    if len(sys.argv) > 5:
        print("too many arguments provided")
        sys.exit(1)
    if not sys.argv[2].isdigit():
        print("maximum concurrency must be an integer")
        sys.exit(1)
    if not sys.argv[3].isdigit():
        print("maximum number of pages must be an integer")
        sys.exit(1)

    BASE_URL = sys.argv[1]
    MAX_CONCURRENCY = int(sys.argv[2])
    MAX_PAGES = int(sys.argv[3])
    print(f"starting crawl of: {BASE_URL}")
    page_data = await crawl_site_async(BASE_URL , MAX_CONCURRENCY, MAX_PAGES)
    write_json_report(page_data)


if __name__ == "__main__":
    asyncio.run(main())
