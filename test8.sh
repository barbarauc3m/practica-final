# test8.sh: Prueba concurrente de PUBLISH y LIST_CONTENT
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

echo "== Test8: Concurrente PUBLISH y LIST_CONTENT =="

# Registrar y conectar varios usuarios en paralelo
for i in {1..20}; do
  printf "REGISTER usr$i\nCONNECT usr$i\nQUIT\n" | $CLIENT &
  sleep 0.05
done
wait

# Cada usuario publica y lista en paralelo
for i in {1..20}; do
  printf "PUBLISH file$i.txt File$i\nLIST_CONTENT usr$i\nDISCONNECT usr$i\nUNREGISTER usr$i\nQUIT\n" | $CLIENT &
done
wait

echo "== Test8: Finalizado =="