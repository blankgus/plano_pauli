
### 2. **Arquivo: `setup_production.py`** (Script automático)

#python
#!/usr/bin/env python
#
#Script para preparar o sistema para produção
#
import os
import sys
import shutil

def setup_production():
    """Prepara todos os arquivos para produção"""
    
    print("=" * 60)
    print("🚀 PREPARANDO SISTEMA PARA PRODUÇÃO")
    print("=" * 60)
    
    # 1. Criar estrutura de pastas
    folders = ['static/css', 'static/js', 'templates', 'data']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✅ Criada pasta: {folder}")
    
    # 2. Criar arquivos de produção
    production_files = {
        'Procfile': 'web: gunicorn app:app\n',
        'runtime.txt': 'python-3.11.0\n',
        'render.yaml': '''services:
  - type: web
    name: business-plan-escolar
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
    plan: free
    autoDeploy: true\n''',
        
        'gunicorn_config.py': '''import multiprocessing

# Configurações do Gunicorn
bind = "0.0.0.0:10000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5\n''',
        
        'wsgi.py': '''import sys
import os

# Adiciona o diretório do projeto ao path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from app import app as application

# Inicializar banco de dados
with application.app_context():
    from app import init_db
    init_db()\n''',
        
        'deploy_instructions.md': open('deploy_instructions.md', 'r', encoding='utf-8').read() if os.path.exists('deploy_instructions.md') else '# Instruções de Deploy\n'
    }
    
    for filename, content in production_files.items():
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Criado arquivo: {filename}")
    
    # 3. Verificar se app.py existe
    if not os.path.exists('app.py'):
        print("❌ ERRO: Arquivo app.py não encontrado!")
        return False
    
    # 4. Atualizar requirements.txt para produção
    requirements = '''Flask==2.3.3
gunicorn==20.1.0'''
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(requirements)
    print("✅ Requirements.txt atualizado para produção")
    
    # 5. Criar README.md se não existir
    if not os.path.exists('README.md'):
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write('''# Sistema de Business Plan Escolar

## 🌐 ACESSO ONLINE
O sistema está disponível em: [INSIRA_SUA_URL_AQUI]

## 🚀 COMO USAR
1. Acesse a URL acima
2. Clique em "Nova Simulação"
3. Preencha os dados da escola
4. Veja os resultados e projeções

## 📊 FUNCIONALIDADES
- Simulação de aumento de 30-50% nas matrículas
- Cálculo de ROI e Payback
- Dashboard com histórico
- Relatórios detalhados

## 🛠️ TECNOLOGIAS
- Python + Flask
- SQLite
- Bootstrap 5
- Chart.js

## 📞 SUPORTE
Para suporte técnico, entre em contato com o administrador do sistema.
''')
        print("✅ README.md criado")
    
    print("\n" + "=" * 60)
    print("✅ PREPARAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Escolha uma plataforma (Render.com recomendado)")
    print("2. Siga as instruções em deploy_instructions.md")
    print("3. Faça o deploy e compartilhe o link!")
    print("\n💡 DICA: Para Render.com:")
    print("   - Crie conta em https://render.com")
    print("   - Faça upload dos arquivos ou conecte GitHub")
    print("   - Seu site estará online em 5 minutos!")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    setup_production()