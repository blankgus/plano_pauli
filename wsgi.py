import sys
import os

# Adiciona o diretório do projeto ao path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from app import app as application

# Inicializar banco de dados
with application.app_context():
    from app import init_db
    init_db()
