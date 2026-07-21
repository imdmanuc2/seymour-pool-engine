import asyncio
import logging

from seymour_pool_engine.stratum.server import StratumServer


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(StratumServer().serve_forever())


if __name__ == "__main__":
    main()
