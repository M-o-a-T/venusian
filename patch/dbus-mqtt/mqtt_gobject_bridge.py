--- /opt/victronenergy/dbus-mqtt/mqtt_gobject_bridge.py	2025-02-10 22:36:17.000000000 +0100
+++ /tmp/mqtt_gobject_bridge.py	2025-02-24 10:31:45.802900668 +0100
@@ -22,7 +22,7 @@
 		self._mqtt_user = user
 		self._mqtt_passwd = passwd
 		self._mqtt_server = mqtt_server or '127.0.0.1'
-		self._client = paho.mqtt.client.Client(client_id)
+		self._client = paho.mqtt.client.Client(paho.mqtt.client.CallbackAPIVersion.VERSION1, client_id)
 		self._client.on_connect = self._on_connect
 		self._client.on_message = self._on_message
 		self._client.on_disconnect = self._on_disconnect
