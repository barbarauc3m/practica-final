# test9.sh: Prueba límite de usuarios (MAX_USERS + 1)
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

echo "== Test9: Registro más allá de MAX_USERS =="
for i in {1..101}; do
  echo "Registering user\$i"
  $CLIENT <<EOF
REGISTER user\$i
QUIT
EOF
done
