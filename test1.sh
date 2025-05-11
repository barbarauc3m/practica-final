# test1.sh: Prueba conexión correcta
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

# Registrar y conectar dos usuarios
echo "== Test1: Prueba conexión correcta =="
$CLIENT <<EOF
REGISTER alice
REGISTER bob
CONNECT alice
CONNECT bob
DISCONNECT alice
DISCONNECT bob
QUIT
EOF
