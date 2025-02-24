--- /opt/venus/opt/victronenergy/dbus-shelly/dbus_shelly.py	2025-02-10 22:25:03.000000000 +0100
+++ /opt/victronenergy/dbus-shelly/dbus_shelly.py	2025-02-24 15:33:09.231998042 +0100
@@ -96,15 +96,11 @@
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
+		await websockets.serve(Server(lambda: Meter(bus_type)), '', 8000+int(os.environ.get("SCREEN",1)))
+		await asyncio.Future()
+	asyncio.run(_main())
 
 
 if __name__ == "__main__":
