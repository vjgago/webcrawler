import sys
from crawl import crawl_page


def main():
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    if len(sys.argv) > 2:
        print("too many arguments provided")
        sys.exit(1)
    if len(sys.argv) == 2:
        BASE_URL = sys.argv[1]
        print(f"starting crawl of: {BASE_URL}")
        a = crawl_page(BASE_URL)
        print(len(a.keys()))


if __name__ == "__main__":
    main()
