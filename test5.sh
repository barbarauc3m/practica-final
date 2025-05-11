# test5.sh: Prueba conectar cliente no registrado
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

echo "== Test5: Intentar conectar sin registrar =="
$CLIENT <<EOF
CONNECT eve
QUIT
EOF
