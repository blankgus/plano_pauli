# app.py - Business Plan Escolar com IA - VERSÃO CORRIGIDA
from flask import Flask, render_template_string, request, jsonify, session, redirect
from datetime import datetime
import json
import os
import sqlite3
import openai
from typing import Dict, List, Any

app = Flask(__name__)

# Configuração
app.config['SECRET_KEY'] = 'business_plan_ia_escolar_2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configurar OpenAI (opcional)
openai.api_key = os.environ.get('OPENAI_API_KEY', '')

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'database_com_ia.db')

# Segmentos básicos
SEGMENTOS = {
    'ei': {'nome': 'Educação Infantil', 'cor': '#FF6B8B', 'descricao': '0-5 anos'},
    'ef_i': {'nome': 'Ensino Fundamental I', 'cor': '#4ECDC4', 'descricao': '6-10 anos'},
    'ef_ii': {'nome': 'Ensino Fundamental II', 'cor': '#45B7D1', 'descricao': '11-14 anos'},
    'em': {'nome': 'Ensino Médio', 'cor': '#FF9F1C', 'descricao': '15-17 anos'}
}

# Categorias de custos
CATEGORIAS_CUSTOS = {
    'investimento_inicial': ['Reforma', 'Equipamentos', 'Materiais', 'Móveis', 'Licenças'],
    'custos_mensais_fixos': ['Aluguel', 'Condomínio', 'Água', 'Energia', 'Internet', 'Limpeza'],
    'custos_mensais_variaveis': ['Material consumo', 'Material didático', 'Uniformes', 'Transporte'],
    'marketing': ['Site', 'Redes sociais', 'Publicidade', 'Divulgação'],
    'recursos_humanos': ['Salários professores', 'Coordenador', 'Secretária', 'Encargos']
}

# Benchmark do setor educativo
BENCHMARKS = {
    'margem_lucro_ideal': 30,
    'roi_minimo_aceitavel': 100,
    'payback_maximo': 36,
    'ratio_aluno_professor': {
        'ei': 10,
        'ef_i': 15,
        'ef_ii': 20,
        'em': 25
    },
    'custo_professor_hora': {
        'ei': 45,
        'ef_i': 50,
        'ef_ii': 55,
        'em': 65
    },
    'receita_media_aluno_mes': {
        'ei': 150,
        'ef_i': 180,
        'ef_ii': 200,
        'em': 250
    }
}

