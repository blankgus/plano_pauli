#!/usr/bin/env python
"""
Script de configuração inicial do sistema de Business Plan
"""
import os
import sys

def setup_environment():
    """Configura o ambiente do projeto"""
    
    print("=" * 60)
    print("CONFIGURAÇÃO DO SISTEMA DE BUSINESS PLAN ESCOLAR")
    print("=" * 60)
    
    # 1. Verificar se a pasta data existe
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        print(f"📁 Criando pasta 'data' em: {data_dir}")
        os.makedirs(data_dir)
    
    # 2. Verificar se requirements.txt existe
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if not os.path.exists(requirements_file):
        print("📄 Criando arquivo requirements.txt...")
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write("""Flask==2.3.3""")
    
    # 3. Criar estrutura de pastas
    folders = ['static/css', 'static/js', 'templates']
    for folder in folders:
        folder_path = os.path.join(os.path.dirname(__file__), folder)
        if not os.path.exists(folder_path):
            print(f"📂 Criando pasta '{folder}'...")
            os.makedirs(folder_path)
    
    # 4. Verificar se os templates existem
    templates = ['base.html', 'index.html', 'simulacao.html', 'resultado.html', 'dashboard.html']
    for template in templates:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', template)
        if not os.path.exists(template_path):
            print(f"📝 Criando template '{template}'...")
            # Criar arquivo básico
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(f"<!-- {template} -->\n")
                f.write("<h1>Template em construção</h1>\n")
    
    # 5. Verificar se os arquivos estáticos existem
    static_files = {
        'static/css/style.css': """/* Estilos do sistema Business Plan */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

.navbar {
    background-color: #2c3e50;
    color: white;
    padding: 15px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.card {
    background: white;
    border-radius: 5px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}""",
        
        'static/js/charts.js': """// Funções para gráficos
function initCharts() {
    console.log('Gráficos inicializados');
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', initCharts);"""
    }
    
    for file_path, content in static_files.items():
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if not os.path.exists(full_path):
            print(f"🎨 Criando arquivo estático '{file_path}'...")
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    print("\n✅ Configuração concluída com sucesso!")
    print("\nPARA EXECUTAR O SISTEMA:")
    print("1. Instale as dependências: pip install -r requirements.txt")
    print("2. Execute o sistema: python app.py")
    print("3. Acesse no navegador: http://localhost:5000")
    print("\n" + "=" * 60)
    
    return True

if __name__ == '__main__':
    setup_environment()