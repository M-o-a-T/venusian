--- /opt/venus/opt/victronenergy/dbus-modbus-client/client.py	2025-02-10 22:25:03.000000000 +0100
+++ /tmp/client.py	2025-02-24 10:40:00.815857087 +0100
@@ -3,10 +3,24 @@
 import threading
 import time
 
-from pymodbus.client.sync import *
-from pymodbus.utilities import computeCRC
+from pymodbus.client import *
+try:
+    from pymodbus.utilities import computeCRC
+except ImportError:
+    try:
+        from pymodbus.framer.rtu import FramerRTU as RTU
+    except ImportError:
+        from pymodbus.message.rtu import MessageRTU as RTU
+    computeCRC = RTU.compute_CRC
+try:
+    from pymodbus.framer.rtu_framer import ModbusRtuFramer
+    from pymodbus.framer.ascii_framer import ModbusAsciiFramer
+except ImportError:
+    from pymodbus.framer.rtu import FramerRTU as ModbusRtuFramer
+    from pymodbus.framer.ascii import FramerAscii as ModbusAsciiFramer
 
-class ModbusExtras:
+
+class RefCount:
     def __init__(self, *args, **kwargs):
         super().__init__(*args, **kwargs)
         self.refcount = 1
@@ -33,19 +39,10 @@
         finally:
             self.in_transaction = False
 
-    def read_registers(self, address, count, access, **kwargs):
-        if access == 'holding':
-            return self.read_holding_registers(address, count, **kwargs)
-
-        if access == 'input':
-            return self.read_input_registers(address, count, **kwargs)
-
-        raise Exception('Invalid register access type: %s' % access)
-
-class TcpClient(ModbusExtras, ModbusTcpClient):
+class TcpClient(RefCount, ModbusTcpClient):
     method = 'tcp'
 
-class UdpClient(ModbusExtras, ModbusUdpClient):
+class UdpClient(RefCount, ModbusUdpClient):
     method = 'udp'
 
     @property
@@ -58,25 +55,30 @@
         if self.socket:
             self.socket.settimeout(t)
 
-class SerialClient(ModbusExtras, ModbusSerialClient):
-    def __init__(self, *args, **kwargs):
-        super().__init__(*args, **kwargs)
+class SerialClient(RefCount, ModbusSerialClient):
+    def __init__(self, *args, method = None, **kwargs):
+        if method == "rtu":
+            framer = ModbusRtuFramer
+        elif method == "ascii":
+            framer = ModbusAsciiFramer
+        else:
+            raise ValueError("RTU or ASCII only")
+        self.method = method
+        super().__init__(*args, framer=framer, **kwargs)
         self.lock = threading.RLock()
 
     @property
     def timeout(self):
-        return self._timeout
+        return self.params.timeout
 
     @timeout.setter
     def timeout(self, t):
-        self._timeout = t
-        if self.socket:
-            self.socket.timeout = t
+        self.params.timeout = t
 
     def put(self):
         super().put()
         if self.refcount == 0:
-            del serial_ports[os.path.basename(self.port)]
+            del serial_ports[os.path.basename(self.params.port)]
 
     def execute(self, request=None):
         with self.lock:
@@ -108,7 +110,7 @@
         return client.get()
 
     dev = '/dev/%s' % tty
-    client = SerialClient(m.method, port=dev, baudrate=m.rate)
+    client = SerialClient(port=dev, baudrate=m.rate, method=m.method)
     if not client.connect():
         client.put()
         return None
