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
                <strong>{