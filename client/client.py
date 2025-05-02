# python3 client.py -s localhost -p 5000


from enum import Enum
import argparse
# Nuevos imports
import socket
import threading
import os

class client :

    # ******************** TYPES *********************
    # *
    # * @brief Return codes for the protocol methods
    class RC(Enum) :
        OK = 0
        ERROR = 1
        USER_ERROR = 2

    # ****************** ATTRIBUTES ******************
    _server = None
    _port = -1
    # Nuevos atributos:
    _listen_port = None
    _listen_socket = None
    _listen_thread = None
    _current_user = None
    _running = True

    # ******************** METHODS *******************


    @staticmethod
    def  register(user) :
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"REGISTER\0" + user.encode() + b"\0")
                response = s.recv(1)
                
                if response == b'\x00':
                    print("c> REGISTER OK")
                    return client.RC.OK
                elif response == b'\x01':
                    print("c> USERNAME IN USE")
                    return client.RC.USER_ERROR
                else:
                    print("c> REGISTER FAIL")
                    return client.RC.ERROR
        except Exception as e:
            print("c> REGISTER FAIL")
            return client.RC.ERROR

   
    @staticmethod
    def  unregister(user) :
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"UNREGISTER\0" + user.encode() + b"\0")
                response = s.recv(1)
                
                if response == b'\x00':
                    print("c> UNREGISTER OK")
                    return client.RC.OK
                elif response == b'\x01':
                    print("c> USER DOES NOT EXIST")
                    return client.RC.USER_ERROR
                else:
                    print("c> UNREGISTER FAIL")
                    return client.RC.ERROR
        except Exception as e:
            print("c> UNREGISTER FAIL")
            return client.RC.ERROR


    
    @staticmethod
    def connect(user):
        try:
            # 1. Crear socket de escucha (servidor) en un puerto libre
            listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_socket.bind(('', 0))  # El sistema elige un puerto libre
            listen_socket.listen(5)
            client._listen_socket = listen_socket
            client._listen_port = listen_socket.getsockname()[1]
            client._current_user = user

            # 2. Crear el hilo que escuchará peticiones (se implementará más adelante)
            def listen():
                while client._running:
                    try:
                        conn, addr = listen_socket.accept()
                        # Aquí en el futuro se atenderán GET_FILE
                        conn.close()
                    except:
                        break

            client._listen_thread = threading.Thread(target=listen, daemon=True)
            client._listen_thread.start()

            # 3. Conectar con el servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"CONNECT\0" + user.encode() + b"\0" + str(client._listen_port).encode()) # + b"\0")
                response = s.recv(1) # Para recibir 1 byte (que es el resultado de la operación (0, 1, 2, 3))

            # 4. Interpretar respuesta
            if response == b'\x00':
                print("c> CONNECT OK")
                return client.RC.OK
            elif response == b'\x01':
                print("c> CONNECT FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response == b'\x02':
                print("c> USER ALREADY CONNECTED")
                return client.RC.USER_ERROR
            else:
                print("c> CONNECT FAIL")
                return client.RC.ERROR

        except Exception as e:
            print("c> CONNECT FAIL")
            return client.RC.ERROR



    
    @staticmethod
    def disconnect(user):
        try:
            # 1. Enviar mensaje al servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"DISCONNECT\0" + user.encode() + b"\0")
                response = s.recv(1)

            # 2. Interpretar respuesta del servidor
            if response == b'\x00':
                print("c> DISCONNECT OK")
            elif response == b'\x01':
                print("c> DISCONNECT FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response == b'\x02':
                print("c> DISCONNECT FAIL, USER NOT CONNECTED")
                return client.RC.USER_ERROR
            else:
                print("c> DISCONNECT FAIL")
                return client.RC.ERROR

            # 3. Parar el hilo y cerrar el socket de escucha
            client._running = False
            if client._listen_socket:
                try:
                    client._listen_socket.close()
                except:
                    pass
                client._listen_socket = None

            client._listen_thread = None
            client._listen_port = None
            client._current_user = None

            return client.RC.OK

        except Exception as e:
            print("c> DISCONNECT FAIL")
            return client.RC.ERROR


    @staticmethod
    def publish(fileName, description):
        if client._current_user is None:
            print("c> PUBLISH FAIL, NOT CONNECTED")
            return client.RC.USER_ERROR

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"PUBLISH\0" +
                        client._current_user.encode() + b"\0" +
                        fileName.encode() + b"\0" +
                        description.encode() + b"\0")

                response = s.recv(1)

            if response == b'\x00':
                print("c> PUBLISH OK")
                return client.RC.OK
            elif response == b'\x01':
                print("c> PUBLISH FAIL, USER DOES NOT EXIST")
            elif response == b'\x02':
                print("c> PUBLISH FAIL, USER NOT CONNECTED")
            elif response == b'\x03':
                print("c> PUBLISH FAIL, CONTENT ALREADY PUBLISHED")
            else:
                print("c> PUBLISH FAIL")
            return client.RC.USER_ERROR

        except Exception as e:
            print("c> PUBLISH FAIL")
            return client.RC.ERROR


    @staticmethod
    def delete(fileName):
        if client._current_user is None:
            print("c> DELETE FAIL, NOT CONNECTED")
            return client.RC.USER_ERROR

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"DELETE\0" +
                        client._current_user.encode() + b"\0" +
                        fileName.encode() + b"\0")

                response = s.recv(1)

            if response == b'\x00':
                print("c> DELETE OK")
                return client.RC.OK
            elif response == b'\x01':
                print("c> DELETE FAIL, USER DOES NOT EXIST")
            elif response == b'\x02':
                print("c> DELETE FAIL, USER NOT CONNECTED")
            elif response == b'\x03':
                print("c> DELETE FAIL, FILE NOT FOUND")
            else:
                print("c> DELETE FAIL")
            return client.RC.USER_ERROR

        except Exception as e:
            print("c> DELETE FAIL")
            return client.RC.ERROR


    @staticmethod
    def listusers():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"LIST_USERS\0" + client._current_user.encode() + b"\0")  # Enviamos también el usuario, aunque no hacemos nada con él.
                # s.sendall(b"LIST_USERS\0")

                # Primero leemos el código de resultado
                result = s.recv(1)
                if result != b'\x00':
                    print("c> LIST_USERS FAIL")
                    return client.RC.ERROR

                # Leer datos hasta encontrar doble \0 (por seguridad usamos BUFFER_SIZE)
                data = bytearray()
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    if data[-2:] == b'\0\0':
                        break

                users = data[:-2].split(b'\0')  # Quitamos el doble \0 final
                print("c> CONNECTED USERS:")
                for user in users:
                    print("   -", user.decode())

                return client.RC.OK

        except Exception as e:
            print("c> LIST_USERS FAIL")
            return client.RC.ERROR


    @staticmethod
    def  listcontent(user) :
        #  Write your code here
        return client.RC.ERROR

    @staticmethod
    def  getfile(user,  remote_FileName,  local_FileName) :
        #  Write your code here
        return client.RC.ERROR

    # *
    # **
    # * @brief Command interpreter for the client. It calls the protocol functions.
    @staticmethod
    def shell():

        while (True) :
            try :
                command = input("c> ")
                line = command.split(" ")
                if (len(line) > 0):

                    line[0] = line[0].upper()

                    if (line[0]=="REGISTER") :
                        if (len(line) == 2) :
                            client.register(line[1])
                        else :
                            print("Syntax error. Usage: REGISTER <userName>")

                    elif(line[0]=="UNREGISTER") :
                        if (len(line) == 2) :
                            client.unregister(line[1])
                        else :
                            print("Syntax error. Usage: UNREGISTER <userName>")

                    elif(line[0]=="CONNECT") :
                        if (len(line) == 2) :
                            client.connect(line[1])
                        else :
                            print("Syntax error. Usage: CONNECT <userName>")
                    
                    elif(line[0]=="PUBLISH") :
                        if (len(line) >= 3) :
                            #  Remove first two words
                            description = ' '.join(line[2:])
                            client.publish(line[1], description)
                        else :
                            print("Syntax error. Usage: PUBLISH <fileName> <description>")

                    elif(line[0]=="DELETE") :
                        if (len(line) == 2) :
                            client.delete(line[1])
                        else :
                            print("Syntax error. Usage: DELETE <fileName>")

                    elif(line[0]=="LIST_USERS") :
                        if (len(line) == 1) :
                            client.listusers()
                        else :
                            print("Syntax error. Use: LIST_USERS")

                    elif(line[0]=="LIST_CONTENT") :
                        if (len(line) == 2) :
                            client.listcontent(line[1])
                        else :
                            print("Syntax error. Usage: LIST_CONTENT <userName>")

                    elif(line[0]=="DISCONNECT") :
                        if (len(line) == 2) :
                            client.disconnect(line[1])
                        else :
                            print("Syntax error. Usage: DISCONNECT <userName>")

                    elif(line[0]=="GET_FILE") :
                        if (len(line) == 4) :
                            client.getfile(line[1], line[2], line[3])
                        else :
                            print("Syntax error. Usage: GET_FILE <userName> <remote_fileName> <local_fileName>")

                    elif(line[0]=="QUIT") :
                        if (len(line) == 1) :
                            break
                        else :
                            print("Syntax error. Use: QUIT")
                    else :
                        print("Error: command " + line[0] + " not valid.")
            except Exception as e:
                print("Exception: " + str(e))

    # *
    # * @brief Prints program usage
    @staticmethod
    def usage() :
        print("Usage: python3 client.py -s <server> -p <port>")


    # *
    # * @brief Parses program execution arguments
    @staticmethod
    def  parseArguments(argv) :
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', type=str, required=True, help='Server IP')
        parser.add_argument('-p', type=int, required=True, help='Server Port')
        args = parser.parse_args()

        if (args.s is None):
            parser.error("Usage: python3 client.py -s <server> -p <port>")
            return False

        if ((args.p < 1024) or (args.p > 65535)):
            parser.error("Error: Port must be in the range 1024 <= port <= 65535");
            return False;
        
        client._server = args.s
        client._port = args.p

        return True


    # ******************** MAIN *********************
    @staticmethod
    def main(argv) :
        if (not client.parseArguments(argv)) :
            client.usage()
            return

        #  Write code here
        client.shell()
        print("+++ FINISHED +++")
    

if __name__=="__main__":
    client.main([])