from liquidation_acme import binance_liquidations, process_symbols, symbols, websocket_uri
import asyncio
import colorama
colorama.init()


async def main():
    """
    Executes the main program flow
    """
    tasks = []
    for symbol in symbols:
        symbol_processing_task = asyncio.create_task(process_symbols(symbol, ""))
        tasks.append(symbol_processing_task)
    liquidations_task = asyncio.create_task(binance_liquidations(websocket_uri))
    await asyncio.gather(*tasks, liquidations_task)


if __name__ == '__main__':
    asyncio.run(main())
