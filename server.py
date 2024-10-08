import asyncio
from aiosmtpd.controller import Controller


class CustomSMTPHandler:
    async def handle_DATA(self, server, session, envelope):
        print(f"Received message from: {envelope.mail_from}")
        print(f"To: {envelope.rcpt_tos}")
        print(f"Message: {envelope.content.decode()}")
        return '250 Message accepted for delivery'


async def main():
    handler = CustomSMTPHandler()
    controller = Controller(handler, port=1025)
    controller.start()
    print("SMTP server is running on localhost:1025")

    try:
        await asyncio.Event().wait()  # Wait indefinitely
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()


if __name__ == "__main__":
    asyncio.run(main())
