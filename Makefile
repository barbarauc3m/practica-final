
# Makefile proyecto RPC + servidor sockets + scripts Python

# -------------------------------------------------------------------
# Ficheros RPC
# -------------------------------------------------------------------
RPC_X        = log_rpc.x
RPC_SRCS     = log_rpc.h log_rpc_xdr.c log_rpc_clnt.c log_rpc_svc.c

# -------------------------------------------------------------------
# Servidor de sockets
# -------------------------------------------------------------------
SOCK_SRC     = servidor.c
SOCK_BIN     = servidor

# -------------------------------------------------------------------
# Detectar servidor_rpc.c 
# -------------------------------------------------------------------
RPC_SRC      := $(wildcard servidor_rpc.c)
RPC_BIN      := $(RPC_SRC:.c=)

# -------------------------------------------------------------------
# Scripts Python
# -------------------------------------------------------------------
CLIENT_PY    = client.py
WEB_PY       = servicio-web.py

# -------------------------------------------------------------------
# Herramientas y flags
# -------------------------------------------------------------------
CC           = gcc
RPCGEN       = rpcgen
RPCGENFLAGS  = -NMa
PYTHON       = python3
CFLAGS       = -Wall -g -I/usr/include/tirpc -Wno-unused-variable
LDLIBS       = -lpthread -ltirpc

.PHONY: all client web clean

# -------------------------------------------------------------------
# 1) Por defecto: genera stubs y compila servidores
# -------------------------------------------------------------------
all: $(SOCK_BIN) $(RPC_BIN)

# -------------------------------------------------------------------
# 2) Generar stubs RPC (modo antiguo + ANSI = -NMa)
#    Se invoca automáticamente si faltan o están desactualizados
# -------------------------------------------------------------------
$(RPC_SRCS): $(RPC_X)
	@echo ">>> Generando stubs RPC (rpcgen $(RPCGENFLAGS)) desde $<..."
	$(RPCGEN) $(RPCGENFLAGS) $<

# -------------------------------------------------------------------
# 3) Compilar servidor de sockets
# -------------------------------------------------------------------
$(SOCK_BIN): $(SOCK_SRC) log_rpc_clnt.c log_rpc_xdr.c
	@echo ">>> Compilando servidor de sockets..."
	$(CC) $(CFLAGS) \
	  $(SOCK_SRC) log_rpc_clnt.c log_rpc_xdr.c \
	  -o $(SOCK_BIN) \
	  $(LDLIBS)

# -------------------------------------------------------------------
# 4) Compilar servidor RPC (sólo si existe el .c)
# -------------------------------------------------------------------
ifneq ($(RPC_SRC),)
$(RPC_BIN): $(RPC_SRC) log_rpc_svc.c log_rpc_xdr.c
	@echo ">>> Compilando servidor RPC ($(RPC_SRC))..."
	$(CC) $(CFLAGS) \
	  $(RPC_SRC) log_rpc_svc.c log_rpc_xdr.c \
	  -o $(RPC_BIN) \
	  $(LDLIBS)
endif

# -------------------------------------------------------------------
# 5) Ejecutar cliente y servicio web
# -------------------------------------------------------------------
client:
	@echo ">>> Ejecutando cliente Python..."
	$(PYTHON) $(CLIENT_PY) -s localhost -p 5000

web:
	@echo ">>> Ejecutando servicio web..."
	$(PYTHON) $(WEB_PY)

# -------------------------------------------------------------------
# 6) Limpiar binarios y stubs RPC generados
# -------------------------------------------------------------------
clean:
	@echo ">>> Limpiando binarios y stubs RPC..."
	rm -f $(SOCK_BIN) $(RPC_BIN) $(RPC_SRCS) log_rpc_server.c log_rpc_client.c Makefile.log_rpc