def init_db():
    """Inicializa o banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data_criacao TEXT,
            data_atualizacao TEXT,
            total_alunos INTEGER,
            total_participantes INTEGER,
            investimento_total REAL,
            custo_mensal_total REAL,
            receita_mensal_total REAL,
            lucro_mensal_total REAL,
            payback_meses REAL,
            roi_percentual REAL,
            margem_lucro REAL,
            dados_completos TEXT,
            analise_ia TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS atividades_simulacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulacao_id INTEGER,
            segmento TEXT,
            nome_atividade TEXT,
            custo_hora_professor REAL,
            horas_semanais REAL,
            semanas_mes INTEGER DEFAULT 4,
            alunos INTEGER,
            nao_alunos INTEGER,
            receita_aluno REAL,
            receita_nao_aluno REAL,
            custo_material_mensal REAL,
            FOREIGN KEY (simulacao_id) REFERENCES simulacoes (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados com IA inicializado!")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

# Inicializar banco de dados
init_db()

def get_base_html(title="Business Plan com IA", content=""):
    """Retorna o HTML base"""
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
            --ei-color: #FF6B8B;
            --ef-i-color: #4ECDC4;
            --ef-ii-color: #45B7D1;
            --em-color: #FF9F1C;
        }}
        body {{ background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .card {{ border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .btn-primary {{ background-color: #4361ee; border-color: #4361ee; }}
        .btn-primary:hover {{ background-color: #3a0ca3; border-color: #3a0ca3; }}
        .segmento-ei {{ border-left: 5px solid var(--ei-color) !important; }}
        .segmento-ef-i {{ border-left: 5px solid var(--ef-i-color) !important; }}
        .segmento-ef-ii {{ border-left: 5px solid var(--ef-ii-color) !important; }}
        .segmento-em {{ border-left: 5px solid var(--em-color) !important; }}
        .chart-container {{ position: relative; height: 300px; width: 100%; }}
        .analise-ia {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        /* CORREÇÕES DE TABELAS */
        .table-fixed {{
            table-layout: fixed;
            width: 100%;
        }}
        
        .table-fixed th,
        .table-fixed td {{
            padding: 12px 10px;
            vertical-align: middle;
        }}
        
        /* Larguras específicas para cada coluna */
        .col-nome {{ width: 220px; min-width: 200px; max-width: 250px; }}
        .col-data {{ width: 100px; min-width: 90px; max-width: 120px; }}
        .col-participantes {{ width: 90px; min-width: 80px; max-width: 100px; }}
        .col-investimento {{ width: 130px; min-width: 120px; max-width: 150px; }}
        .col-receita {{ width: 130px; min-width: 120px; max-width: 150px; }}
        .col-lucro {{ width: 130px; min-width: 120px; max-width: 150px; }}
        .col-margem {{ width: 100px; min-width: 90px; max-width: 120px; }}
        .col-roi {{ width: 100px; min-width: 90px; max-width: 120px; }}
        .col-payback {{ width: 110px; min-width: 100px; max-width: 130px; }}
        .col-acoes {{ width: 140px; min-width: 130px; max-width: 160px; }}
        
        /* Para tabela de atividades */
        .col-atividade-nome {{ width: 200px; min-width: 180px; max-width: 250px; }}
        .col-atividade-segmento {{ width: 140px; min-width: 120px; max-width: 160px; }}
        .col-atividade-alunos {{ width: 80px; min-width: 70px; max-width: 90px; }}
        .col-atividade-nao-alunos {{ width: 100px; min-width: 90px; max-width: 110px; }}
        .col-atividade-receita {{ width: 120px; min-width: 110px; max-width: 130px; }}
        .col-atividade-custo {{ width: 120px; min-width: 110px; max-width: 130px; }}
        .col-atividade-lucro {{ width: 120px; min-width: 110px; max-width: 130px; }}
        .col-atividade-margem {{ width: 100px; min-width: 90px; max-width: 110px; }}
        
        /* Overflow controlado */
        .text-truncate-cell {{
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: block;
        }}
        
        /* Badges com tamanho consistente */
        .badge-fixed {{
            display: inline-block;
            min-width: 75px;
            text-align: center;
            padding: 5px 8px;
            font-size: 0.85em;
        }}
        
        /* Altura uniforme para cards */
        .card-custo {{
            min-height: 350px;
            display: flex;
            flex-direction: column;
        }}
        
        .card-custo .card-body {{
            flex-grow: 1;
            overflow-y: auto;
        }}
        
        @media (max-width: 1200px) {{
            .col-nome {{ width: 180px; min-width: 160px; }}
            .col-investimento, .col-receita, .col-lucro {{ width: 110px; min-width: 100px; }}
        }}
        
        @media (max-width: 992px) {{
            .table-responsive {{
                font-size: 0.9em;
            }}
            .table-fixed th,
            .table-fixed td {{
                padding: 8px 6px;
            }}
        }}
        
        /* Melhorias para a seção de simulação */
        .atividade-row {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        
        .custo-calculado {{
            background-color: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        
        .add-atividade {{
            background-color: #e9ecef;
            border: 2px dashed #6c757d;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .add-atividade:hover {{
            background-color: #d4edda;
            border-color: #28a745;
        }}
        
        /* Estilos para alerts */
        .recomendacao {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        
        .alerta {{
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        
        .dica {{
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        
        .benchmark-card {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-robot"></i> Business Plan com IA
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-home"></i> Início</a>
                <a class="nav-link" href="/simulacao"><i class="fas fa-plus"></i> Nova</a>
                <a class="nav-link" href="/dashboard"><i class="fas fa-chart-line"></i> Dashboard</a>
                <a class="nav-link" href="/analise_ia"><i class="fas fa-brain"></i> Análise IA</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {content}
    </div>

    <footer class="bg-dark text-white mt-5">
        <div class="container text-center py-4">
            <p><i class="fas fa-robot"></i> Sistema com Análise de Inteligência Artificial</p>
            <p class="mb-0">© 2024 - Análise inteligente de planos de negócios escolares</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

def formatar_analise_ia(texto_analise: str) -> str:
    """Formata o texto da análise da IA para HTML"""
    if not texto_analise:
        return '<p class="text-muted">Nenhuma análise disponível.</p>'
    
    # Substituir markdown por HTML básico
    html = texto_analise.replace('# ', '<h5>').replace('\n#', '</h5>\n<h5>')
    html = html.replace('## ', '<h6 class="mt-3">').replace('\n##', '</h6>\n<h6>')
    html = html.replace('- ', '<li>').replace('\n-', '</li>\n<li>')
    html = html.replace('**', '<strong>').replace('**', '</strong>')
    html = html.replace('\n\n', '</p><p>')
    html = html.replace('\n', '<br>')
    
    # Adicionar classes
    html = html.replace('✅', '<span class="text-success">✅</span>')
    html = html.replace('⚠️', '<span class="text-warning">⚠️</span>')
    html = html.replace('🎯', '<span class="text-primary">🎯</span>')
    html = html.replace('📋', '<span class="text-info">📋</span>')
    
    return f'<div class="analise-texto">{html}</div>'

@app.route('/')
def index():
    """Página inicial"""
    content = '''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="analise-ia text-center">
                <h1 class="display-4 mb-4">
                    <i class="fas fa-robot"></i> Business Plan com Análise de IA
                </h1>
                <p class="lead mb-4">
                    Crie seu plano de negócios escolar e receba análise inteligente com recomendações personalizadas
                </p>
                <div class="row mt-4">
                    <div class="col-md-4">
                        <div class="card bg-white text-dark">
                            <div class="card-body">
                                <i class="fas fa-brain fa-3x mb-3" style="color: #667eea;"></i>
                                <h5>Análise Inteligente</h5>
                                <p>IA analisa seu plano e sugere melhorias</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-white text-dark">
                            <div class="card-body">
                                <i class="fas fa-chart-line fa-3x mb-3" style="color: #4ECDC4;"></i>
                                <h5>Benchmarks</h5>
                                <p>Compare com padrões do setor</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-white text-dark">
                            <div class="card-body">
                                <i class="fas fa-lightbulb fa-3x mb-3" style="color: #FF9F1C;"></i>
                                <h5>Recomendações</h5>
                                <p>Planos de ação personalizados</p>
                            </div>
                        </div>
                    </div>
                </div>
                <a href="/simulacao" class="btn btn-light btn-lg mt-4">
                    <i class="fas fa-rocket"></i> Começar Agora
                </a>
            </div>
            
            <div class="card mt-4">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0"><i class="fas fa-info-circle"></i> Como funciona a análise de IA</h4>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h5><i class="fas fa-check-circle text-success"></i> O que a IA analisa:</h5>
                            <ul>
                                <li>Rentabilidade do projeto</li>
                                <li>Estrutura de custos</li>
                                <li>Precificação adequada</li>
                                <li>Alocação de recursos</li>
                                <li>Riscos e oportunidades</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h5><i class="fas fa-bullseye text-warning"></i> Benefícios:</h5>
                            <ul>
                                <li>Detecção de problemas antecipada</li>
                                <li>Otimização de custos</li>
                                <li>Maximização de receitas</li>
                                <li>Plano de ação específico</li>
                                <li>Comparação com mercado</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Business Plan com IA", content)

@app.route('/simulacao')
@app.route('/simulacao/<int:simulacao_id>')
def simulacao(simulacao_id=None):
    """Página de simulação"""
    modo_edicao = simulacao_id is not None
    dados_edicao = {}
    
    if modo_edicao:
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM simulacoes WHERE id = ?', (simulacao_id,))
            simulacao = cursor.fetchone()
            if simulacao:
                dados_completos = json.loads(simulacao['dados_completos'])
                dados_edicao = {
                    'id': simulacao_id,
                    'nome': simulacao['nome'],
                    'dados_entrada': dados_completos.get('entrada', {}),
                    'resultados': dados_completos.get('resultados', {}),
                    'atividades': dados_completos.get('atividades', []),
                    'custos': dados_completos.get('custos', {}),
                    'meses_analise': dados_completos.get('entrada', {}).get('meses_analise', 24)
                }
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar: {e}")
            return redirect('/dashboard')
    
    # HTML dos segmentos
    segmentos_html = ""
    for sigla, info in SEGMENTOS.items():
        segmentos_html += f'''
        <div class="col-md-6 mb-4">
            <div class="card segmento-card segmento-{sigla.replace('_', '-')}">
                <div class="card-header" style="background-color: {info['cor']}; color: white;">
                    <h5 class="mb-0"><i class="fas fa-graduation-cap"></i> {info['nome']}</h5>
                    <small>{info['descricao']}</small>
                </div>
                <div class="card-body">
                    <div id="atividades_container_{sigla}" class="mb-3">
                        <!-- Atividades serão adicionadas aqui -->
                    </div>
                    <div class="add-atividade mb-3" onclick="adicionarAtividade('{sigla}')">
                        <i class="fas fa-plus-circle fa-2x text-success mb-2"></i>
                        <p class="mb-0">Adicionar atividade</p>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    # HTML dos custos - VERSÃO CORRIGIDA
    campos_custos = ""
    categorias = {
        'investimento_inicial': ('info', 'Investimento Inicial'),
        'custos_mensais_fixos': ('warning', 'Custos Mensais Fixos'),
        'custos_mensais_variaveis': ('primary', 'Custos Variáveis'),
        'marketing': ('success', 'Marketing'),
        'recursos_humanos': ('danger', 'Recursos Humanos')
    }
    
    # Mapeamento de ícones
    icons_map = {
        'investimento_inicial': 'tools',
        'custos_mensais_fixos': 'dollar-sign',
        'custos_mensais_variaveis': 'shopping-cart',
        'marketing': 'bullhorn',
        'recursos_humanos': 'users'
    }
    
    for categoria, (cor, titulo) in categorias.items():
        campos_custos += f'''
        <div class="col-md-6 mb-4">
            <div class="card card-custo h-100">
                <div class="card-header bg-{cor} text-white">
                    <h5 class="mb-0"><i class="fas fa-{icons_map.get(categoria, "question-circle")}"></i> {titulo}</h5>
                </div>
                <div class="card-body">
        '''
        
        for item in CATEGORIAS_CUSTOS[categoria]:
            campo_id = f"{categoria}_{item.replace(' ', '_').lower()}"
            is_mensal = 'mensais' in categoria
            valor_edicao = 0
            if dados_edicao.get('custos', {}).get(categoria, {}).get(item, {}):
                valor_edicao = dados_edicao['custos'][categoria][item].get('valor', 0)
            
            campos_custos += f'''
            <div class="mb-3">
                <label class="form-label">{item}:</label>
                <div class="input-group">
                    <span class="input-group-text">R$</span>
                    <input type="number" class="form-control campo-custo" 
                           id="{campo_id}" data-categoria="{categoria}"
                           data-item="{item}" data-mensal="{str(is_mensal).lower()}"
                           value="{valor_edicao}" min="0" step="10">
                    <span class="input-group-text">{'/mês' if is_mensal else ''}</span>
                </div>
            </div>
            '''
        
        campos_custos += '''
                </div>
            </div>
        </div>
        '''
    
    botao_acao = "Calcular e Analisar com IA" if not modo_edicao else "Atualizar e Reanalisar"
    acao_js = f"calcularSimulacao({simulacao_id if modo_edicao else 'null'})"
    
    content = f'''
    <div class="row">
        <div class="col-lg-12">
            <div class="card shadow">
                <div class="card-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <h3 class="mb-0"><i class="fas fa-calculator"></i> {'Editar Simulação' if modo_edicao else 'Nova Simulação'} com IA</h3>
                </div>
                <div class="card-body">
                    <form id="simulacaoForm">
                        <!-- Configuração -->
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Nome da Simulação:</label>
                                    <input type="text" class="form-control" id="nome_simulacao" 
                                           value="{dados_edicao.get('nome', 'Meu Plano Escolar')}">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meses para análise:</label>
                                    <select class="form-select" id="meses_analise">
                                        <option value="12">12 meses</option>
                                        <option value="24" selected>24 meses</option>
                                        <option value="36">36 meses</option>
                                        <option value="60">60 meses</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Atividades -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-tasks"></i> Atividades por Segmento
                                </h4>
                                <p class="text-muted">A IA analisará cada atividade separadamente.</p>
                                <div class="row">
                                    {segmentos_html}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Custos -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-money-bill-wave"></i> Custos do Projeto
                                </h4>
                                <div class="row">
                                    {campos_custos}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Resumo e IA -->
                        <div class="row">
                            <div class="col-md-5">
                                <div class="card">
                                    <div class="card-header bg-success text-white">
                                        <h5 class="mb-0"><i class="fas fa-chart-line"></i> Resumo Financeiro</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="resumo_simulacao">
                                            <p class="text-center text-muted">Preencha os dados para ver o resumo</p>
                                        </div>
                                        <div class="mt-3">
                                            <button type="button" class="btn btn-primary w-100 mb-2" onclick="{acao_js}">
                                                <i class="fas fa-robot"></i> {botao_acao}
                                            </button>
                                            <button type="button" class="btn btn-outline-secondary w-100 mb-2" onclick="resetForm()">
                                                <i class="fas fa-redo"></i> Limpar
                                            </button>
                                            <button type="button" class="btn btn-outline-info w-100" onclick="carregarExemploIA()">
                                                <i class="fas fa-magic"></i> Exemplo com IA
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-7">
                                <div id="analise_rapida" class="mb-3">
                                    <!-- Análise rápida em tempo real -->
                                </div>
                                <div id="graficos_container">
                                    <!-- Gráficos -->
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Template atividade -->
    <template id="template-atividade">
        <div class="atividade-row">
            <div class="row">
                <div class="col-11">
                    <h6><i class="fas fa-dumbbell"></i> <span class="nome-atividade">Nova Atividade</span></h6>
                </div>
                <div class="col-1 text-end">
                    <i class="fas fa-times text-danger" style="cursor: pointer;" onclick="removerAtividade(this)"></i>
                </div>
            </div>
            <div class="row g-2">
                <div class="col-md-6">
                    <input type="text" class="form-control form-control-sm mb-2 nome-atividade-input" placeholder="Nome da atividade" value="Nova Atividade">
                </div>
                <div class="col-md-6">
                    <input type="number" class="form-control form-control-sm mb-2 custo-hora" placeholder="Custo/hora professor" value="50">
                </div>
                <div class="col-md-4">
                    <input type="number" class="form-control form-control-sm mb-2 horas-semanais" placeholder="Horas/semana" value="4">
                </div>
                <div class="col-md-4">
                    <input type="number" class="form-control form-control-sm mb-2 semanas-mes" placeholder="Semanas/mês" value="4">
                </div>
                <div class="col-md-4">
                    <input type="number" class="form-control form-control-sm mb-2 custo-material" placeholder="Custo material/mês" value="100">
                </div>
                <div class="col-md-3">
                    <input type="number" class="form-control form-control-sm mb-2 alunos" placeholder="Alunos" value="10">
                </div>
                <div class="col-md-3">
                    <input type="number" class="form-control form-control-sm mb-2 nao-alunos" placeholder="Não-alunos" value="5">
                </div>
                <div class="col-md-3">
                    <input type="number" class="form-control form-control-sm mb-2 receita-aluno" placeholder="Receita aluno/mês" value="150">
                </div>
                <div class="col-md-3">
                    <input type="number" class="form-control form-control-sm mb-2 receita-nao-aluno" placeholder="Receita não-aluno/mês" value="200">
                </div>
            </div>
            <div class="custo-calculado mt-2 p-2">
                <div class="row small">
                    <div class="col-6">
                        <strong>Custo mensal:</strong><br>
                        <span class="custo-mensal-atividade">R$ 900,00</span>
                    </div>
                    <div class="col-6">
                        <strong>Receita mensal:</strong><br>
                        <span class="receita-mensal-atividade">R$ 2.500,00</span>
                    </div>
                </div>
            </div>
        </div>
    </template>

    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Adicionar uma atividade inicial em cada segmento
        Object.keys({json.dumps(SEGMENTOS)}).forEach(seg => {{
            adicionarAtividade(seg, true);
        }});
        
        // Configurar eventos
        document.getElementById('nome_simulacao').addEventListener('input', atualizarResumoIA);
        document.getElementById('meses_analise').addEventListener('change', atualizarResumoIA);
        document.querySelectorAll('.campo-custo').forEach(campo => {{
            campo.addEventListener('input', atualizarResumoIA);
        }});
        
        atualizarResumoIA();
    }});
    
    function adicionarAtividade(segmento, inicial = false) {{
        const container = document.getElementById(`atividades_container_${{segmento}}`);
        const template = document.getElementById('template-atividade').content.cloneNode(true);
        
        // Configurar eventos
        const campos = template.querySelectorAll('input');
        campos.forEach(campo => {{
            campo.addEventListener('input', function() {{
                if (this.classList.contains('nome-atividade-input')) {{
                    this.closest('.atividade-row').querySelector('.nome-atividade').textContent = this.value;
                }}
                calcularAtividade(this.closest('.atividade-row'));
                atualizarResumoIA();
            }});
        }});
        
        container.appendChild(template);
        if (!inicial) {{
            calcularAtividade(container.lastElementChild);
            atualizarResumoIA();
        }}
    }}
    
    function removerAtividade(elemento) {{
        elemento.closest('.atividade-row').remove();
        atualizarResumoIA();
    }}
    
    function calcularAtividade(atividadeRow) {{
        const custoHora = parseFloat(atividadeRow.querySelector('.custo-hora').value) || 0;
        const horasSemanais = parseFloat(atividadeRow.querySelector('.horas-semanais').value) || 0;
        const semanasMes = parseFloat(atividadeRow.querySelector('.semanas-mes').value) || 4;
        const custoMaterial = parseFloat(atividadeRow.querySelector('.custo-material').value) || 0;
        const alunos = parseInt(atividadeRow.querySelector('.alunos').value) || 0;
        const naoAlunos = parseInt(atividadeRow.querySelector('.nao-alunos').value) || 0;
        const receitaAluno = parseFloat(atividadeRow.querySelector('.receita-aluno').value) || 0;
        const receitaNaoAluno = parseFloat(atividadeRow.querySelector('.receita-nao-aluno').value) || 0;
        
        const custoProfessorMensal = custoHora * horasSemanais * semanasMes;
        const custoMensalTotal = custoProfessorMensal + custoMaterial;
        const receitaMensal = (alunos * receitaAluno) + (naoAlunos * receitaNaoAluno);
        
        atividadeRow.querySelector('.custo-mensal-atividade').textContent = 
            `R$ ${{custoMensalTotal.toLocaleString('pt-BR')}}`;
        atividadeRow.querySelector('.receita-mensal-atividade').textContent = 
            `R$ ${{receitaMensal.toLocaleString('pt-BR')}}`;
        
        return {{ custoMensal: custoMensalTotal, receitaMensal: receitaMensal, alunos: alunos, naoAlunos: naoAlunos }};
    }}
    
    function atualizarResumoIA() {{
        // Coletar dados
        let totalAlunos = 0, totalNaoAlunos = 0, receitaTotal = 0, custoAtividadesTotal = 0;
        const atividades = [];
        
        Object.keys({json.dumps(SEGMENTOS)}).forEach(segmento => {{
            const container = document.getElementById(`atividades_container_${{segmento}}`);
            if (!container) return;
            
            const atividadesRows = container.querySelectorAll('.atividade-row');
            atividadesRows.forEach(row => {{
                const dados = calcularAtividade(row);
                atividades.push({{
                    segmento: segmento,
                    nome: row.querySelector('.nome-atividade-input').value,
                    ...dados
                }});
                
                totalAlunos += dados.alunos;
                totalNaoAlunos += dados.naoAlunos;
                receitaTotal += dados.receitaMensal;
                custoAtividadesTotal += dados.custoMensal;
            }});
        }});
        
        // Custos gerais
        let investimentoTotal = 0, custoMensalTotal = custoAtividadesTotal;
        document.querySelectorAll('.campo-custo').forEach(campo => {{
            const valor = parseFloat(campo.value) || 0;
            if (campo.getAttribute('data-mensal') === 'true') {{
                custoMensalTotal += valor;
            }} else {{
                investimentoTotal += valor;
            }}
        }});
        
        // Indicadores
        const lucroMensal = receitaTotal - custoMensalTotal;
        const margemLucro = receitaTotal > 0 ? (lucroMensal / receitaTotal) * 100 : 0;
        const mesesAnalise = parseInt(document.getElementById('meses_analise').value) || 24;
        let paybackMeses = 0, roiPercentual = 0;
        
        if (lucroMensal > 0 && investimentoTotal > 0) {{
            paybackMeses = investimentoTotal / lucroMensal;
            roiPercentual = ((lucroMensal * mesesAnalise) / investimentoTotal) * 100;
        }}
        
        // Atualizar resumo
        document.getElementById('resumo_simulacao').innerHTML = `
            <table class="table table-sm">
                <tr><td>Atividades:</td><td class="text-end"><span class="badge bg-primary">${{atividades.length}}</span></td></tr>
                <tr><td>Participantes:</td><td class="text-end"><strong>${{totalAlunos + totalNaoAlunos}}</strong></td></tr>
                <tr><td>Receita mensal:</td><td class="text-end text-success">R$ ${{receitaTotal.toLocaleString('pt-BR')}}</td></tr>
                <tr><td>Custo mensal:</td><td class="text-end text-danger">R$ ${{custoMensalTotal.toLocaleString('pt-BR')}}</td></tr>
                <tr><td>Investimento:</td><td class="text-end">R$ ${{investimentoTotal.toLocaleString('pt-BR')}}</td></tr>
                <tr class="table-info"><td><strong>Lucro mensal:</strong></td><td class="text-end"><strong>R$ ${{lucroMensal.toLocaleString('pt-BR')}}</strong></td></tr>
                <tr><td>Margem de lucro:</td><td class="text-end"><span class="badge ${{margemLucro >= 30 ? 'bg-success' : margemLucro >= 15 ? 'bg-warning' : 'bg-danger'}}">${{margemLucro.toFixed(1)}}%</span></td></tr>
                <tr><td>ROI (${{mesesAnalise}} meses):</td><td class="text-end"><span class="badge ${{roiPercentual >= 100 ? 'bg-success' : roiPercentual >= 50 ? 'bg-warning' : 'bg-danger'}}">${{roiPercentual.toFixed(1)}}%</span></td></tr>
            </table>
        `;
        
        // Análise rápida da IA
        fazerAnaliseRapida({{
            lucroMensal: lucroMensal,
            margemLucro: margemLucro,
            roiPercentual: roiPercentual,
            paybackMeses: paybackMeses,
            investimentoTotal: investimentoTotal,
            atividadesCount: atividades.length
        }});
        
        atualizarGraficos(atividades);
    }}
    
    function fazerAnaliseRapida(dados) {{
        const container = document.getElementById('analise_rapida');
        let analiseHTML = '<div class="card"><div class="card-header bg-info text-white"><h6 class="mb-0"><i class="fas fa-bolt"></i> Análise Rápida</h6></div><div class="card-body">';
        
        // Análise baseada em benchmarks
        if (dados.margemLucro < 15) {{
            analiseHTML += `<div class="alerta"><i class="fas fa-exclamation-triangle"></i> <strong>Atenção:</strong> Margem de lucro baixa (${{dados.margemLucro.toFixed(1)}}%). Considere aumentar receitas ou reduzir custos.</div>`;
        }} else if (dados.margemLucro >= 30) {{
            analiseHTML += `<div class="recomendacao"><i class="fas fa-check-circle"></i> <strong>Excelente:</strong> Margem de lucro saudável (${{dados.margemLucro.toFixed(1)}}%).</div>`;
        }}
        
        if (dados.roiPercentual < 50) {{
            analiseHTML += `<div class="alerta"><i class="fas fa-exclamation-triangle"></i> ROI abaixo do ideal (${{dados.roiPercentual.toFixed(1)}}%). Investimento pode ser muito alto para o retorno.</div>`;
        }}
        
        if (dados.paybackMeses > 36 && dados.paybackMeses > 0) {{
            analiseHTML += `<div class="alerta"><i class="fas fa-clock"></i> Payback muito longo (${{dados.paybackMeses.toFixed(1)}} meses). Considere reduzir investimento inicial.</div>`;
        }}
        
        if (dados.atividadesCount === 0) {{
            analiseHTML += `<div class="dica"><i class="fas fa-lightbulb"></i> Adicione atividades para começar a análise.</div>`;
        }} else if (dados.atividadesCount < 3) {{
            analiseHTML += `<div class="dica"><i class="fas fa-lightbulb"></i> Considere diversificar com mais atividades para reduzir riscos.</div>`;
        }}
        
        analiseHTML += '</div></div>';
        container.innerHTML = analiseHTML;
    }}
    
    function atualizarGraficos(atividades) {{
        if (atividades.length === 0) return;
        
        const container = document.getElementById('graficos_container');
        container.innerHTML = `
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-chart-bar"></i> Visualização</h6>
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="chartAtividades"></canvas>
                    </div>
                </div>
            </div>
        `;
        
        // Gráfico simples
        setTimeout(() => {{
            const ctx = document.getElementById('chartAtividades').getContext('2d');
            const cores = ['#FF6B8B', '#4ECDC4', '#45B7D1', '#FF9F1C'];
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: atividades.slice(0, 8).map(a => a.nome.substring(0, 10) + '...'),
                    datasets: [
                        {{
                            label: 'Receita',
                            data: atividades.slice(0, 8).map(a => a.receitaMensal),
                            backgroundColor: cores[0]
                        }},
                        {{
                            label: 'Custo',
                            data: atividades.slice(0, 8).map(a => a.custoMensal),
                            backgroundColor: cores[2]
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});
        }}, 100);
    }}
    
    async function calcularSimulacao(simulacaoId = null) {{
        const btn = document.querySelector('button[onclick*="calcularSimulacao"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analisando com IA...';
        btn.disabled = true;
        
        try {{
            // Coletar dados
            const dados = {{
                nome: document.getElementById('nome_simulacao').value,
                meses_analise: parseInt(document.getElementById('meses_analise').value) || 24
            }};
            
            // Atividades
            dados.atividades = [];
            Object.keys({json.dumps(SEGMENTOS)}).forEach(segmento => {{
                const container = document.getElementById(`atividades_container_${{segmento}}`);
                if (!container) return;
                
                const atividadesRows = container.querySelectorAll('.atividade-row');
                atividadesRows.forEach(row => {{
                    dados.atividades.push({{
                        segmento: segmento,
                        nome: row.querySelector('.nome-atividade-input').value,
                        custo_hora_professor: parseFloat(row.querySelector('.custo-hora').value) || 0,
                        horas_semanais: parseFloat(row.querySelector('.horas-semanais').value) || 0,
                        semanas_mes: parseFloat(row.querySelector('.semanas-mes').value) || 4,
                        custo_material_mensal: parseFloat(row.querySelector('.custo-material').value) || 0,
                        alunos: parseInt(row.querySelector('.alunos').value) || 0,
                        nao_alunos: parseInt(row.querySelector('.nao-alunos').value) || 0,
                        receita_aluno: parseFloat(row.querySelector('.receita-aluno').value) || 0,
                        receita_nao_aluno: parseFloat(row.querySelector('.receita-nao-aluno').value) || 0
                    }});
                }});
            }});
            
            // Custos
            dados.custos = {{}};
            document.querySelectorAll('.campo-custo').forEach(campo => {{
                const categoria = campo.getAttribute('data-categoria');
                const item = campo.getAttribute('data-item');
                const valor = parseFloat(campo.value) || 0;
                const isMensal = campo.getAttribute('data-mensal') === 'true';
                
                if (!dados.custos[categoria]) {{
                    dados.custos[categoria] = {{}};
                }}
                dados.custos[categoria][item] = {{ valor: valor, mensal: isMensal }};
            }});
            
            // Enviar para API
            const url = simulacaoId ? `/api/atualizar_simulacao_ia/${{simulacaoId}}` : '/api/calcular_com_ia';
            const method = simulacaoId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {{
                method: method,
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(dados)
            }});
            
            if (!response.ok) throw new Error(await response.text());
            
            const resultados = await response.json();
            
            // Mostrar sucesso
            document.getElementById('analise_rapida').innerHTML = `
                <div class="alert alert-success">
                    <h5><i class="fas fa-check-circle"></i> Análise completa!</h5>
                    <p>Redirecionando para relatório detalhado com IA...</p>
                </div>
            `;
            
            setTimeout(() => {{
                window.location.href = '/resultado_com_ia';
            }}, 2000);
            
        }} catch (error) {{
            alert('Erro: ' + error.message);
        }} finally {{
            btn.innerHTML = originalText;
            btn.disabled = false;
        }}
    }}
    
    function carregarExemploIA() {{
        if (confirm('Carregar exemplo otimizado com recomendações de IA?')) {{
            // Limpar
            Object.keys({json.dumps(SEGMENTOS)}).forEach(seg => {{
                const container = document.getElementById(`atividades_container_${{seg}}`);
                if (container) container.innerHTML = '';
            }});
            
            // Exemplo otimizado pela IA
            const exemplos = [
                {{ segmento: 'ei', nome: 'Musicalização Infantil', custo_hora: 48, horas: 8, alunos: 18, nao_alunos: 6, receita_aluno: 135, receita_nao_aluno: 180, material: 220 }},
                {{ segmento: 'ef_i', nome: 'Robótica Educacional', custo_hora: 65, horas: 10, alunos: 16, nao_alunos: 8, receita_aluno: 195, receita_nao_aluno: 260, material: 450 }},
                {{ segmento: 'ef_ii', nome: 'Olimpíadas de Matemática', custo_hora: 58, horas: 6, alunos: 20, nao_alunos: 10, receita_aluno: 160, receita_nao_aluno: 210, material: 180 }},
                {{ segmento: 'em', nome: 'Preparatório Universitário', custo_hora: 75, horas: 15, alunos: 22, nao_alunos: 12, receita_aluno: 240, receita_nao_aluno: 320, material: 350 }}
            ];
            
            exemplos.forEach(ex => {{
                const container = document.getElementById(`atividades_container_${{ex.segmento}}`);
                const template = document.getElementById('template-atividade').content.cloneNode(true);
                
                template.querySelector('.nome-atividade-input').value = ex.nome;
                template.querySelector('.nome-atividade').textContent = ex.nome;
                template.querySelector('.custo-hora').value = ex.custo_hora;
                template.querySelector('.horas-semanais').value = ex.horas;
                template.querySelector('.alunos').value = ex.alunos;
                template.querySelector('.nao-alunos').value = ex.nao_alunos;
                template.querySelector('.receita-aluno').value = ex.receita_aluno;
                template.querySelector('.receita-nao-aluno').value = ex.receita_nao_aluno;
                template.querySelector('.custo-material').value = ex.material;
                
                container.appendChild(template);
            }});
            
            // Custos otimizados
            const custosOtimizados = {{
                'investimento_inicial_reforma': 45000,
                'investimento_inicial_equipamentos': 28000,
                'custos_mensais_fixos_aluguel': 7500,
                'custos_mensais_fixos_energia': 1200,
                'recursos_humanos_salários_professores': 12000,
                'marketing_site': 800
            }};
            
            Object.entries(custosOtimizados).forEach(([id, valor]) => {{
                const campo = document.getElementById(id);
                if (campo) campo.value = valor;
            }});
            
            document.getElementById('nome_simulacao').value = 'Plano Otimizado por IA';
            atualizarResumoIA();
        }}
    }}
    
    function resetForm() {{
        if (confirm('Limpar todos os dados?')) {{
            Object.keys({json.dumps(SEGMENTOS)}).forEach(seg => {{
                const container = document.getElementById(`atividades_container_${{seg}}`);
                if (container) container.innerHTML = '';
                adicionarAtividade(seg, true);
            }});
            
            document.querySelectorAll('.campo-custo').forEach(campo => campo.value = 0);
            document.getElementById('nome_simulacao').value = 'Meu Plano Escolar';
            document.getElementById('meses_analise').value = '24';
            
            atualizarResumoIA();
        }}
    }}
    </script>
    '''
    
    return get_base_html("Simulação com IA", content)

def analisar_com_ia(dados_simulacao: Dict) -> Dict:
    """
    Analisa a simulação usando IA (OpenAI)
    Retorna recomendações, alertas e plano de ação
    """
    try:
        # Preparar prompt para a IA
        atividades_texto = ""
        for i, atividade in enumerate(dados_simulacao.get('atividades', [])[:10], 1):
            atividades_texto += f"{i}. {atividade['nome']} ({atividade['segmento']}): "
            atividades_texto += f"{atividade['alunos']} alunos + {atividade['nao_alunos']} não-alunos, "
            atividades_texto += f"Receita: R${atividade.get('receita_mensal', 0):,.0f}/mês, "
            atividades_texto += f"Custo: R${atividade.get('custo_total_mensal', 0):,.0f}/mês\n"
        
        resumo = dados_simulacao.get('resultados', {})
        
        prompt = f"""
        Analise este plano de negócios para uma escola/centro educacional:
        
        RESUMO:
        - Total de atividades: {len(dados_simulacao.get('atividades', []))}
        - Investimento inicial: R${resumo.get('investimento_inicial', 0):,.0f}
        - Receita mensal: R${resumo.get('receita_mensal_atividades', 0):,.0f}
        - Custo mensal total: R${resumo.get('custo_mensal_total', 0):,.0f}
        - Lucro mensal: R${resumo.get('lucro_mensal', 0):,.0f}
        - Margem de lucro: {resumo.get('margem_lucro', 0):.1f}%
        - ROI ({resumo.get('meses_analise', 24)} meses): {resumo.get('roi_percentual', 0):.1f}%
        - Payback: {resumo.get('payback_meses', 0):.1f} meses
        
        ATIVIDADES:
        {atividades_texto}
        
        Por favor, forneça uma análise em português brasileiro com:
        1. PONTOS FORTES (até 3 itens)
        2. PONTOS DE ATENÇÃO/RISCOS (até 3 itens)
        3. RECOMENDAÇÕES ESPECÍFICAS (3-5 recomendações práticas)
        4. PLANO DE AÇÃO (passos concretos para implementação)
        5. BENCHMARK COMPARATIVO (como está vs mercado)
        
        Seja específico, prático e foque em ações que possam ser implementadas.
        Use markdown para formatação.
        """
        
        # Chamar OpenAI API (versão simplificada se não tiver chave)
        if openai.api_key and openai.api_key != '':
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Você é um consultor especializado em planejamento financeiro para instituições educacionais."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                analise_texto = response.choices[0].message.content
            except:
                analise_texto = gerar_analise_fallback(dados_simulacao)
        else:
            # Fallback: análise baseada em regras
            analise_texto = gerar_analise_fallback(dados_simulacao)
        
        # Processar a análise
        return {
            'analise_completa': analise_texto,
            'recomendacoes': extrair_recomendacoes(analise_texto),
            'alertas': identificar_alertas(resumo),
            'pontos_fortes': identificar_pontos_fortes(resumo),
            'plano_acao': extrair_plano_acao(analise_texto)
        }
        
    except Exception as e:
        print(f"Erro na análise com IA: {e}")
        return {
            'analise_completa': "Análise temporariamente indisponível. Use os benchmarks abaixo para orientação.",
            'recomendacoes': [],
            'alertas': identificar_alertas(dados_simulacao.get('resultados', {})),
            'pontos_fortes': identificar_pontos_fortes(dados_simulacao.get('resultados', {})),
            'plano_acao': []
        }

def gerar_analise_fallback(dados_simulacao: Dict) -> str:
    """Gera análise quando a IA não está disponível"""
    resumo = dados_simulacao.get('resultados', {})
    
    analise = "# Análise do Plano de Negócios\n\n"
    
    # Pontos fortes
    analise += "## ✅ PONTOS FORTES\n\n"
    if resumo.get('margem_lucro', 0) >= 25:
        analise += f"- Margem de lucro saudável ({resumo.get('margem_lucro', 0):.1f}%)\n"
    if resumo.get('roi_percentual', 0) >= 100:
        analise += f"- ROI excelente ({resumo.get('roi_percentual', 0):.1f}% em {resumo.get('meses_analise', 24)} meses)\n"
    if resumo.get('payback_meses', 0) <= 24 and resumo.get('payback_meses', 0) > 0:
        analise += f"- Payback rápido ({resumo.get('payback_meses', 0):.1f} meses)\n"
    if len(dados_simulacao.get('atividades', [])) >= 4:
        analise += f"- Boa diversificação ({len(dados_simulacao.get('atividades', []))} atividades)\n"
    
    # Pontos de atenção
    analise += "\n## ⚠️ PONTOS DE ATENÇÃO\n\n"
    if resumo.get('margem_lucro', 0) < 15:
        analise += f"- Margem de lucro baixa ({resumo.get('margem_lucro', 0):.1f}%). Considere revisar preços ou custos.\n"
    if resumo.get('payback_meses', 0) > 36:
        analise += f"- Payback muito longo ({resumo.get('payback_meses', 0):.1f} meses). Risco alto.\n"
    if resumo.get('investimento_inicial', 0) > 100000:
        analise += f"- Investimento inicial elevado (R${resumo.get('investimento_inicial', 0):,.0f})\n"
    
    # Recomendações
    analise += "\n## 🎯 RECOMENDAÇÕES\n\n"
    analise += "1. **Otimize a estrutura de custos**: Revise custos variáveis e negocie com fornecedores\n"
    analise += "2. **Aumente o valor percebido**: Diferencie suas atividades para justificar preços mais altos\n"
    analise += "3. **Diversifique as fontes de receita**: Considere pacotes semestrais/anuais com desconto\n"
    analise += "4. **Controle o investimento inicial**: Foque em equipamentos essenciais primeiro\n"
    analise += "5. **Monitore a relação aluno/professor**: Otimize para maximizar a rentabilidade\n"
    
    # Plano de ação
    analise += "\n## 📋 PLANO DE AÇÃO\n\n"
    analise += "**Mês 1-3:**\n"
    analise += "- Implementar 2-3 atividades principais\n"
    analise += "- Campanha de lançamento com preços promocionais\n"
    analise += "- Contratação de equipe mínima\n\n"
    
    analise += "**Mês 4-6:**\n"
    analise += "- Avaliar desempenho das atividades\n"
    analise += "- Ajustar preços conforme aceitação do mercado\n"
    analise += "- Expandir para atividades adicionais\n\n"
    
    analise += "**Mês 7-12:**\n"
    analise += "- Buscar eficiências operacionais\n"
    analise += "- Implementar pacotes de fidelização\n"
    analise += "- Expandir para novos segmentos\n"
    
    return analise

def extrair_recomendacoes(analise_texto: str) -> List[str]:
    """Extrai recomendações da análise"""
    recomendacoes = []
    linhas = analise_texto.split('\n')
    
    for linha in linhas:
        linha = linha.strip()
        if linha.startswith('- ') or linha.startswith('* ') or linha.startswith('1. ') or linha.startswith('2. '):
            if any(keyword in linha.lower() for keyword in ['recomendo', 'sugiro', 'aconselho', 'considere', 'sugestão']):
                recomendacoes.append(linha)
    
    return recomendacoes[:5] if recomendacoes else [
        "Revise a estrutura de custos para melhorar a margem",
        "Considere aumentar o preço das atividades mais populares",
        "Diversifique as fontes de receita com pacotes promocionais"
    ]

def identificar_alertas(resumo: Dict) -> List[Dict]:
    """Identifica alertas baseados em benchmarks"""
    alertas = []
    
    if resumo.get('margem_lucro', 0) < 15:
        alertas.append({
            'tipo': 'alto',
            'mensagem': f'Margem de lucro muito baixa ({resumo.get("margem_lucro", 0):.1f}%)',
            'acao': 'Aumente receitas ou reduza custos'
        })
    
    if resumo.get('payback_meses', 0) > 36:
        alertas.append({
            'tipo': 'alto',
            'mensagem': f'Payback muito longo ({resumo.get("payback_meses", 0):.1f} meses)',
            'acao': 'Reduza investimento inicial ou aumente lucro'
        })
    
    if resumo.get('roi_percentual', 0) < 50:
        alertas.append({
            'tipo': 'medio',
            'mensagem': f'ROI abaixo do ideal ({resumo.get("roi_percentual", 0):.1f}%)',
            'acao': 'Otimize a relação custo-benefício'
        })
    
    return alertas

def identificar_pontos_fortes(resumo: Dict) -> List[Dict]:
    """Identifica pontos fortes"""
    pontos = []
    
    if resumo.get('margem_lucro', 0) >= 25:
        pontos.append({
            'aspecto': 'Rentabilidade',
            'detalhe': f'Margem de lucro excelente: {resumo.get("margem_lucro", 0):.1f}%'
        })
    
    if resumo.get('roi_percentual', 0) >= 100:
        pontos.append({
            'aspecto': 'Retorno sobre Investimento',
            'detalhe': f'ROI muito bom: {resumo.get("roi_percentual", 0):.1f}%'
        })
    
    if resumo.get('payback_meses', 0) <= 24 and resumo.get('payback_meses', 0) > 0:
        pontos.append({
            'aspecto': 'Recuperação do Investimento',
            'detalhe': f'Payback rápido: {resumo.get("payback_meses", 0):.1f} meses'
        })
    
    return pontos

def extrair_plano_acao(analise_texto: str) -> List[str]:
    """Extrai plano de ação"""
    plano = []
    dentro_plano = False
    
    for linha in analise_texto.split('\n'):
        linha = linha.strip()
        if 'PLANO DE AÇÃO' in linha or 'plano de ação' in linha.lower():
            dentro_plano = True
            continue
        if dentro_plano and linha and (linha.startswith('- ') or linha.startswith('* ') or linha.startswith('1. ')):
            plano.append(linha)
        if dentro_plano and linha.startswith('##'):
            break
    
    return plano[:6] if plano else [
        "Mês 1-3: Implementação inicial e captação de alunos",
        "Mês 4-6: Ajustes baseados em feedback e otimização",
        "Mês 7-12: Expansão e consolidação"
    ]

@app.route('/api/calcular_com_ia', methods=['POST'])
def api_calcular_com_ia():
    """API para cálculo com análise de IA"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'error': 'Sem dados'}), 400
        
        print("Processando simulação com IA...")
        
        # Calcular resultados
        resultados = calcular_resultados(dados)
        
        # Gerar análise com IA
        dados_simulacao = {
            'entrada': dados,
            'resultados': resultados,
            'atividades': processar_atividades(dados.get('atividades', [])),
            'custos': dados.get('custos', {})
        }
        
        analise_ia = analisar_com_ia(dados_simulacao)
        
        # Salvar na sessão
        session['simulacao_com_ia'] = {
            'dados_entrada': dados,
            'resultados': resultados,
            'analise_ia': analise_ia,
            'atividades_detalhadas': processar_atividades(dados.get('atividades', [])),
            'nome_simulacao': dados.get('nome', 'Análise com IA')
        }
        
        # Salvar no banco
        salvar_no_banco(dados, resultados, analise_ia)
        
        return jsonify({
            **resultados,
            'analise_disponivel': True,
            'alertas': analise_ia.get('alertas', []),
            'recomendacoes_count': len(analise_ia.get('recomendacoes', []))
        })
        
    except Exception as e:
        print(f"Erro na API com IA: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/atualizar_simulacao_ia/<int:simulacao_id>', methods=['PUT'])
def api_atualizar_simulacao_ia(simulacao_id):
    """API para atualizar com IA"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'error': 'Sem dados'}), 400
        
        # Calcular resultados
        resultados = calcular_resultados(dados)
        
        # Gerar análise com IA
        dados_simulacao = {
            'entrada': dados,
            'resultados': resultados,
            'atividades': processar_atividades(dados.get('atividades', [])),
            'custos': dados.get('custos', {})
        }
        
        analise_ia = analisar_com_ia(dados_simulacao)
        
        # Salvar na sessão
        session['simulacao_com_ia'] = {
            'dados_entrada': dados,
            'resultados': resultados,
            'analise_ia': analise_ia,
            'atividades_detalhadas': processar_atividades(dados.get('atividades', [])),
            'nome_simulacao': dados.get('nome', 'Análise com IA')
        }
        
        # Atualizar no banco
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE simulacoes SET
                nome = ?,
                data_atualizacao = ?,
                total_alunos = ?,
                total_participantes = ?,
                investimento_total = ?,
                custo_mensal_total = ?,
                receita_mensal_total = ?,
                lucro_mensal_total = ?,
                payback_meses = ?,
                roi_percentual = ?,
                margem_lucro = ?,
                dados_completos = ?,
                analise_ia = ?
            WHERE id = ?
            ''', (
                dados.get('nome', 'Simulação IA'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                resultados['total_alunos'],
                resultados['total_participantes'],
                resultados['investimento_inicial'],
                resultados['custo_mensal_total'],
                resultados['receita_mensal_atividades'],
                resultados['lucro_mensal'],
                resultados.get('payback_meses', 0),
                resultados.get('roi_percentual', 0),
                resultados.get('margem_lucro', 0),
                json.dumps({
                    'entrada': dados,
                    'resultados': resultados,
                    'atividades': processar_atividades(dados.get('atividades', []))
                }),
                json.dumps(analise_ia),
                simulacao_id
            ))
            
            # Remover atividades antigas
            cursor.execute('DELETE FROM atividades_simulacao WHERE simulacao_id = ?', (simulacao_id,))
            
            # Salvar novas atividades
            for atividade in processar_atividades(dados.get('atividades', [])):
                cursor.execute('''
                INSERT INTO atividades_simulacao (
                    simulacao_id, segmento, nome_atividade, custo_hora_professor,
                    horas_semanais, semanas_mes, alunos, nao_alunos,
                    receita_aluno, receita_nao_aluno, custo_material_mensal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    simulacao_id,
                    atividade['segmento'],
                    atividade['nome'],
                    atividade['custo_hora_professor'],
                    atividade['horas_semanais'],
                    atividade['semanas_mes'],
                    atividade['alunos'],
                    atividade['nao_alunos'],
                    atividade['receita_aluno'],
                    atividade['receita_nao_aluno'],
                    atividade['custo_material_mensal']
                ))
            
            conn.commit()
            conn.close()
            print(f"✅ Simulação #{simulacao_id} atualizada com análise de IA!")
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar no banco: {e}")
        
        return jsonify({
            **resultados,
            'analise_disponivel': True,
            'alertas': analise_ia.get('alertas', []),
            'recomendacoes_count': len(analise_ia.get('recomendacoes', []))
        })
        
    except Exception as e:
        print(f"Erro na API atualizar com IA: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/excluir_simulacao/<int:simulacao_id>', methods=['DELETE'])
def api_excluir_simulacao(simulacao_id):
    """API para excluir simulação"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Primeiro excluir atividades relacionadas
        cursor.execute('DELETE FROM atividades_simulacao WHERE simulacao_id = ?', (simulacao_id,))
        
        # Depois excluir a simulação
        cursor.execute('DELETE FROM simulacoes WHERE id = ?', (simulacao_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Simulação excluída com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao excluir simulação: {e}")
        return jsonify({'error': str(e)}), 500

def calcular_resultados(dados: Dict) -> Dict:
    """Calcula resultados financeiros"""
    # Processar atividades
    atividades = processar_atividades(dados.get('atividades', []))
    
    # Totais
    totais = {
        'total_alunos': sum(a['alunos'] for a in atividades),
        'total_nao_alunos': sum(a['nao_alunos'] for a in atividades),
        'receita_mensal_atividades': sum(a['receita_mensal'] for a in atividades),
        'custo_mensal_atividades': sum(a['custo_total_mensal'] for a in atividades),
        'investimento_inicial': 0,
        'custo_mensal_geral': 0
    }
    
    # Custos
    for categoria, itens in dados.get('custos', {}).items():
        for item, info in itens.items():
            valor = info.get('valor', 0)
            if info.get('mensal'):
                totais['custo_mensal_geral'] += valor
            else:
                totais['investimento_inicial'] += valor
    
    # Totais finais
    totais['total_participantes'] = totais['total_alunos'] + totais['total_nao_alunos']
    totais['custo_mensal_total'] = totais['custo_mensal_atividades'] + totais['custo_mensal_geral']
    totais['lucro_mensal'] = totais['receita_mensal_atividades'] - totais['custo_mensal_total']
    
    # Margem e ROI
    totais['margem_lucro'] = (totais['lucro_mensal'] / totais['receita_mensal_atividades'] * 100) if totais['receita_mensal_atividades'] > 0 else 0
    
    meses_analise = dados.get('meses_analise', 24)
    if totais['lucro_mensal'] > 0 and totais['investimento_inicial'] > 0:
        totais['payback_meses'] = totais['investimento_inicial'] / totais['lucro_mensal']
        totais['roi_percentual'] = ((totais['lucro_mensal'] * meses_analise) / totais['investimento_inicial']) * 100
    else:
        totais['payback_meses'] = 0
        totais['roi_percentual'] = 0
    
    totais['meses_analise'] = meses_analise
    totais['total_atividades'] = len(atividades)
    
    return totais

def processar_atividades(atividades_raw: List) -> List:
    """Processa atividades com cálculos detalhados"""
    atividades = []
    for a in atividades_raw:
        custo_professor = a['custo_hora_professor'] * a['horas_semanais'] * a['semanas_mes']
        custo_total = custo_professor + a['custo_material_mensal']
        receita = (a['alunos'] * a['receita_aluno']) + (a['nao_alunos'] * a['receita_nao_aluno'])
        
        atividades.append({
            **a,
            'custo_professor_mensal': custo_professor,
            'custo_total_mensal': custo_total,
            'receita_mensal': receita,
            'lucro_mensal': receita - custo_total,
            'margem_atividade': (receita - custo_total) / receita * 100 if receita > 0 else 0
        })
    return atividades

def salvar_no_banco(dados: Dict, resultados: Dict, analise_ia: Dict):
    """Salva simulação no banco"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO simulacoes (
            nome, data_criacao, data_atualizacao, total_alunos, total_participantes,
            investimento_total, custo_mensal_total, receita_mensal_total,
            lucro_mensal_total, payback_meses, roi_percentual, margem_lucro,
            dados_completos, analise_ia
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            dados.get('nome', 'Simulação IA'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            resultados['total_alunos'],
            resultados['total_participantes'],
            resultados['investimento_inicial'],
            resultados['custo_mensal_total'],
            resultados['receita_mensal_atividades'],
            resultados['lucro_mensal'],
            resultados.get('payback_meses', 0),
            resultados.get('roi_percentual', 0),
            resultados.get('margem_lucro', 0),
            json.dumps({
                'entrada': dados,
                'resultados': resultados,
                'atividades': processar_atividades(dados.get('atividades', []))
            }),
            json.dumps(analise_ia)
        ))
        
        simulacao_id = cursor.lastrowid
        
        # Salvar atividades
        for atividade in processar_atividades(dados.get('atividades', [])):
            cursor.execute('''
            INSERT INTO atividades_simulacao (
                simulacao_id, segmento, nome_atividade, custo_hora_professor,
                horas_semanais, semanas_mes, alunos, nao_alunos,
                receita_aluno, receita_nao_aluno, custo_material_mensal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                simulacao_id,
                atividade['segmento'],
                atividade['nome'],
                atividade['custo_hora_professor'],
                atividade['horas_semanais'],
                atividade['semanas_mes'],
                atividade['alunos'],
                atividade['nao_alunos'],
                atividade['receita_aluno'],
                atividade['receita_nao_aluno'],
                atividade['custo_material_mensal']
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Simulação #{simulacao_id} salva com análise de IA!")
        
    except Exception as e:
        print(f"⚠️ Erro ao salvar no banco: {e}")

@app.route('/resultado_com_ia')
def resultado_com_ia():
    """Página de resultados com análise de IA"""
    if 'simulacao_com_ia' not in session:
        return redirect('/simulacao')
    
    dados = session['simulacao_com_ia']
    resultados = dados['resultados']
    analise_ia = dados['analise_ia']
    atividades = dados['atividades_detalhadas']
    nome_simulacao = dados['nome_simulacao']
    
    # HTML para análise de IA
    analise_html = f'''
    <div class="analise-ia">
        <h4><i class="fas fa-robot"></i> Análise de Inteligência Artificial</h4>
        <div class="mt-3">
            {formatar_analise_ia(analise_ia['analise_completa'])}
        </div>
    </div>
    '''
    
    # HTML para alertas
    alertas_html = ""
    if analise_ia.get('alertas'):
        for alerta in analise_ia['alertas']:
            alertas_html += f'''
            <div class="alert alert-{"danger" if alerta["tipo"] == "alto" else "warning"}">
                <i class="fas fa-exclamation-triangle"></i> <strong>{alerta["mensagem"]}</strong>
                <br><small>{alerta["acao"]}</small>
            </div>
            '''
    
    # HTML para pontos fortes
    pontos_html = ""
    if analise_ia.get('pontos_fortes'):
        for ponto in analise_ia['pontos_fortes']:
            pontos_html += f'''
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i> <strong>{ponto["aspecto"]}:</strong> {ponto["detalhe"]}
            </div>
            '''
    
    # HTML para recomendações
    recomendacoes_html = ""
    if analise_ia.get('recomendacoes'):
        recomendacoes_html = '<h5><i class="fas fa-lightbulb"></i> Recomendações da IA</h5><ul>'
        for rec in analise_ia['recomendacoes'][:5]:
            recomendacoes_html += f'<li>{rec}</li>'
        recomendacoes_html += '</ul>'
    
    # HTML para plano de ação
    plano_acao_html = ""
    if analise_ia.get('plano_acao'):
        plano_acao_html = '<h5><i class="fas fa-clipboard-list"></i> Plano de Ação</h5><ul>'
        for passo in analise_ia['plano_acao'][:6]:
            plano_acao_html += f'<li>{passo}</li>'
        plano_acao_html += '</ul>'
    
    # Tabela de resultados
    resultados_html = f'''
    <table class="table table-bordered">
        <thead class="table-dark">
            <tr>
                <th colspan="2" class="text-center">RESUMO FINANCEIRO</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Investimento Inicial</strong></td>
                <td class="text-end">R$ {resultados.get('investimento_inicial', 0):,.2f}</td>
            </tr>
            <tr>
                <td><strong>Receita Mensal</strong></td>
                <td class="text-end text-success">R$ {resultados.get('receita_mensal_atividades', 0):,.2f}</td>
            </tr>
            <tr>
                <td><strong>Custo Mensal Total</strong></td>
                <td class="text-end text-danger">R$ {resultados.get('custo_mensal_total', 0):,.2f}</td>
            </tr>
            <tr class="table-info">
                <td><strong>Lucro Mensal</strong></td>
                <td class="text-end"><strong>R$ {resultados.get('lucro_mensal', 0):,.2f}</strong></td>
            </tr>
            <tr>
                <td><strong>Margem de Lucro</strong></td>
                <td class="text-end">
                    <span class="badge badge-fixed { 'bg-success' if resultados.get('margem_lucro', 0) >= 25 else 'bg-warning' if resultados.get('margem_lucro', 0) >= 15 else 'bg-danger' }">
                        {resultados.get('margem_lucro', 0):.1f}%
                    </span>
                </td>
            </tr>
            <tr>
                <td><strong>ROI ({resultados.get('meses_analise', 24)} meses)</strong></td>
                <td class="text-end">
                    <span class="badge badge-fixed { 'bg-success' if resultados.get('roi_percentual', 0) >= 100 else 'bg-warning' if resultados.get('roi_percentual', 0) >= 50 else 'bg-danger' }">
                        {resultados.get('roi_percentual', 0):.1f}%
                    </span>
                </td>
            </tr>
            <tr>
                <td><strong>Payback (meses)</strong></td>
                <td class="text-end">
                    <span class="badge badge-fixed { 'bg-success' if resultados.get('payback_meses', 0) <= 24 else 'bg-warning' if resultados.get('payback_meses', 0) <= 36 else 'bg-danger' }">
                        {resultados.get('payback_meses', 0):.1f} meses
                    </span>
                </td>
            </tr>
        </tbody>
    </table>
    '''
    
    # Tabela de atividades
    atividades_html = ""
    if atividades:
        atividades_html = '''
        <div class="card mt-4">
            <div class="card-header bg-light">
                <h5 class="mb-0"><i class="fas fa-tasks"></i> Detalhamento das Atividades</h5>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover table-sm mb-0 table-fixed">
                        <thead class="table-light">
                            <tr>
                                <th class="col-atividade-nome">Atividade</th>
                                <th class="col-atividade-segmento">Segmento</th>
                                <th class="col-atividade-alunos text-center">Alunos</th>
                                <th class="col-atividade-nao-alunos text-center">Não-Alunos</th>
                                <th class="col-atividade-receita text-end">Receita</th>
                                <th class="col-atividade-custo text-end">Custo</th>
                                <th class="col-atividade-lucro text-end">Lucro</th>
                                <th class="col-atividade-margem text-center">Margem</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for ativ in atividades:
            atividades_html += f'''
                            <tr>
                                <td class="col-atividade-nome">
                                    <span class="text-truncate-cell" title="{ativ.get('nome', 'Sem nome')}">
                                        {ativ.get('nome', 'Sem nome')}
                                    </span>
                                </td>
                                <td class="col-atividade-segmento">
                                    <span class="badge badge-fixed" style="background-color: {SEGMENTOS.get(ativ.get('segmento', 'ei'), {}).get('cor', '#ccc')}">
                                        {SEGMENTOS.get(ativ.get('segmento', 'ei'), {}).get('nome', 'EI')}
                                    </span>
                                </td>
                                <td class="col-atividade-alunos text-center">{ativ.get('alunos', 0)}</td>
                                <td class="col-atividade-nao-alunos text-center">{ativ.get('nao_alunos', 0)}</td>
                                <td class="col-atividade-receita text-end text-success">R$ {ativ.get('receita_mensal', 0):,.2f}</td>
                                <td class="col-atividade-custo text-end text-danger">R$ {ativ.get('custo_total_mensal', 0):,.2f}</td>
                                <td class="col-atividade-lucro text-end { 'text-success' if ativ.get('lucro_mensal', 0) > 0 else 'text-danger' }">
                                    R$ {ativ.get('lucro_mensal', 0):,.2f}
                                </td>
                                <td class="col-atividade-margem text-center">
                                    <span class="badge badge-fixed { 'bg-success' if ativ.get('margem_atividade', 0) >= 30 else 'bg-warning' if ativ.get('margem_atividade', 0) >= 15 else 'bg-danger' }">
                                        {ativ.get('margem_atividade', 0):.1f}%
                                    </span>
                                </td>
                            </tr>
            '''
        
        atividades_html += '''
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        '''
    
    content = f'''
    <div class="row">
        <div class="col-lg-12">
            <div class="card shadow mb-4">
                <div class="card-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <h3 class="mb-0"><i class="fas fa-chart-line"></i> Resultados da Simulação: {nome_simulacao}</h3>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            {analise_html}
                        </div>
                        <div class="col-md-4">
                            {resultados_html}
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            {alertas_html}
                            {pontos_html}
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0"><i class="fas fa-bullseye"></i> Benchmarks do Setor</h5>
                                </div>
                                <div class="card-body">
                                    <div class="benchmark-card">
                                        <h6><i class="fas fa-tachometer-alt"></i> Margem de Lucro Ideal</h6>
                                        <div class="progress">
                                            <div class="progress-bar { 'bg-success' if resultados.get('margem_lucro', 0) >= 30 else 'bg-warning' if resultados.get('margem_lucro', 0) >= 15 else 'bg-danger' }" 
                                                 style="width: {min(resultados.get('margem_lucro', 0), 100)}%">
                                                {resultados.get('margem_lucro', 0):.1f}% (Meta: 30%)
                                            </div>
                                        </div>
                                    </div>
                                    <div class="benchmark-card">
                                        <h6><i class="fas fa-chart-line"></i> ROI Mínimo Aceitável</h6>
                                        <div class="progress">
                                            <div class="progress-bar { 'bg-success' if resultados.get('roi_percentual', 0) >= 100 else 'bg-warning' if resultados.get('roi_percentual', 0) >= 50 else 'bg-danger' }" 
                                                 style="width: {min(resultados.get('roi_percentual', 0) / 2, 100)}%">
                                                {resultados.get('roi_percentual', 0):.1f}% (Meta: 100%)
                                            </div>
                                        </div>
                                    </div>
                                    <div class="benchmark-card">
                                        <h6><i class="fas fa-clock"></i> Payback Máximo Recomendado</h6>
                                        <div class="progress">
                                            <div class="progress-bar { 'bg-success' if resultados.get('payback_meses', 0) <= 24 else 'bg-warning' if resultados.get('payback_meses', 0) <= 36 else 'bg-danger' }" 
                                                 style="width: {max(0, 100 - (resultados.get('payback_meses', 0) / 36 * 100))}%">
                                                {resultados.get('payback_meses', 0):.1f} meses (Máx: 36 meses)
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-warning text-white">
                                    <h5 class="mb-0"><i class="fas fa-lightbulb"></i> Recomendações e Plano de Ação</h5>
                                </div>
                                <div class="card-body">
                                    {recomendacoes_html}
                                    {plano_acao_html}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-chart-pie"></i> Distribuição</h5>
                                </div>
                                <div class="card-body">
                                    <div class="chart-container">
                                        <canvas id="graficoResultados"></canvas>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-12">
                            {atividades_html}
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-12 text-center">
                            <a href="/simulacao" class="btn btn-primary btn-lg me-3">
                                <i class="fas fa-plus"></i> Nova Simulação
                            </a>
                            <a href="/dashboard" class="btn btn-secondary btn-lg">
                                <i class="fas fa-chart-line"></i> Ver Dashboard
                            </a>
                            <button onclick="window.print()" class="btn btn-info btn-lg ms-3">
                                <i class="fas fa-print"></i> Imprimir Relatório
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Gráfico de pizza
        const ctx = document.getElementById('graficoResultados').getContext('2d');
        new Chart(ctx, {{
            type: 'pie',
            data: {{
                labels: ['Investimento', 'Receita Mensal', 'Custo Mensal', 'Lucro Mensal'],
                datasets: [{{
                    data: [
                        {resultados.get('investimento_inicial', 0)},
                        {resultados.get('receita_mensal_atividades', 0)},
                        {resultados.get('custo_mensal_total', 0)},
                        {resultados.get('lucro_mensal', 0)}
                    ],
                    backgroundColor: [
                        '#FF6B8B',
                        '#4ECDC4',
                        '#45B7D1',
                        '#FF9F1C'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
    }});
    </script>
    '''
    
    return get_base_html(f"Resultados: {nome_simulacao}", content)

@app.route('/dashboard')
def dashboard():
    """Dashboard com histórico de simulações"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, nome, data_criacao, total_participantes, investimento_total,
               receita_mensal_total, lucro_mensal_total, margem_lucro,
               roi_percentual, payback_meses
        FROM simulacoes 
        ORDER BY data_criacao DESC 
        LIMIT 20
        ''')
        
        simulacoes = cursor.fetchall()
        
        # Estatísticas
        cursor.execute('''
        SELECT COUNT(*) as total, 
               AVG(margem_lucro) as avg_margem,
               AVG(roi_percentual) as avg_roi,
               SUM(investimento_total) as total_investido,
               SUM(receita_mensal_total) as total_receita
        FROM simulacoes
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        # HTML para tabela
        tabela_html = ""
        if simulacoes:
            tabela_html = '''
            <div class="card mb-4">
                <div class="card-header bg-secondary text-white">
                    <h5 class="mb-0"><i class="fas fa-history"></i> Histórico de Simulações</h5>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0 table-fixed">
                            <thead class="table-dark">
                                <tr>
                                    <th class="col-nome">Nome</th>
                                    <th class="col-data">Data</th>
                                    <th class="col-participantes text-center">Part.</th>
                                    <th class="col-investimento text-end">Investimento</th>
                                    <th class="col-receita text-end">Receita/Mês</th>
                                    <th class="col-lucro text-end">Lucro/Mês</th>
                                    <th class="col-margem text-center">Margem</th>
                                    <th class="col-roi text-center">ROI</th>
                                    <th class="col-payback text-center">Payback</th>
                                    <th class="col-acoes text-center">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
            '''
            
            for sim in simulacoes:
                tabela_html += f'''
                                <tr>
                                    <td class="col-nome">
                                        <span class="text-truncate-cell" title="{sim['nome']}">
                                            {sim['nome']}
                                        </span>
                                    </td>
                                    <td class="col-data">{sim['data_criacao'][:10]}</td>
                                    <td class="col-participantes text-center">{sim['total_participantes']}</td>
                                    <td class="col-investimento text-end">R$ {sim['investimento_total']:,.0f}</td>
                                    <td class="col-receita text-end text-success">R$ {sim['receita_mensal_total']:,.0f}</td>
                                    <td class="col-lucro text-end { 'text-success' if sim['lucro_mensal_total'] > 0 else 'text-danger' }">
                                        R$ {sim['lucro_mensal_total']:,.0f}
                                    </td>
                                    <td class="col-margem text-center">
                                        <span class="badge badge-fixed { 'bg-success' if sim['margem_lucro'] >= 25 else 'bg-warning' if sim['margem_lucro'] >= 15 else 'bg-danger' }">
                                            {sim['margem_lucro']:.1f}%
                                        </span>
                                    </td>
                                    <td class="col-roi text-center">
                                        <span class="badge badge-fixed { 'bg-success' if sim['roi_percentual'] >= 100 else 'bg-warning' if sim['roi_percentual'] >= 50 else 'bg-danger' }">
                                            {sim['roi_percentual']:.1f}%
                                        </span>
                                    </td>
                                    <td class="col-payback text-center">
                                        <span class="badge badge-fixed { 'bg-success' if sim['payback_meses'] <= 24 else 'bg-warning' if sim['payback_meses'] <= 36 else 'bg-danger' }">
                                            {sim['payback_meses']:.1f} m
                                        </span>
                                    </td>
                                    <td class="col-acoes text-center">
                                        <div class="btn-group btn-group-sm" role="group">
                                            <a href="/simulacao/{sim['id']}" class="btn btn-warning" title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            <a href="/resultado_com_ia" class="btn btn-info" title="Ver Resultados" onclick="sessionStorage.setItem('simulacao_id', {sim['id']})">
                                                <i class="fas fa-eye"></i>
                                            </a>
                                            <button class="btn btn-danger" title="Excluir" onclick="excluirSimulacao({sim['id']})">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                '''
            
            tabela_html += '''
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            '''
        else:
            tabela_html = '''
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> Nenhuma simulação encontrada. 
                <a href="/simulacao" class="alert-link">Crie sua primeira simulação</a>.
            </div>
            '''
        
        content = f'''
        <div class="row">
            <div class="col-lg-12">
                <div class="card shadow mb-4">
                    <div class="card-header bg-primary text-white">
                        <h3 class="mb-0"><i class="fas fa-chart-line"></i> Dashboard - Histórico de Simulações</h3>
                    </div>
                    <div class="card-body">
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="card bg-success text-white">
                                    <div class="card-body text-center">
                                        <h2><i class="fas fa-calculator"></i></h2>
                                        <h4>{stats['total']}</h4>
                                        <p class="mb-0">Simulações</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-info text-white">
                                    <div class="card-body text-center">
                                        <h2><i class="fas fa-percentage"></i></h2>
                                        <h4>{stats['avg_margem']:.1f}%</h4>
                                        <p class="mb-0">Margem Média</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-warning text-white">
                                    <div class="card-body text-center">
                                        <h2><i class="fas fa-chart-line"></i></h2>
                                        <h4>{stats['avg_roi']:.1f}%</h4>
                                        <p class="mb-0">ROI Médio</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-danger text-white">
                                    <div class="card-body text-center">
                                        <h2><i class="fas fa-money-bill-wave"></i></h2>
                                        <h4>R$ {stats['total_investido']:,.0f}</h4>
                                        <p class="mb-0">Total Investido</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        {tabela_html}
                        
                        <div class="row mt-4">
                            <div class="col-12">
                                <div class="card">
                                    <div class="card-header bg-secondary text-white">
                                        <h5 class="mb-0"><i class="fas fa-chart-bar"></i> Análise Comparativa</h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="chart-container">
                                            <canvas id="dashboardChart"></canvas>
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
            // Gráfico do dashboard
            const ctx = document.getElementById('dashboardChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: ['Margem Média', 'ROI Médio', 'Payback Médio'],
                    datasets: [{{
                        label: 'Seu Desempenho',
                        data: [{stats['avg_margem']}, {stats['avg_roi']}, 0],
                        backgroundColor: '#4361ee'
                    }}, {{
                        label: 'Benchmarks',
                        data: [30, 100, 24],
                        backgroundColor: '#FF9F1C'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
            
            // Função para excluir simulação
            window.excluirSimulacao = function(id) {{
                if (confirm('Tem certeza que deseja excluir esta simulação?')) {{
                    fetch('/api/excluir_simulacao/' + id, {{
                        method: 'DELETE'
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            location.reload();
                        }} else {{
                            alert('Erro ao excluir simulação: ' + (data.error || 'Erro desconhecido'));
                        }}
                    }})
                    .catch(error => {{
                        alert('Erro: ' + error.message);
                    }});
                }}
            }};
        }});
        </script>
        '''
        
        return get_base_html("Dashboard", content)
        
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return redirect('/')

@app.route('/analise_ia')
def analise_ia():
    """Página de análise de IA avançada"""
    content = '''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card shadow">
                <div class="card-header bg-dark text-white">
                    <h3 class="mb-0"><i class="fas fa-brain"></i> Análise Avançada com IA</h3>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0"><i class="fas fa-robot"></i> Funcionalidades da IA</h5>
                                </div>
                                <div class="card-body">
                                    <ul class="list-group list-group-flush">
                                        <li class="list-group-item">
                                            <i class="fas fa-check-circle text-success me-2"></i>
                                            <strong>Análise de Rentabilidade:</strong> Avaliação detalhada dos indicadores financeiros
                                        </li>
                                        <li class="list-group-item">
                                            <i class="fas fa-check-circle text-success me-2"></i>
                                            <strong>Detecção de Riscos:</strong> Identificação de pontos críticos no plano
                                        </li>
                                        <li class="list-group-item">
                                            <i class="fas fa-check-circle text-success me-2"></i>
                                            <strong>Otimização de Custos:</strong> Sugestões para redução de despesas
                                        </li>
                                        <li class="list-group-item">
                                            <i class="fas fa-check-circle text-success me-2"></i>
                                            <strong>Benchmarking:</strong> Comparação com padrões do setor
                                        </li>
                                        <li class="list-group-item">
                                            <i class="fas fa-check-circle text-success me-2"></i>
                                            <strong>Plano de Ação Personalizado:</strong> Passos concretos para implementação
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-chart-line"></i> Como Funciona</h5>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <h6><i class="fas fa-1 text-primary"></i> Coleta de Dados</h6>
                                        <p class="small">Você insere informações sobre atividades, custos e receitas.</p>
                                    </div>
                                    <div class="mb-3">
                                        <h6><i class="fas fa-2 text-primary"></i> Processamento</h6>
                                        <p class="small">O sistema calcula indicadores financeiros automaticamente.</p>
                                    </div>
                                    <div class="mb-3">
                                        <h6><i class="fas fa-3 text-primary"></i> Análise IA</h6>
                                        <p class="small">Inteligência Artificial analisa os dados e gera recomendações.</p>
                                    </div>
                                    <div class="mb-3">
                                        <h6><i class="fas fa-4 text-primary"></i> Relatório</h6>
                                        <p class="small">Você recebe um relatório detalhado com plano de ação.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-warning text-white">
                                    <h5 class="mb-0"><i class="fas fa-lightbulb"></i> Benefícios da Análise com IA</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-4">
                                            <div class="text-center p-3">
                                                <i class="fas fa-clock fa-3x text-primary mb-3"></i>
                                                <h6>Economia de Tempo</h6>
                                                <p class="small">Análise em segundos que levaria horas manualmente</p>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="text-center p-3">
                                                <i class="fas fa-shield-alt fa-3x text-success mb-3"></i>
                                                <h6>Redução de Riscos</h6>
                                                <p class="small">Identificação antecipada de problemas</p>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="text-center p-3">
                                                <i class="fas fa-chart-line fa-3x text-danger mb-3"></i>
                                                <h6>Melhores Resultados</h6>
                                                <p class="small">Otimização da rentabilidade do projeto</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-12 text-center">
                            <a href="/simulacao" class="btn btn-primary btn-lg me-3">
                                <i class="fas fa-rocket"></i> Começar Análise
                            </a>
                            <a href="/dashboard" class="btn btn-secondary btn-lg">
                                <i class="fas fa-history"></i> Ver Histórico
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_base_html("Análise com IA", content)

if __name__ == '__main__':
    app.run(debug=True, port=5000)