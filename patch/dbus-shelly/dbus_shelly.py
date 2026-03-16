--- /mnt/r/v3.71/opt/victronenergy/dbus-shelly/dbus_shelly.py	2026-03-15 17:32:01.000000000 +0100
+++ /tmp/dbus_shelly.py	2026-03-16 16:09:51.081586215 +0100
@@ -78,8 +78,8 @@
 
 def main():
 	parser = ArgumentParser(description=sys.argv[0])
-	parser.add_argument('--dbus', help='dbus bus to use, defaults to system',
-			default='system')
+	parser.add_argument('--dbus', help='dbus bus to use, defaults to session',
+			default='session')
 	parser.add_argument('--debug', help='Turn on debug logging',
 			default=False, action='store_true')
 	args = parser.parse_args()
@@ -97,20 +97,13 @@
 
 	shellyDiscovery = ShellyDiscovery(bus_type)
 
-	mainloop = asyncio.new_event_loop()
-	asyncio.set_event_loop(mainloop)
+    async def _main():
+	    await shellyDiscovery.start()
+		await websockets.serve(Server(lambda: Meter(bus_type)), '', 8000+int(os.environ.get("SCREEN",1)))
 
-	# This loop should be removed one day.
-	mainloop.run_until_complete(
-		websockets.serve(Server(lambda: Meter(bus_type)), '', 8000))
 
-	mainloop.run_until_complete(shellyDiscovery.start())
-
-	try:
 		logger.info("Starting main loop")
-		mainloop.run_forever()
-	except KeyboardInterrupt:
-		mainloop.stop()
+    asyncio.run(_main())
 
 
 if __name__ == "__main__":
