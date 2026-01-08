from flask import Flask, render_template_string, request, jsonify, session, redirect
from datetime import datetime
import json
import math
import os
import sqlite3

app = Flask(__name__)

# Configuração para produção
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'business_plan_escolar_prod_2024_seguro')
app.config['TEMPLATES_AUTO_RELOAD'] = os.environ.get('FLASK_ENV') == 'development'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'data', 'database.db')

# Dados padrão para custos por nível escolar
CUSTOS_POR_NIVEL = {
    'infantil': {
        'custo_professor_por_hora': 45,
        'material_mensal_por_aluno': 80,
        'atividades_especificas': ['Música', 'Artes', 'Psicomotricidade', 'Contação de Histórias'],
        'infraestrutura_especifica': ['Brinquedoteca', 'Parque infantil', 'Sala multiuso'],
        'ratio_professor_aluno': 10  # 1 professor para cada 10 alunos
    },
    'fundamental_i': {
        'custo_professor_por_hora': 50,
        'material_mensal_por_aluno': 60,
        'atividades_especificas': ['Robótica', 'Programação', 'Teatro', 'Esportes', 'Inglês'],
        'infraestrutura_especifica': ['Laboratório de informática', 'Quadra poliesportiva', 'Biblioteca'],
        'ratio_professor_aluno': 15
    },
    'fundamental_ii': {
        'custo_professor_por_hora': 55,
        'material_mensal_por_aluno': 70,
        'atividades_especificas': ['Robótica Avançada', 'Olimpíadas Científicas', 'Debate', 'Música Instrumental', 'Esportes Competitivos'],
        'infraestrutura_especifica': ['Laboratório de ciências', 'Estúdio de música', 'Sala de estudos'],
        'ratio_professor_aluno': 20
    },
    'medio': {
        'custo_professor_por_hora': 65,
        'material_mensal_por_aluno': 90,
        'atividades_especificas': ['Preparatório ENEM', 'Orientação Profissional', 'Projetos Científicos', 'Debates Filosóficos', 'Empreendedorismo'],
        'infraestrutura_especifica': ['Laboratório avançado', 'Sala de projeção', 'Espaço coworking'],
        'ratio_professor_aluno': 25
    }
}

# Categorias detalhadas de custos
CATEGORIAS_CUSTOS = {
    'infraestrutura': {
        'itens': [
            {'nome': 'Reforma de salas', 'custo_base': 5000, 'descricao': 'Adaptação para atividades específicas'},
            {'nome': 'Equipamentos tecnológicos', 'custo_base': 15000, 'descricao': 'Computadores, tablets, projetores'},
            {'nome': 'Materiais esportivos', 'custo_base': 3000, 'descricao': 'Bolas, redes, equipamentos'},
            {'nome': 'Instrumentos musicais', 'custo_base': 8000, 'descricao': 'Violões, teclados, percussão'},
            {'nome': 'Mobiliário especializado', 'custo_base': 7000, 'descricao': 'Mesas, cadeiras, armários'},
            {'nome': 'Kit robótica/programação', 'custo_base': 12000, 'descricao': 'Kits Arduino, impressora 3D'}
        ]
    },
    'material': {
        'itens': [
            {'nome': 'Material didático', 'custo_base': 2000, 'por_aluno': True},
            {'nome': 'Kits de atividades', 'custo_base': 1500, 'por_aluno': True},
            {'nome': 'Uniformes', 'custo_base': 3000, 'por_aluno': True},
            {'nome': 'Material de consumo', 'custo_base': 1000, 'descricao': 'Papel, tinta, etc'},
            {'nome': 'Livros paradidáticos', 'custo_base': 4000, 'por_aluno': True}
        ]
    },
    'marketing': {
        'itens': [
            {'nome': 'Site e redes sociais', 'custo_base': 3000, 'descricao': 'Desenvolvimento e manutenção'},
            {'nome': 'Material impresso', 'custo_base': 1500, 'descricao': 'Folhetos, banners, cartazes'},
            {'nome': 'Eventos de divulgação', 'custo_base': 5000, 'descricao': 'Open school, workshops'},
            {'nome': 'Publicidade online', 'custo_base': 4000, 'descricao': 'Google Ads, redes sociais'},
            {'nome': 'Produção de vídeos', 'custo_base': 6000, 'descricao': 'Vídeos institucionais'}
        ]
    },
    'recursos_humanos': {
        'itens': [
            {'nome': 'Capacitação de professores', 'custo_base': 8000, 'descricao': 'Cursos e workshops'},
            {'nome': 'Contratação especialistas', 'custo_base': 15000, 'descricao': 'Professores específicos'},
            {'nome': 'Equipe de apoio', 'custo_base': 6000, 'descricao': 'Coordenadores, monitores'},
            {'nome': 'Benefícios e encargos', 'custo_base': 10000, 'descricao': 'VT, VR, saúde'}
        ]
    }
}

