#!/usr/bin/env python3
import asyncio,json,sys
async def main(host: str, port: int) -> None:
    reader,writer = await asyncio.open_connection(host,port)
    for request in [
        {"id":1,"method":"mining.subscribe","params":["seymour-smoke/1.0"]},
        {"id":2,"method":"mining.authorize","params":["test.worker","x"]},
    ]:
        writer.write(json.dumps(request).encode()+b"\n")
        await writer.drain()
    for _ in range(4):
        print((await asyncio.wait_for(reader.readline(),5)).decode().rstrip())
    writer.close()
    await writer.wait_closed()
if __name__ == "__main__":
    asyncio.run(main(
        sys.argv[1] if len(sys.argv)>1 else "127.0.0.1",
        int(sys.argv[2]) if len(sys.argv)>2 else 3333,
    ))
