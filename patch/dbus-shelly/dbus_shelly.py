--- /opt/venus/opt/victronenergy/dbus-shelly/dbus_shelly.py	2025-02-10 22:25:03.000000000 +0100
+++ /tmp/dbus_shelly.py	2025-02-24 10:43:33.498503085 +0100
@@ -96,15 +96,10 @@
 		"session": BusType.SESSION
 	}.get(args.dbus, BusType.SESSION)
 
-	mainloop = asyncio.get_event_loop()
-	mainloop.run_until_complete(
-		websockets.serve(Server(lambda: Meter(bus_type)), '', 8000))
-
-	try:
-		logger.info("Starting main loop")
-		mainloop.run_forever()
-	except KeyboardInterrupt:
-		mainloop.stop()
+	logger.info("Starting main loop")
+	async def _main():
+		await websockets.serve(Server(lambda: Meter(bus_type)), '', 8000)
+	asyncio.run(_main())
 
 
 if __name__ == "__main__":