def init_db():
    """Inicializa o banco de dados SQLite"""
    try:
        data_dir = os.path.join(basedir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data_criacao TEXT,
            alunos_atuais INTEGER,
            mensalidade_media REAL,
            aumento_esperado REAL,
            novos_alunos INTEGER,
            nivel_escolar TEXT,
            atividades_selecionadas TEXT,
            custos_detalhados TEXT,
            receita_mensal_atual REAL,
            receita_projetada REAL,
            investimento_total REAL,
            retorno_mensal REAL,
            payback REAL,
            roi REAL,
            dados TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

def salvar_simulacao(dados_entrada, resultados, custos_detalhados):
    """Salva uma simulação no banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO simulacoes (
            nome, data_criacao, alunos_atuais, mensalidade_media,
            aumento_esperado, novos_alunos, nivel_escolar,
            atividades_selecionadas, custos_detalhados,
            receita_mensal_atual, receita_projetada, investimento_total,
            retorno_mensal, payback, roi, dados
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"Simulação {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            dados_entrada.get('alunos_atuais', 0),
            dados_entrada.get('mensalidade_media', 0),
            dados_entrada.get('aumento_esperado', 0),
            resultados.get('novos_alunos', 0),
            dados_entrada.get('nivel_escolar', 'fundamental_i'),
            json.dumps(dados_entrada.get('atividades_selecionadas', [])),
            json.dumps(custos_detalhados),
            resultados.get('receita_atual', 0),
            resultados.get('receita_projetada', 0),
            resultados.get('investimento_total', 0),
            resultados.get('retorno_mensal', 0),
            resultados.get('payback_meses', 0),
            resultados.get('roi_percentual', 0),
            json.dumps({'entrada': dados_entrada, 'resultados': resultados, 'custos_detalhados': custos_detalhados})
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar simulação: {e}")
        return False

def buscar_simulacoes():
    """Busca todas as simulações do banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulacoes ORDER BY data_criacao DESC')
        simulacoes = cursor.fetchall()
        
        conn.close()
        return simulacoes
    except Exception as e:
        print(f"Erro ao buscar simulações: {e}")
        return []

def buscar_simulacao_por_id(id):
    """Busca uma simulação específica por ID"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulacoes WHERE id = ?', (id,))
        simulacao = cursor.fetchone()
        
        conn.close()
        return simulacao
    except Exception as e:
        print(f"Erro ao buscar simulação: {e}")
        return None

# Funções de cálculo aprimoradas
def calcular_custos_detalhados(dados_entrada):
    """Calcula custos detalhados por categoria"""
    nivel = dados_entrada.get('nivel_escolar', 'fundamental_i')
    alunos_atuais = dados_entrada.get('alunos_atuais', 0)
    novos_alunos = int(alunos_atuais * (dados_entrada.get('aumento_esperado', 0) / 100))
    total_alunos_projetado = alunos_atuais + novos_alunos
    
    # Configurações do nível escolar
    config_nivel = CUSTOS_POR_NIVEL.get(nivel, CUSTOS_POR_NIVEL['fundamental_i'])
    
    # Atividades selecionadas
    atividades_selecionadas = dados_entrada.get('atividades_selecionadas', [])
    num_atividades = len(atividades_selecionadas) if atividades_selecionadas else 3
    
    # Cálculo de professores necessários
    ratio = config_nivel['ratio_professor_aluno']
    professores_necessarios = math.ceil(total_alunos_projetado / ratio)
    
    custos_detalhados = {
        'categorias': {},
        'resumo': {},
        'nivel_escolar': nivel,
        'atividades_selecionadas': atividades_selecionadas
    }
    
    # 1. CUSTOS COM PROFESSORES
    horas_semanais = dados_entrada.get('horas_semanais', 10)
    semanas_mes = 4.3
    custo_hora = config_nivel['custo_professor_por_hora']
    
    custo_professores = professores_necessarios * custo_hora * horas_semanais * semanas_mes
    custos_detalhados['categorias']['professores'] = {
        'total': custo_professores,
        'detalhes': [
            {'item': f'Professores especializados ({professores_necessarios})', 'valor': custo_professores * 0.7},
            {'item': 'Coordenador de atividades', 'valor': custo_professores * 0.2},
            {'item': 'Substituições e reserva', 'valor': custo_professores * 0.1}
        ]
    }
    
    # 2. CUSTOS DE INFRAESTRUTURA (seleção do usuário)
    infra_itens_selecionados = dados_entrada.get('infra_itens_selecionados', [])
    custo_infra = 0
    detalhes_infra = []
    
    for item_nome in infra_itens_selecionados:
        for item in CATEGORIAS_CUSTOS['infraestrutura']['itens']:
            if item['nome'] == item_nome:
                custo_item = item['custo_base']
                # Ajuste por nível escolar
                if nivel == 'infantil':
                    custo_item *= 0.8
                elif nivel == 'medio':
                    custo_item *= 1.2
                
                custo_infra += custo_item
                detalhes_infra.append({
                    'item': item_nome,
                    'valor': custo_item,
                    'descricao': item.get('descricao', '')
                })
                break
    
    if not detalhes_infra:
        # Valor padrão se nenhum item selecionado
        custo_infra = dados_entrada.get('custo_infraestrutura', 1000)
        detalhes_infra.append({
            'item': 'Adaptações básicas',
            'valor': custo_infra,
            'descricao': 'Reformas e adaptações necessárias'
        })
    
    custos_detalhados['categorias']['infraestrutura'] = {
        'total': custo_infra,
        'detalhes': detalhes_infra
    }
    
    # 3. CUSTOS DE MATERIAL (por aluno)
    material_itens_selecionados = dados_entrada.get('material_itens_selecionados', [])
    custo_material = 0
    detalhes_material = []
    
    for item_nome in material_itens_selecionados:
        for item in CATEGORIAS_CUSTOS['material']['itens']:
            if item['nome'] == item_nome:
                if item.get('por_aluno', False):
                    custo_item = item['custo_base'] * total_alunos_projetado
                else:
                    custo_item = item['custo_base']
                
                custo_material += custo_item
                detalhes_material.append({
                    'item': item_nome,
                    'valor': custo_item,
                    'por_aluno': item.get('por_aluno', False)
                })
                break
    
    if not detalhes_material:
        # Valor padrão por aluno
        custo_material_por_aluno = config_nivel['material_mensal_por_aluno']
        custo_material = custo_material_por_aluno * total_alunos_projetado
        detalhes_material.append({
            'item': 'Material didático básico',
            'valor': custo_material,
            'por_aluno': True
        })
    
    custos_detalhados['categorias']['material'] = {
        'total': custo_material,
        'detalhes': detalhes_material
    }
    
    # 4. CUSTOS DE MARKETING
    marketing_itens_selecionados = dados_entrada.get('marketing_itens_selecionados', [])
    custo_marketing = 0
    detalhes_marketing = []
    
    for item_nome in marketing_itens_selecionados:
        for item in CATEGORIAS_CUSTOS['marketing']['itens']:
            if item['nome'] == item_nome:
                custo_marketing += item['custo_base']
                detalhes_marketing.append({
                    'item': item_nome,
                    'valor': item['custo_base'],
                    'descricao': item.get('descricao', '')
                })
                break
    
    if not detalhes_marketing:
        custo_marketing = dados_entrada.get('custo_marketing', 800)
        detalhes_marketing.append({
            'item': 'Divulgação básica',
            'valor': custo_marketing,
            'descricao': 'Campanha inicial de divulgação'
        })
    
    custos_detalhados['categorias']['marketing'] = {
        'total': custo_marketing,
        'detalhes': detalhes_marketing
    }
    
    # 5. CUSTOS COM RECURSOS HUMANOS
    rh_itens_selecionados = dados_entrada.get('rh_itens_selecionados', [])
    custo_rh = 0
    detalhes_rh = []
    
    for item_nome in rh_itens_selecionados:
        for item in CATEGORIAS_CUSTOS['recursos_humanos']['itens']:
            if item['nome'] == item_nome:
                custo_rh += item['custo_base']
                detalhes_rh.append({
                    'item': item_nome,
                    'valor': item['custo_base'],
                    'descricao': item.get('descricao', '')
                })
                break
    
    if not detalhes_rh:
        custo_rh = 5000  # Valor padrão
        detalhes_rh.append({
            'item': 'Treinamento básico',
            'valor': custo_rh,
            'descricao': 'Capacitação inicial da equipe'
        })
    
    custos_detalhados['categorias']['recursos_humanos'] = {
        'total': custo_rh,
        'detalhes': detalhes_rh
    }
    
    # 6. OUTROS CUSTOS
    outros_custos = dados_entrada.get('outros_custos', 200)
    custos_detalhados['categorias']['outros'] = {
        'total': outros_custos,
        'detalhes': [{'item': 'Custos diversos', 'valor': outros_custos}]
    }
    
    # Resumo geral
    investimento_total = sum([cat['total'] for cat in custos_detalhados['categorias'].values()])
    
    custos_detalhados['resumo'] = {
        'investimento_total': investimento_total,
        'professores_necessarios': professores_necessarios,
        'custo_medio_por_aluno': investimento_total / total_alunos_projetado if total_alunos_projetado > 0 else 0,
        'custo_medio_por_atividade': investimento_total / num_atividades if num_atividades > 0 else 0
    }
    
    return custos_detalhados

def calcular_projecao(dados_entrada, custos_detalhados):
    """Calcula todas as projeções baseadas nos dados inseridos"""
    
    alunos_atuais = dados_entrada.get('alunos_atuais', 0)
    mensalidade = dados_entrada.get('mensalidade_media', 0)
    aumento_percentual = dados_entrada.get('aumento_esperado', 0) / 100
    
    # Cálculo de novos alunos
    novos_alunos = int(alunos_atuais * aumento_percentual)
    
    # Receitas
    receita_atual = alunos_atuais * mensalidade
    receita_projetada = (alunos_atuais + novos_alunos) * mensalidade
    
    # Custos do investimento
    investimento_total = custos_detalhados['resumo']['investimento_total']
    
    # Retorno mensal adicional
    retorno_mensal = novos_alunos * mensalidade
    
    # Cálculo de payback e ROI
    if retorno_mensal > 0:
        payback_meses = investimento_total / retorno_mensal
    else:
        payback_meses = 0
        
    if investimento_total > 0:
        roi_percentual = (retorno_mensal * 12 / investimento_total) * 100
    else:
        roi_percentual = 0
    
    return {
        'novos_alunos': novos_alunos,
        'receita_atual': receita_atual,
        'receita_projetada': receita_projetada,
        'investimento_total': investimento_total,
        'retorno_mensal': retorno_mensal,
        'payback_meses': payback_meses,
        'roi_percentual': roi_percentual,
        'professores_necessarios': custos_detalhados['resumo']['professores_necessarios'],
        'custo_medio_por_aluno': custos_detalhados['resumo']['custo_medio_por_aluno'],
        'custo_medio_por_atividade': custos_detalhados['resumo']['custo_medio_por_atividade']
    }

# Templates HTML inline
def get_base_html(title="Business Plan Escolar", content=""):
    """Retorna o HTML base para todas as páginas"""
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary-color: #4361ee;
            --secondary-color: #3a0ca3;
            --success-color: #4cc9f0;
            --infantil-color: #FF6B8B;
            --fundamental-color: #4ECDC4;
            --medio-color: #45B7D1;
        }}
        body {{
            background-color: #f5f7fb;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }}
        .navbar-brand {{
            font-weight: 700;
            font-size: 1.5rem;
        }}
        .card {{
            border-radius: 10px;
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
        .card-header {{
            border-radius: 10px 10px 0 0 !important;
            font-weight: 600;
        }}
        .btn-primary {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
        }}
        .btn-primary:hover {{
            background-color: var(--secondary-color);
            border-color: var(--secondary-color);
        }}
        .nivel-infantil {{ border-left: 5px solid var(--infantil-color) !important; }}
        .nivel-fundamental {{ border-left: 5px solid var(--fundamental-color) !important; }}
        .nivel-medio {{ border-left: 5px solid var(--medio-color) !important; }}
        
        .costo-item {{
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .costo-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .costo-seleccionado {{
            background-color: #e8f4fd !important;
            border-color: var(--primary-color) !important;
        }}
        
        .hero-section {{
            background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
        }}
        
        .badge-nivel {{
            font-size: 0.8em;
            padding: 5px 10px;
            border-radius: 20px;
        }}
        .badge-infantil {{ background-color: var(--infantil-color); }}
        .badge-fundamental {{ background-color: var(--fundamental-color); }}
        .badge-medio {{ background-color: var(--medio-color); }}
        
        footer {{
            background-color: #2c3e50;
            color: white;
            padding: 20px 0;
            margin-top: 40px;
        }}
        
        .sticky-summary {{
            position: sticky;
            top: 20px;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-chart-line"></i> Business Plan Escolar
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Início</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/simulacao">Nova Simulação</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/info">
                            <i class="fas fa-info-circle"></i> Info
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {content}
    </div>

    <footer class="bg-dark text-white mt-5">
        <div class="container text-center">
            <p>Sistema de Business Plan para Escolas - Análise detalhada de custos por nível escolar</p>
            <p class="mb-0">© 2024 - Desenvolvido com Python, Flask e SQLite</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

# Rotas da aplicação
@app.route('/')
def index():
    content = '''
    <div class="row">
        <div class="col-lg-8 mx-auto text-center">
            <div class="hero-section">
                <h1 class="display-4 mb-4">
                    <i class="fas fa-school"></i> Sistema de Business Plan Escolar
                </h1>
                <p class="lead mb-4">
                    Ferramenta avançada para análise de custo-benefício com <strong>custos específicos por nível escolar</strong>
                    visando aumentar em <strong>30% a 50%</strong> o número de matrículas.
                </p>
                <div class="row mt-5">
                    <div class="col-md-3">
                        <div class="card mb-4 border-primary">
                            <div class="card-body">
                                <i class="fas fa-baby fa-3x text-primary mb-3"></i>
                                <h4>Educação Infantil</h4>
                                <p>Custos específicos para berçário ao infantil</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card mb-4 border-success">
                            <div class="card-body">
                                <i class="fas fa-graduation-cap fa-3x text-success mb-3"></i>
                                <h4>Fundamental I</h4>
                                <p>Anos iniciais do ensino fundamental</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card mb-4 border-info">
                            <div class="card-body">
                                <i class="fas fa-book fa-3x text-info mb-3"></i>
                                <h4>Fundamental II</h4>
                                <p>Anos finais do ensino fundamental</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card mb-4 border-warning">
                            <div class="card-body">
                                <i class="fas fa-university fa-3x text-warning mb-3"></i>
                                <h4>Ensino Médio</h4>
                                <p>Preparação para vestibular e ENEM</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <a href="/simulacao" class="btn btn-primary btn-lg mt-4">
                    <i class="fas fa-play-circle"></i> Iniciar Nova Simulação
                </a>
            </div>
        </div>
    </div>

    <div class="row mt-5">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-info text-white">
                    <h4><i class="fas fa-bullseye"></i> Novas Funcionalidades</h4>
                </div>
                <div class="card-body">
                    <ul class="list-group list-group-flush">
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            <strong>Custos por nível escolar</strong> - Infantil, Fundamental I/II, Médio
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            <strong>Seleção de atividades específicas</strong> por nível
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            <strong>Custos detalhados por categoria</strong> - Infraestrutura, Material, etc.
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            <strong>Cálculo automático de professores</strong> necessários
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            <strong>Seleção de itens de custo</strong> personalizável
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h4><i class="fas fa-chart-pie"></i> Análise Detalhada de Custos</h4>
                </div>
                <div class="card-body">
                    <div class="alert alert-success">
                        <strong>Infraestrutura específica:</strong> Brinquedoteca, laboratórios, quadras
                    </div>
                    <div class="alert alert-info">
                        <strong>Materiais por aluno:</strong> Kits de atividades, uniformes, livros
                    </div>
                    <div class="alert alert-warning">
                        <strong>Recursos humanos:</strong> Professores especializados, capacitação
                    </div>
                    <div class="alert alert-primary">
                        <strong>Marketing segmentado:</strong> Divulgação por público-alvo
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Business Plan Escolar - Início", content)

@app.route('/simulacao')
def simulacao():
    # Gerar opções de atividades por nível
    atividades_options = ""
    for nivel, config in CUSTOS_POR_NIVEL.items():
        atividades_options += f'<optgroup label="{nivel.replace("_", " ").title()}">'
        for atividade in config['atividades_especificas']:
            atividades_options += f'<option value="{atividade}">{atividade}</option>'
        atividades_options += '</optgroup>'
    
    # Gerar opções de infraestrutura
    infra_options = ""
    for item in CATEGORIAS_CUSTOS['infraestrutura']['itens']:
        infra_options += f'''
        <div class="form-check mb-2 costo-item" onclick="toggleCostoItem(this, 'infra')">
            <input class="form-check-input" type="checkbox" name="infra_itens" value="{item['nome']}" id="infra_{item['nome'].replace(' ', '_')}">
            <label class="form-check-label" for="infra_{item['nome'].replace(' ', '_')}">
                <strong>{item['nome']}</strong> - R$ {item['custo_base']:,.0f}
                <small class="d-block text-muted">{item.get('descricao', '')}</small>
            </label>
        </div>
        '''
    
    # Gerar opções de material
    material_options = ""
    for item in CATEGORIAS_CUSTOS['material']['itens']:
        por_aluno = " (por aluno)" if item.get('por_aluno', False) else ""
        material_options += f'''
        <div class="form-check mb-2 costo-item" onclick="toggleCostoItem(this, 'material')">
            <input class="form-check-input" type="checkbox" name="material_itens" value="{item['nome']}" id="material_{item['nome'].replace(' ', '_')}">
            <label class="form-check-label" for="material_{item['nome'].replace(' ', '_')}">
                <strong>{item['nome']}</strong> - R$ {item['custo_base']:,.0f}{por_aluno}
            </label>
        </div>
        '''
    
    # Gerar opções de marketing
    marketing_options = ""
    for item in CATEGORIAS_CUSTOS['marketing']['itens']:
        marketing_options += f'''
        <div class="form-check mb-2 costo-item" onclick="toggleCostoItem(this, 'marketing')">
            <input class="form-check-input" type="checkbox" name="marketing_itens" value="{item['nome']}" id="marketing_{item['nome'].replace(' ', '_')}">
            <label class="form-check-label" for="marketing_{item['nome'].replace(' ', '_')}">
                <strong>{item['nome']}</strong> - R$ {item['custo_base']:,.0f}
                <small class="d-block text-muted">{item.get('descricao', '')}</small>
            </label>
        </div>
        '''
    
    # Gerar opções de RH
    rh_options = ""
    for item in CATEGORIAS_CUSTOS['recursos_humanos']['itens']:
        rh_options += f'''
        <div class="form-check mb-2 costo-item" onclick="toggleCostoItem(this, 'rh')">
            <input class="form-check-input" type="checkbox" name="rh_itens" value="{item['nome']}" id="rh_{item['nome'].replace(' ', '_')}">
            <label class="form-check-label" for="rh_{item['nome'].replace(' ', '_')}">
                <strong>{item['nome']}</strong> - R$ {item['custo_base']:,.0f}
                <small class="d-block text-muted">{item.get('descricao', '')}</small>
            </label>
        </div>
        '''
    
    content = f'''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-calculator"></i> Simulação Detalhada de Business Plan</h3>
                    <p class="mb-0">Configure os custos específicos por nível escolar e atividades</p>
                </div>
                <div class="card-body">
                    <form id="simulacaoForm">
                        <div class="row">
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-school"></i> Dados da Escola
                                </h4>
                                
                                <div class="mb-3">
                                    <label class="form-label">Nível Escolar:</label>
                                    <select class="form-select" id="nivel_escolar" onchange="atualizarCustosPorNivel()" required>
                                        <option value="infantil">Educação Infantil</option>
                                        <option value="fundamental_i" selected>Ensino Fundamental I (1º ao 5º ano)</option>
                                        <option value="fundamental_ii">Ensino Fundamental II (6º ao 9º ano)</option>
                                        <option value="medio">Ensino Médio</option>
                                    </select>
                                    <div class="form-text">Selecione o nível escolar para cálculos específicos</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Número atual de alunos:</label>
                                    <input type="number" class="form-control" id="alunos_atuais" 
                                           value="200" min="1" required>
                                    <div class="form-text">Total de alunos matriculados atualmente</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Mensalidade média (R$):</label>
                                    <input type="number" class="form-control" id="mensalidade_media" 
                                           value="800" min="100" step="50" required>
                                    <div class="form-text">Valor médio da mensalidade por aluno</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Aumento esperado de matrículas:</label>
                                    <div class="input-group">
                                        <input type="range" class="form-range" id="aumento_esperado_range" 
                                               min="30" max="50" step="5" value="40">
                                        <span class="input-group-text w-25" id="aumento_esperado_value">40%</span>
                                    </div>
                                    <div class="form-text">Meta: 30% a 50% (recomendado pela gestão)</div>
                                    <input type="hidden" id="aumento_esperado" value="40">
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-chalkboard-teacher"></i> Atividades Extracurriculares
                                </h4>
                                
                                <div class="mb-3">
                                    <label class="form-label">Selecione as atividades:</label>
                                    <select class="form-select" id="atividades_selecionadas" multiple size="6">
                                        {atividades_options}
                                    </select>
                                    <div class="form-text">Pressione Ctrl para selecionar múltiplas atividades</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Horas semanais por atividade:</label>
                                    <input type="number" class="form-control" id="horas_semanais" 
                                           value="10" min="5" step="1">
                                    <div class="form-text">Horas totais de atividades por semana</div>
                                </div>
                                
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle"></i>
                                    <strong>Dicas:</strong>
                                    <ul class="mb-0 mt-2">
                                        <li>Infantil: Recomendado 2-3 atividades</li>
                                        <li>Fundamental: Recomendado 3-4 atividades</li>
                                        <li>Médio: Recomendado 4-5 atividades</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mt-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-tools"></i> Custos de Infraestrutura
                                </h4>
                                <div class="row">
                                    <div class="col-md-6">
                                        {infra_options}
                                    </div>
                                    <div class="col-md-6">
                                        <div class="card">
                                            <div class="card-body">
                                                <h6><i class="fas fa-lightbulb"></i> Recomendações por Nível</h6>
                                                <div id="recomendacoes_infra">
                                                    <p class="mb-2"><strong>Infantil:</strong> Brinquedoteca, Parque infantil</p>
                                                    <p class="mb-2"><strong>Fundamental:</strong> Laboratório, Quadra</p>
                                                    <p class="mb-2"><strong>Médio:</strong> Laboratório avançado, Estúdio</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mt-4">
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-book"></i> Materiais e Equipamentos
                                </h4>
                                {material_options}
                            </div>
                            
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-bullhorn"></i> Marketing e Divulgação
                                </h4>
                                {marketing_options}
                            </div>
                        </div>
                        
                        <div class="row mt-4">
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-users"></i> Recursos Humanos
                                </h4>
                                {rh_options}
                            </div>
                            
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-calculator"></i> Resumo de Custos
                                </h4>
                                <div class="sticky-summary">
                                    <h5>Estimativa de Investimento</h5>
                                    <div id="resumo_custos">
                                        <p>Selecione itens para ver a estimativa</p>
                                    </div>
                                    <div class="mt-3">
                                        <div class="mb-3">
                                            <label class="form-label">Outros custos (R$):</label>
                                            <input type="number" class="form-control" id="outros_custos" 
                                                   value="200" min="0" step="50">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mt-4">
                            <div class="col-12 text-center">
                                <button type="button" class="btn btn-primary btn-lg" 
                                        onclick="calcularSimulacao()" id="btnCalcular">
                                    <i class="fas fa-calculator"></i> Calcular Projeção Detalhada
                                </button>
                                <button type="button" class="btn btn-secondary btn-lg ms-2" onclick="resetForm()">
                                    <i class="fas fa-redo"></i> Limpar Tudo
                                </button>
                            </div>
                        </div>
                    </form>
                    
                    <div class="row mt-5">
                        <div class="col-12">
                            <div id="resultado" style="display: none;">
                                <!-- Resultados serão inseridos aqui via JavaScript -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Configurar eventos
        document.getElementById('alunos_atuais').addEventListener('input', atualizarResumo);
        document.getElementById('mensalidade_media').addEventListener('input', atualizarResumo);
        document.getElementById('aumento_esperado_range').addEventListener('input', function() {{
            document.getElementById('aumento_esperado_value').textContent = this.value + '%';
            document.getElementById('aumento_esperado').value = this.value;
            atualizarResumo();
        }});
        
        // Configurar seleção de itens de custo
        document.querySelectorAll('.costo-item input[type="checkbox"]').forEach(checkbox => {{
            checkbox.addEventListener('change', atualizarResumo);
        }});
        
        atualizarResumo();
    }});
    
    function toggleCostoItem(element, tipo) {{
        const checkbox = element.querySelector('input[type="checkbox"]');
        checkbox.checked = !checkbox.checked;
        element.classList.toggle('costo-seleccionado', checkbox.checked);
        atualizarResumo();
    }}
    
    function atualizarCustosPorNivel() {{
        const nivel = document.getElementById('nivel_escolar').value;
        let recomendacoes = '';
        
        switch(nivel) {{
            case 'infantil':
                recomendacoes = '<p class="mb-2"><strong>Infantil:</strong> Brinquedoteca, Parque infantil, Sala multiuso</p>';
                break;
            case 'fundamental_i':
                recomendacoes = '<p class="mb-2"><strong>Fundamental I:</strong> Laboratório de informática, Quadra, Biblioteca</p>';
                break;
            case 'fundamental_ii':
                recomendacoes = '<p class="mb-2"><strong>Fundamental II:</strong> Laboratório de ciências, Estúdio de música, Sala de estudos</p>';
                break;
            case 'medio':
                recomendacoes = '<p class="mb-2"><strong>Médio:</strong> Laboratório avançado, Sala de projeção, Espaço coworking</p>';
                break;
        }}
        
        document.getElementById('recomendacoes_infra').innerHTML = recomendacoes;
        atualizarResumo();
    }}
    
    function atualizarResumo() {{
        const alunos = parseInt(document.getElementById('alunos_atuais').value) || 0;
        const mensalidade = parseFloat(document.getElementById('mensalidade_media').value) || 0;
        const aumento = parseInt(document.getElementById('aumento_esperado').value) || 0;
        const nivel = document.getElementById('nivel_escolar').value;
        
        // Calcular novos alunos
        const novosAlunos = Math.round(alunos * (aumento / 100));
        const totalAlunos = alunos + novosAlunos;
        
        // Calcular custos selecionados
        let custoTotal = 0;
        const custosDetalhados = {{}};
        
        // Infraestrutura
        const infraSelecionados = Array.from(document.querySelectorAll('input[name="infra_itens"]:checked'))
            .map(cb => cb.value);
        
        // Material (ajustar por aluno se necessário)
        const materialSelecionados = Array.from(document.querySelectorAll('input[name="material_itens"]:checked'))
            .map(cb => cb.value);
        
        // Marketing
        const marketingSelecionados = Array.from(document.querySelectorAll('input[name="marketing_itens"]:checked'))
            .map(cb => cb.value);
        
        // RH
        const rhSelecionados = Array.from(document.querySelectorAll('input[name="rh_itens"]:checked'))
            .map(cb => cb.value);
        
        // Outros custos
        const outrosCustos = parseFloat(document.getElementById('outros_custos').value) || 0;
        
        // Atividades selecionadas
        const atividadesSelect = document.getElementById('atividades_selecionadas');
        const atividadesSelecionadas = Array.from(atividadesSelect.selectedOptions).map(opt => opt.value);
        
        // Atualizar resumo
        let resumoHTML = `
            <table class="table table-sm">
                <tr>
                    <td>Alunos atuais:</td>
                    <td class="text-end"><strong>${{alunos}}</strong></td>
                </tr>
                <tr>
                    <td>Novos alunos projetados:</td>
                    <td class="text-end text-success"><strong>+${{novosAlunos}}</strong></td>
                </tr>
                <tr>
                    <td>Total projetado:</td>
                    <td class="text-end"><strong>${{totalAlunos}}</strong></td>
                </tr>
                <tr>
                    <td>Aumento:</td>
                    <td class="text-end"><strong>${{aumento}}%</strong></td>
                </tr>
                <tr class="table-secondary">
                    <td>Nível escolar:</td>
                    <td class="text-end"><span class="badge badge-${{nivel}}">${{nivel.replace('_', ' ').toUpperCase()}}</span></td>
                </tr>
                <tr class="table-secondary">
                    <td>Atividades selecionadas:</td>
                    <td class="text-end"><strong>${{atividadesSelecionadas.length}}</strong></td>
                </tr>
            </table>
            
            <div class="alert alert-info mt-3">
                <i class="fas fa-calculator"></i> 
                <strong>Receita adicional mensal estimada:</strong> 
                <span class="float-end">R$ ${{(novosAlunos * mensalidade).toLocaleString('pt-BR')}}</span>
            </div>
        `;
        
        document.getElementById('resumo_custos').innerHTML = resumoHTML;
    }}
    
    function resetForm() {{
        document.getElementById('simulacaoForm').reset();
        document.querySelectorAll('.costo-item').forEach(item => {{
            item.classList.remove('costo-seleccionado');
        }});
        atualizarResumo();
    }}
    
    async function calcularSimulacao() {{
        const btn = document.getElementById('btnCalcular');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculando...';
        btn.disabled = true;
        
        try {{
            // Coletar dados do formulário
            const atividadesSelect = document.getElementById('atividades_selecionadas');
            const atividadesSelecionadas = Array.from(atividadesSelect.selectedOptions).map(opt => opt.value);
            
            const infraSelecionados = Array.from(document.querySelectorAll('input[name="infra_itens"]:checked'))
                .map(cb => cb.value);
            
            const materialSelecionados = Array.from(document.querySelectorAll('input[name="material_itens"]:checked'))
                .map(cb => cb.value);
            
            const marketingSelecionados = Array.from(document.querySelectorAll('input[name="marketing_itens"]:checked'))
                .map(cb => cb.value);
            
            const rhSelecionados = Array.from(document.querySelectorAll('input[name="rh_itens"]:checked'))
                .map(cb => cb.value);
            
            const dados = {{
                alunos_atuais: parseInt(document.getElementById('alunos_atuais').value),
                mensalidade_media: parseFloat(document.getElementById('mensalidade_media').value),
                aumento_esperado: parseInt(document.getElementById('aumento_esperado').value),
                nivel_escolar: document.getElementById('nivel_escolar').value,
                atividades_selecionadas: atividadesSelecionadas,
                infra_itens_selecionados: infraSelecionados,
                material_itens_selecionados: materialSelecionados,
                marketing_itens_selecionados: marketingSelecionados,
                rh_itens_selecionados: rhSelecionados,
                horas_semanais: parseInt(document.getElementById('horas_semanais').value) || 10,
                outros_custos: parseFloat(document.getElementById('outros_custos').value) || 0
            }};
            
            const response = await fetch('/calcular', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify(dados)
            }});
            
            const resultados = await response.json();
            
            if (response.ok) {{
                mostrarResultados(resultados);
                // Redirecionar para resultado após cálculo
                setTimeout(() => {{
                    window.location.href = '/resultado';
                }}, 1500);
            }} else {{
                alert('Erro: ' + (resultados.error || 'Desconhecido'));
            }}
        }} catch (error) {{
            alert('Erro ao calcular: ' + error.message);
        }} finally {{
            btn.innerHTML = '<i class="fas fa-calculator"></i> Calcular Projeção Detalhada';
            btn.disabled = false;
        }}
    }}
    
    function mostrarResultados(resultados) {{
        const divResultado = document.getElementById('resultado');
        
        let html = `
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <h4 class="mb-0"><i class="fas fa-chart-line"></i> Simulação Calculada com Sucesso!</h4>
                </div>
                <div class="card-body">
                    <div class="alert alert-success">
                        <h5><i class="fas fa-check-circle"></i> Cálculos concluídos</h5>
                        <p>Redirecionando para análise detalhada...</p>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <h5>Resumo Financeiro</h5>
                            <table class="table table-bordered">
                                <tr>
                                    <th>Investimento Total:</th>
                                    <td class="text-danger">R$ ${{resultados.investimento_total.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}}</td>
                                </tr>
                                <tr>
                                    <th>Retorno Mensal:</th>
                                    <td class="text-success">R$ ${{resultados.retorno_mensal.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}}</td>
                                </tr>
                                <tr>
                                    <th>Payback:</th>
                                    <td>${{resultados.payback_meses.toFixed(1)}} meses</td>
                                </tr>
                                <tr>
                                    <th>ROI Anual:</th>
                                    <td class="text-success">${{resultados.roi_percentual.toFixed(1)}}%</td>
                                </tr>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h5>Indicadores Operacionais</h5>
                            <table class="table table-bordered">
                                <tr>
                                    <th>Professores necessários:</th>
                                    <td>${{resultados.professores_necessarios}}</td>
                                </tr>
                                <tr>
                                    <th>Custo médio por aluno:</th>
                                    <td>R$ ${{resultados.custo_medio_por_aluno.toFixed(2)}}</td>
                                </tr>
                                <tr>
                                    <th>Custo por atividade:</th>
                                    <td>R$ ${{resultados.custo_medio_por_atividade.toFixed(2)}}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        divResultado.innerHTML = html;
        divResultado.style.display = 'block';
        divResultado.scrollIntoView({{ behavior: 'smooth' }});
    }}
    </script>
    
    <style>
    .badge-infantil {{ background-color: #FF6B8B; }}
    .badge-fundamental {{ background-color: #4ECDC4; }}
    .badge-medio {{ background-color: #45B7D1; }}
    </style>
    '''
    return get_base_html("Simulação Detalhada - Business Plan", content)

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        dados = request.json
        
        # Validação básica
        if not dados.get('alunos_atuais') or dados['alunos_atuais'] <= 0:
            return jsonify({'error': 'Número de alunos atual inválido'}), 400
            
        if dados.get('aumento_esperado') < 30 or dados.get('aumento_esperado') > 50:
            return jsonify({'warning': 'Aumento esperado deve estar entre 30% e 50%'})
        
        # Calcular custos detalhados
        custos_detalhados = calcular_custos_detalhados(dados)
        
        # Calcular projeções
        resultados = calcular_projecao(dados, custos_detalhados)
        
        # Salvar na sessão
        session['ultima_simulacao'] = {
            'dados_entrada': dados,
            'resultados': resultados,
            'custos_detalhados': custos_detalhados
        }
        
        # Salvar no banco de dados
        salvar_simulacao(dados, resultados, custos_detalhados)
        
        return jsonify(resultados)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/resultado')
def resultado():
    if 'ultima_simulacao' not in session:
        return index()
    
    dados = session['ultima_simulacao']
    custos_detalhados = dados['custos_detalhados']
    
    # Gerar HTML para tabelas de custos detalhados
    tabelas_custos = ""
    for categoria, info in custos_detalhados['categorias'].items():
        linhas = ""
        for detalhe in info['detalhes']:
            valor_formatado = f"R$ {detalhe['valor']:,.2f}"
            descricao = f"<br><small class='text-muted'>{detalhe.get('descricao', '')}</small>" if detalhe.get('descricao') else ""
            por_aluno = " <span class='badge bg-info'>por aluno</span>" if detalhe.get('por_aluno', False) else ""
            
            linhas += f'''
            <tr>
                <td>{detalhe['item']}{por_aluno}{descricao}</td>
                <td class="text-end">{valor_formatado}</td>
            </tr>
            '''
        
        tabelas_custos += f'''
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-{'primary' if categoria == 'professores' else 'info' if categoria == 'infraestrutura' else 'success' if categoria == 'material' else 'warning' if categoria == 'marketing' else 'secondary'} text-white">
                    <h6 class="mb-0">
                        <i class="fas fa-{'chalkboard-teacher' if categoria == 'professores' else 'building' if categoria == 'infraestrutura' else 'book' if categoria == 'material' else 'bullhorn' if categoria == 'marketing' else 'users'}"></i>
                        {categoria.replace('_', ' ').title()}
                        <span class="float-end">R$ {info['total']:,.2f}</span>
                    </h6>
                </div>
                <div class="card-body p-0">
                    <table class="table table-sm mb-0">
                        <tbody>
                            {linhas}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        '''
    
    # Gerar gráfico de distribuição de custos
    chart_data_labels = []
    chart_data_values = []
    chart_background_colors = [
        'rgba(54, 162, 235, 0.7)',   # Professores - azul
        'rgba(75, 192, 192, 0.7)',   # Infraestrutura - verde água
        'rgba(255, 206, 86, 0.7)',   # Material - amarelo
        'rgba(255, 99, 132, 0.7)',   # Marketing - vermelho
        'rgba(153, 102, 255, 0.7)',  # RH - roxo
        'rgba(201, 203, 207, 0.7)'   # Outros - cinza
    ]
    
    for i, (categoria, info) in enumerate(custos_detalhados['categorias'].items()):
        if info['total'] > 0:
            chart_data_labels.append(categoria.title())
            chart_data_values.append(info['total'])
    
    chart_js = f'''
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Gráfico de distribuição de custos
        const ctx1 = document.getElementById('chartCustos').getContext('2d');
        new Chart(ctx1, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(chart_data_labels)},
                datasets: [{{
                    data: {json.dumps(chart_data_values)},
                    backgroundColor: {json.dumps(chart_background_colors[:len(chart_data_labels)])},
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((context.parsed / total) * 100);
                                return context.label + ': R$ ' + context.parsed.toLocaleString('pt-BR') + 
                                       ' (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Gráfico de receitas
        const ctx2 = document.getElementById('chartReceitas').getContext('2d');
        new Chart(ctx2, {{
            type: 'bar',
            data: {{
                labels: ['Receita Atual', 'Receita Projetada'],
                datasets: [{{
                    label: 'Valor em R$',
                    data: [{dados['resultados']['receita_atual']}, {dados['resultados']['receita_projetada']}],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(75, 192, 192, 0.5)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(75, 192, 192, 1)'
                    ],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'R$ ' + context.parsed.y.toLocaleString('pt-BR');
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return 'R$ ' + value.toLocaleString('pt-BR');
                            }}
                        }}
                    }}
                }}
            }}
        }});
    }});
    </script>
    '''
    
    content = f'''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card shadow mb-4">
                <div class="card-header bg-primary text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h3 class="mb-0"><i class="fas fa-chart-pie"></i> Análise Detalhada da Projeção</h3>
                            <p class="mb-0">
                                Nível: <span class="badge badge-{dados['custos_detalhados']['nivel_escolar']}">
                                    {dados['custos_detalhados']['nivel_escolar'].replace('_', ' ').title()}
                                </span>
                                | Aumento: {dados['dados_entrada']['aumento_esperado']}%
                                | Atividades: {len(dados['custos_detalhados']['atividades_selecionadas'])}
                            </p>
                        </div>
                        <span class="badge bg-light text-primary fs-6">
                            ROI: {dados['resultados']['roi_percentual']:.1f}%
                        </span>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0"><i class="fas fa-chart-bar"></i> Comparativo de Receitas</h5>
                                </div>
                                <div class="card-body">
                                    <canvas id="chartReceitas" height="200"></canvas>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-user-plus"></i> Crescimento</h5>
                                </div>
                                <div class="card-body text-center">
                                    <h1 class="display-1 text-primary">{dados['resultados']['novos_alunos']}</h1>
                                    <p class="lead">Novos Alunos</p>
                                    <div class="progress" style="height: 30px;">
                                        <div class="progress-bar bg-success" role="progressbar" 
                                             style="width: {dados['dados_entrada']['aumento_esperado']}%">
                                            {dados['dados_entrada']['aumento_esperado']}% de Aumento
                                        </div>
                                    </div>
                                    <p class="mt-3 mb-0">
                                        <small>Professores necessários: <strong>{dados['resultados']['professores_necessarios']}</strong></small>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-warning text-dark">
                                    <h5 class="mb-0"><i class="fas fa-money-bill-wave"></i> Indicadores Financeiros</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row text-center">
                                        <div class="col-6">
                                            <div class="p-3 border rounded bg-light">
                                                <h6>Payback</h6>
                                                <h3 class="text-primary">{dados['resultados']['payback_meses']:.1f} meses</h3>
                                                <small>Tempo para recuperar investimento</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="p-3 border rounded bg-light">
                                                <h6>ROI Anual</h6>
                                                <h3 class="text-success">{dados['resultados']['roi_percentual']:.1f}%</h3>
                                                <small>Retorno sobre investimento</small>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <table class="table table-bordered mt-3">
                                        <tr>
                                            <th>Investimento Total:</th>
                                            <td class="text-end">R$ {dados['resultados']['investimento_total']:,.2f}</td>
                                        </tr>
                                        <tr>
                                            <th>Retorno Mensal:</th>
                                            <td class="text-end text-success">R$ {dados['resultados']['retorno_mensal']:,.2f}</td>
                                        </tr>
                                        <tr>
                                            <th>Lucro Anual Projetado:</th>
                                            <td class="text-end text-success">R$ {dados['resultados']['retorno_mensal'] * 12:,.2f}</td>
                                        </tr>
                                        <tr>
                                            <th>Custo médio por aluno:</th>
                                            <td class="text-end">R$ {dados['resultados']['custo_medio_por_aluno']:,.2f}</td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-danger text-white">
                                    <h5 class="mb-0"><i class="fas fa-chart-pie"></i> Distribuição de Custos</h5>
                                </div>
                                <div class="card-body">
                                    <canvas id="chartCustos" height="200"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-dark text-white">
                                    <h5 class="mb-0"><i class="fas fa-list-alt"></i> Detalhamento de Custos por Categoria</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        {tabelas_custos}
                                    </div>
                                    
                                    <div class="alert alert-info mt-4">
                                        <h6><i class="fas fa-lightbulb"></i> Atividades Selecionadas:</h6>
                                        <div class="mt-2">
                                            {', '.join(dados['custos_detalhados']['atividades_selecionadas']) if dados['custos_detalhados']['atividades_selecionadas'] else 'Nenhuma atividade selecionada'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-lightbulb"></i> Recomendações Estratégicas</h5>
                                </div>
                                <div class="card-body">
                                    <div class="alert {'alert-success' if dados['resultados']['roi_percentual'] > 100 else 'alert-warning'}">
                                        <h5>
                                            <i class="fas {'fa-check-circle' if dados['resultados']['roi_percentual'] > 100 else 'fa-exclamation-triangle'}"></i> 
                                            Viabilidade Financeira: {'ALTA' if dados['resultados']['roi_percentual'] > 100 else 'MODERADA'}
                                        </h5>
                                        <p>
                                            O ROI de {dados['resultados']['roi_percentual']:.1f}% indica 
                                            {'um excelente retorno sobre o investimento' if dados['resultados']['roi_percentual'] > 100 else 'um retorno satisfatório sobre o investimento'}.
                                            Payback estimado em {dados['resultados']['payback_meses']:.1f} meses.
                                        </p>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="card mb-3">
                                                <div class="card-body">
                                                    <h6><i class="fas fa-thumbs-up text-success"></i> Pontos Fortes</h6>
                                                    <ul>
                                                        <li>Aumento significativo de matrículas ({dados['dados_entrada']['aumento_esperado']}%)</li>
                                                        <li>Receita adicional mensal: R$ {dados['resultados']['retorno_mensal']:,.2f}</li>
                                                        <li>Diferenciação competitiva no mercado</li>
                                                        <li>Oferta especializada para {dados['custos_detalhados']['nivel_escolar'].replace('_', ' ')}</li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="card mb-3">
                                                <div class="card-body">
                                                    <h6><i class="fas fa-exclamation-triangle text-warning"></i> Considerações</h6>
                                                    <ul>
                                                        <li>Necessidade de {dados['resultados']['professores_necessarios']} professores especializados</li>
                                                        <li>Investimento inicial: R$ {dados['resultados']['investimento_total']:,.2f}</li>
                                                        <li>Gerenciamento de múltiplas atividades</li>
                                                        <li>Adequação da infraestrutura necessária</li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="text-center mt-3">
                                        <a href="/simulacao" class="btn btn-primary me-2">
                                            <i class="fas fa-redo"></i> Nova Simulação
                                        </a>
                                        <a href="/dashboard" class="btn btn-success me-2">
                                            <i class="fas fa-tachometer-alt"></i> Dashboard
                                        </a>
                                        <button class="btn btn-info me-2" onclick="window.print()">
                                            <i class="fas fa-print"></i> Imprimir Relatório
                                        </button>
                                        <a href="/simulacao/exportar" class="btn btn-warning">
                                            <i class="fas fa-file-excel"></i> Exportar Dados
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {chart_js}
    '''
    return get_base_html("Resultados Detalhados - Business Plan", content)

@app.route('/dashboard')
def dashboard():
    # Buscar todas as simulações
    simulacoes_db = buscar_simulacoes()
    
    # Converter para lista de dicionários
    simulacoes = []
    for s in simulacoes_db:
        try:
            data_criacao = datetime.strptime(s['data_criacao'], '%Y-%m-%d %H:%M:%S')
        except:
            data_criacao = datetime.now()
            
        # Carregar dados extras
        dados_extras = json.loads(s['dados']) if s['dados'] else {}
        
        simulacoes.append({
            'id': s['id'],
            'nome': s['nome'],
            'data_criacao': data_criacao,
            'alunos_atuais': s['alunos_atuais'],
            'mensalidade_media': s['mensalidade_media'],
            'aumento_esperado': s['aumento_esperado'],
            'novos_alunos': s['novos_alunos'],
            'nivel_escolar': s['nivel_escolar'],
            'investimento_total': s['investimento_total'],
            'retorno_mensal': s['retorno_mensal'],
            'payback': s['payback'],
            'roi': s['roi'],
            'dados_extras': dados_extras
        })
    
    # Estatísticas gerais
    total_simulacoes = len(simulacoes)
    
    if total_simulacoes > 0:
        media_aumento = sum([s['aumento_esperado'] for s in simulacoes]) / total_simulacoes
        media_roi = sum([s['roi'] for s in simulacoes]) / total_simulacoes
        media_payback = sum([s['payback'] for s in simulacoes]) / total_simulacoes
    else:
        media_aumento = media_roi = media_payback = 0
    
    # Criar tabela de simulações
    tabela_html = ""
    for s in simulacoes:
        nivel_badge = f"<span class='badge badge-{s['nivel_escolar']}'>{s['nivel_escolar'].replace('_', ' ').title()}</span>"
        
        tabela_html += f'''
        <tr>
            <td>{s['data_criacao'].strftime('%d/%m/%Y')}</td>
            <td>{s['nome']}</td>
            <td>{nivel_badge}</td>
            <td>{s['alunos_atuais']}</td>
            <td><span class="badge bg-success">{s['novos_alunos']}</span></td>
            <td><span class="badge bg-info">{s['aumento_esperado']}%</span></td>
            <td>R$ {s['investimento_total']:,.2f}</td>
            <td>
                <span class="badge {'bg-success' if s['roi'] > 100 else 'bg-warning'}">
                    {s['roi']:.1f}%
                </span>
            </td>
            <td>{s['payback']:.1f} meses</td>
            <td>
                <a href="/simulacao/{s['id']}" class="btn btn-sm btn-primary">
                    <i class="fas fa-eye"></i> Ver
                </a>
            </td>
        </tr>
        '''
    
    if total_simulacoes == 0:
        tabela_html = '''
        <tr>
            <td colspan="10" class="text-center py-5">
                <i class="fas fa-inbox fa-4x text-muted mb-3"></i>
                <h4>Nenhuma simulação encontrada</h4>
                <p>Realize sua primeira simulação para começar a análise</p>
                <a href="/simulacao" class="btn btn-primary">
                    <i class="fas fa-plus-circle"></i> Nova Simulação
                </a>
            </td>
        </tr>
        '''
    
    content = f'''
    <div class="row">
        <div class="col-12">
            <div class="card shadow mb-4">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                    <h3 class="mb-0"><i class="fas fa-tachometer-alt"></i> Dashboard - Histórico de Simulações</h3>
                    <span class="badge bg-light text-primary fs-6">{total_simulacoes} simulações</span>
                </div>
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card text-white bg-info mb-3">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 class="card-title">Média de Aumento</h6>
                                            <h2 class="mb-0">{media_aumento:.1f}%</h2>
                                        </div>
                                        <i class="fas fa-chart-line fa-3x opacity-50"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-success mb-3">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 class="card-title">ROI Médio</h6>
                                            <h2 class="mb-0">{media_roi:.1f}%</h2>
                                        </div>
                                        <i class="fas fa-percentage fa-3x opacity-50"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-warning mb-3">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 class="card-title">Payback Médio</h6>
                                            <h2 class="mb-0">{media_payback:.1f} meses</h2>
                                        </div>
                                        <i class="fas fa-calendar-alt fa-3x opacity-50"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-white bg-danger mb-3">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 class="card-title">Total Simulações</h6>
                                            <h2 class="mb-0">{total_simulacoes}</h2>
                                        </div>
                                        <i class="fas fa-database fa-3x opacity-50"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-dark text-white">
                                    <h5 class="mb-0"><i class="fas fa-history"></i> Histórico de Simulações por Nível Escolar</h5>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-hover">
                                            <thead class="table-light">
                                                <tr>
                                                    <th>Data</th>
                                                    <th>Nome</th>
                                                    <th>Nível</th>
                                                    <th>Alunos</th>
                                                    <th>Novos</th>
                                                    <th>Aumento</th>
                                                    <th>Investimento</th>
                                                    <th>ROI</th>
                                                    <th>Payback</th>
                                                    <th>Ações</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {tabela_html}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0"><i class="fas fa-chart-bar"></i> Distribuição por Nível Escolar</h5>
                                </div>
                                <div class="card-body">
                                    <canvas id="chartNiveis" height="200"></canvas>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-bullseye"></i> Metas e Recomendações</h5>
                                </div>
                                <div class="card-body">
                                    <div class="alert alert-success">
                                        <h5><i class="fas fa-trophy"></i> Metas por Nível</h5>
                                        <ul class="mb-0">
                                            <li><strong>Infantil:</strong> ROI mínimo 80%, Payback máximo 20 meses</li>
                                            <li><strong>Fundamental:</strong> ROI mínimo 100%, Payback máximo 18 meses</li>
                                            <li><strong>Médio:</strong> ROI mínimo 120%, Payback máximo 15 meses</li>
                                        </ul>
                                    </div>
                                    
                                    <div class="alert alert-info">
                                        <h5><i class="fas fa-check-circle"></i> KPIs de Sucesso</h5>
                                        <ul class="mb-0">
                                            <li>Taxa de adesão às atividades: 70%+</li>
                                            <li>Satisfação dos pais: 90%+</li>
                                            <li>Retenção de alunos: 85%+</li>
                                            <li>Crescimento orgânico: 10%+ ao ano</li>
                                        </ul>
                                    </div>
                                    
                                    <div class="text-center mt-3">
                                        <a href="/simulacao" class="btn btn-primary">
                                            <i class="fas fa-plus-circle"></i> Nova Simulação
                                        </a>
                                        <a href="/info" class="btn btn-info ms-2">
                                            <i class="fas fa-info-circle"></i> Informações
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Contar simulações por nível
        const niveis = {json.dumps([s['nivel_escolar'] for s in simulacoes])};
        const contagem = {{}};
        niveis.forEach(nivel => {{
            contagem[nivel] = (contagem[nivel] || 0) + 1;
        }});
        
        if (Object.keys(contagem).length > 0) {{
            const ctx = document.getElementById('chartNiveis').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(contagem).map(n => n.replace('_', ' ').toUpperCase()),
                    datasets: [{{
                        data: Object.values(contagem),
                        backgroundColor: [
                            'rgba(255, 107, 139, 0.7)',   // Infantil
                            'rgba(78, 205, 196, 0.7)',    // Fundamental I
                            'rgba(69, 183, 209, 0.7)',    // Fundamental II
                            'rgba(255, 193, 7, 0.7)'      // Médio
                        ],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ position: 'bottom' }}
                    }}
                }}
            }});
        }}
    }});
    </script>
    '''
    return get_base_html("Dashboard - Business Plan", content)

@app.route('/simulacao/<int:id>')
def ver_simulacao(id):
    simulacao_db = buscar_simulacao_por_id(id)
    if simulacao_db:
        try:
            dados_json = json.loads(simulacao_db['dados'])
        except:
            dados_json = {'entrada': {}, 'resultados': {}, 'custos_detalhados': {}}
        
        # Salvar na sessão para a rota /resultado usar
        session['ultima_simulacao'] = dados_json
        return redirect('/resultado')
    return index()

@app.route('/simulacao/exportar')
def exportar_simulacao():
    if 'ultima_simulacao' not in session:
        return redirect('/')
    
    dados = session['ultima_simulacao']
    
    # Criar um formato simplificado para exportação
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'dados_entrada': dados['dados_entrada'],
        'resultados': dados['resultados'],
        'custos_detalhados': dados.get('custos_detalhados', {})
    }
    
    return jsonify(export_data)

@app.route('/info')
def info():
    simulacoes_count = len(buscar_simulacoes())
    
    # Contar por nível escolar
    simulacoes = buscar_simulacoes()
    contagem_niveis = {}
    for s in simulacoes:
        nivel = s['nivel_escolar']
        contagem_niveis[nivel] = contagem_niveis.get(nivel, 0) + 1
    
    niveis_html = ""
    for nivel, count in contagem_niveis.items():
        niveis_html += f'''
        <div class="col-md-3">
            <div class="card">
                <div class="card-body text-center">
                    <h3>{count}</h3>
                    <p>{nivel.replace('_', ' ').title()}</p>
                </div>
            </div>
        </div>
        '''
    
    content = f'''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-info-circle"></i> Informações do Sistema Avançado</h3>
                </div>
                <div class="card-body">
                    <h4>Sistema de Business Plan Escolar - Versão Avançada</h4>
                    <p><strong>Versão:</strong> 2.0.0 (com custos específicos)</p>
                    <p><strong>Status:</strong> Online e operacional</p>
                    <p><strong>Última atualização:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    
                    <h5 class="mt-4">Estatísticas do Sistema:</h5>
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card bg-info text-white">
                                <div class="card-body text-center">
                                    <h3>{simulacoes_count}</h3>
                                    <p>Total de Simulações</p>
                                </div>
                            </div>
                        </div>
                        {niveis_html}
                    </div>
                    
                    <h5 class="mt-4">Funcionalidades Avançadas:</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <ul>
                                <li><strong>Custos por nível escolar</strong> - Infantil, Fundamental I/II, Médio</li>
                                <li><strong>Seleção de atividades específicas</strong> por nível</li>
                                <li><strong>Cálculo automático de professores</strong> necessários</li>
                                <li><strong>Ratio professor/aluno</strong> configurável por nível</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul>
                                <li><strong>Custos detalhados por categoria</strong> - 4 categorias principais</li>
                                <li><strong>Seleção de itens de custo</strong> personalizável</li>
                                <li><strong>Materiais por aluno</strong> ou fixos</li>
                                <li><strong>Gráficos interativos</strong> de distribuição</li>
                            </ul>
                        </div>
                    </div>
                    
                    <h5 class="mt-4">Categorias de Custos Implementadas:</h5>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="alert alert-primary">
                                <strong>Infraestrutura</strong><br>
                                {len(CATEGORIAS_CUSTOS['infraestrutura']['itens'])} itens
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="alert alert-success">
                                <strong>Material</strong><br>
                                {len(CATEGORIAS_CUSTOS['material']['itens'])} itens
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="alert alert-warning">
                                <strong>Marketing</strong><br>
                                {len(CATEGORIAS_CUSTOS['marketing']['itens'])} itens
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="alert alert-info">
                                <strong>Recursos Humanos</strong><br>
                                {len(CATEGORIAS_CUSTOS['recursos_humanos']['itens'])} itens
                            </div>
                        </div>
                    </div>
                    
                    <div class="text-center mt-4">
                        <a href="/" class="btn btn-primary">
                            <i class="fas fa-home"></i> Voltar ao Sistema
                        </a>
                        <a href="/dashboard" class="btn btn-success ms-2">
                            <i class="fas fa-chart-bar"></i> Ver Dashboard
                        </a>
                        <a href="/simulacao" class="btn btn-warning ms-2">
                            <i class="fas fa-calculator"></i> Nova Simulação
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Informações do Sistema", content)

# Rota de saúde
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'service': 'Business Plan Escolar - Versão Avançada',
        'version': '2.0.0',
        'database': 'active',
        'simulations_count': len(buscar_simulacoes()),
        'features': {
            'cost_categories': len(CATEGORIAS_CUSTOS),
            'school_levels': len(CUSTOS_POR_NIVEL),
            'total_cost_items': sum(len(cat['itens']) for cat in CATEGORIAS_CUSTOS.values())
        }
    })

# Tratamento de erros
@app.errorhandler(404)
def page_not_found(e):
    content = '''
    <div class="container text-center py-5">
        <div class="row">
            <div class="col-lg-6 mx-auto">
                <div class="card shadow">
                    <div class="card-body p-5">
                        <h1 class="display-1 text-muted">404</h1>
                        <h2 class="mb-4">Página não encontrada</h2>
                        <p class="lead mb-4">
                            A página que você está procurando não existe ou foi movida.
                        </p>
                        <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
                            <a href="/" class="btn btn-primary btn-lg px-4 gap-3">
                                <i class="fas fa-home"></i> Voltar ao Início
                            </a>
                            <a href="/simulacao" class="btn btn-outline-primary btn-lg px-4">
                                <i class="fas fa-calculator"></i> Nova Simulação
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Página não encontrada - 404", content), 404

@app.errorhandler(500)
def internal_server_error(e):
    content = '''
    <div class="container text-center py-5">
        <div class="row">
            <div class="col-lg-6 mx-auto">
                <div class="card shadow">
                    <div class="card-body p-5">
                        <h1 class="display-1 text-danger">500</h1>
                        <h2 class="mb-4">Erro interno do servidor</h2>
                        <p class="lead mb-4">
                            Ocorreu um erro inesperado. Nossa equipe já foi notificada.
                        </p>
                        <p class="text-muted mb-4">
                            Tente novamente em alguns instantes ou entre em contato com o suporte.
                        </p>
                        <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
                            <a href="/" class="btn btn-primary btn-lg px-4 gap-3">
                                <i class="fas fa-redo"></i> Tentar Novamente
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Erro Interno - 500", content), 500

if __name__ == '__main__':
    # Inicializar banco de dados
    if init_db():
        print("=" * 60)
        print("🚀 SISTEMA DE BUSINESS PLAN ESCOLAR - VERSÃO AVANÇADA")
        print("=" * 60)
        print("📊 Sistema com custos específicos por nível escolar")
        print("=" * 60)
        
        # Configurações
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') != 'production'
        
        if debug:
            print("🔧 Modo: Desenvolvimento")
            print("🌐 Acesse: http://localhost:{}".format(port))
        else:
            print("🚀 Modo: Produção")
            print("✅ Sistema pronto para acesso remoto")
        
        # Informações
        print("\n📊 Funcionalidades implementadas:")
        print("   ✅ Custos por nível escolar (4 níveis)")
        print("   ✅ {0} categorias de custos detalhadas".format(len(CATEGORIAS_CUSTOS)))
        print("   ✅ {0} itens de custo configuráveis".format(sum(len(cat['itens']) for cat in CATEGORIAS_CUSTOS.values())))
        print("   ✅ Cálculo automático de professores necessários")
        print("   ✅ Seleção de atividades específicas por nível")
        
        print("\n💡 Dicas de uso:")
        print("   1. Selecione o nível escolar para custos específicos")
        print("   2. Escolha atividades adequadas ao nível")
        print("   3. Selecione itens de custo conforme necessidade")
        print("   4. Analise o ROI e payback por nível")
        
        print("=" * 60)
        print("📢 Sistema iniciado com sucesso!")
        print("=" * 60)
        
        # Executar aplicação
        app.run(
            debug=debug, 
            port=port, 
            host='0.0.0.0',
            threaded=True
        )
    else:
        print("❌ Não foi possível inicializar o sistema.")