from liquidation_acme import binance_liquidations, websocket_uri, process_messages
import asyncio
import colorama

colorama.init()


async def main():
    """
    Executes the main program flow
    """
    tasks = [
        process_messages(),
        binance_liquidations(websocket_uri)
    ]

    while True:
        try:
            await asyncio.gather(*tasks)
        except asyncio.exceptions.CancelledError:
            # Handle task cancellation due to exceptions in other tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            break  # Break out of the loop on other exceptions


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt. Stopping the program.")
