from flask import Flask, render_template, request, jsonify, session, redirect
from datetime import datetime
import json
import math
import os
import sqlite3

app = Flask(__name__)

# Configuração para produção
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'business_plan_escolar_prod_2024_seguro')
app.config['TEMPLATES_AUTO_RELOAD'] = os.environ.get('FLASK_ENV') == 'development'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # Cache de 1 ano

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'data', 'database.db')

def init_db():
    """Inicializa o banco de dados SQLite"""
    try:
        # Garante que a pasta data existe
        data_dir = os.path.join(basedir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Cria a tabela de simulações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data_criacao TEXT,
            alunos_atuais INTEGER,
            mensalidade_media REAL,
            aumento_esperado REAL,
            novos_alunos INTEGER,
            custo_infraestrutura REAL,
            custo_professores REAL,
            custo_material REAL,
            custo_marketing REAL,
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

def salvar_simulacao(dados_entrada, resultados):
    """Salva uma simulação no banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO simulacoes (
            nome, data_criacao, alunos_atuais, mensalidade_media,
            aumento_esperado, novos_alunos, custo_infraestrutura,
            custo_professores, custo_material, custo_marketing,
            receita_mensal_atual, receita_projetada, investimento_total,
            retorno_mensal, payback, roi, dados
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"Simulação {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            dados_entrada.get('alunos_atuais', 0),
            dados_entrada.get('mensalidade_media', 0),
            dados_entrada.get('aumento_esperado', 0),
            resultados.get('novos_alunos', 0),
            resultados.get('custo_infraestrutura', 0),
            resultados.get('custo_professores', 0),
            resultados.get('custo_material', 0),
            resultados.get('custo_marketing', 0),
            resultados.get('receita_atual', 0),
            resultados.get('receita_projetada', 0),
            resultados.get('investimento_total', 0),
            resultados.get('retorno_mensal', 0),
            resultados.get('payback_meses', 0),
            resultados.get('roi_percentual', 0),
            json.dumps({'entrada': dados_entrada, 'resultados': resultados})
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

# Funções de cálculo
def calcular_projecao(dados):
    """Calcula todas as projeções baseadas nos dados inseridos"""
    
    alunos_atuais = dados.get('alunos_atuais', 0)
    mensalidade = dados.get('mensalidade_media', 0)
    aumento_percentual = dados.get('aumento_esperado', 0) / 100
    
    # Cálculo de novos alunos
    novos_alunos = int(alunos_atuais * aumento_percentual)
    
    # Receitas
    receita_atual = alunos_atuais * mensalidade
    receita_projetada = (alunos_atuais + novos_alunos) * mensalidade
    
    # Custos das atividades extracurriculares
    num_atividades = dados.get('num_atividades', 3)
    custo_professor_por_hora = dados.get('custo_professor_por_hora', 50)
    horas_semanais = dados.get('horas_semanais', 10)
    semanas_mes = 4.3
    
    custo_professores = num_atividades * custo_professor_por_hora * horas_semanais * semanas_mes
    
    # Outros custos
    custo_infra = dados.get('custo_infraestrutura', 1000)
    custo_material = dados.get('custo_material', 500)
    custo_marketing = dados.get('custo_marketing', 800)
    
    investimento_total = custo_infra + custo_professores + custo_material + custo_marketing
    
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
        'custo_professores': custo_professores,
        'custo_infraestrutura': custo_infra,
        'custo_material': custo_material,
        'custo_marketing': custo_marketing
    }

# Funções para criar templates HTML inline
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
        .hero-section {{
            background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
        }}
        footer {{
            background-color: #2c3e50;
            color: white;
            padding: 20px 0;
            margin-top: 40px;
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
            <p>Sistema de Business Plan para Escolas - Análise de expansão com aulas extracurriculares</p>
            <p class="mb-0">© 2024 - Desenvolvido com Python, Flask e SQLite</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

# Rotas da aplicação com templates inline
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
                    Ferramenta para análise de custo-benefício na implementação de aulas extracurriculares
                    visando aumentar em <strong>30% a 50%</strong> o número de matrículas.
                </p>
                <div class="row mt-5">
                    <div class="col-md-4">
                        <div class="card mb-4 border-primary">
                            <div class="card-body">
                                <i class="fas fa-calculator fa-3x text-primary mb-3"></i>
                                <h4>Análise Financeira</h4>
                                <p>Cálculos detalhados de investimento e retorno</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card mb-4 border-success">
                            <div class="card-body">
                                <i class="fas fa-chart-bar fa-3x text-success mb-3"></i>
                                <h4>Projeções</h4>
                                <p>Simulações de crescimento de 30% a 50%</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card mb-4 border-info">
                            <div class="card-body">
                                <i class="fas fa-file-alt fa-3x text-info mb-3"></i>
                                <h4>Relatórios</h4>
                                <p>Dashboard completo com indicadores</p>
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
                    <h4><i class="fas fa-bullseye"></i> Objetivo do Sistema</h4>
                </div>
                <div class="card-body">
                    <ul class="list-group list-group-flush">
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            Aumentar matrículas em 30-50% com aulas extracurriculares
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            Calcular custo-benefício da expansão
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            Analisar receitas e gastos projetados
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            Identificar ponto de equilíbrio (break-even)
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-check-circle text-success"></i>
                            Calcular ROI (Retorno sobre Investimento)
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h4><i class="fas fa-graduation-cap"></i> Benefícios para a Escola</h4>
                </div>
                <div class="card-body">
                    <div class="alert alert-success">
                        <strong>Diferenciação no mercado:</strong> Atividades extracurriculares atraem novos alunos
                    </div>
                    <div class="alert alert-info">
                        <strong>Aumento de receita:</strong> Mais matrículas = maior faturamento
                    </div>
                    <div class="alert alert-warning">
                        <strong>Melhor utilização da infraestrutura:</strong> Espaços ociosos são aproveitados
                    </div>
                    <div class="alert alert-primary">
                        <strong>Fidelização:</strong> Alunos permanecem mais tempo na escola
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Business Plan Escolar - Início", content)

@app.route('/simulacao')
def simulacao():
    content = '''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-calculator"></i> Simulação de Business Plan</h3>
                    <p class="mb-0">Preencha os dados para análise de expansão com aulas extracurriculares</p>
                </div>
                <div class="card-body">
                    <form id="simulacaoForm">
                        <div class="row">
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2">Dados Atuais da Escola</h4>
                                
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
                                    <label class="form-label">Receita mensal atual (R$):</label>
                                    <div class="input-group">
                                        <span class="input-group-text">R$</span>
                                        <input type="text" class="form-control" id="receita_atual" 
                                               readonly value="160,000">
                                    </div>
                                    <div class="form-text">Calculado automaticamente</div>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2">Projeção de Crescimento</h4>
                                
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
                                
                                <div class="mb-3">
                                    <label class="form-label">Novos alunos projetados:</label>
                                    <div class="input-group">
                                        <input type="number" class="form-control" id="novos_alunos" 
                                               readonly value="80">
                                        <span class="input-group-text">alunos</span>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Total projetado de alunos:</label>
                                    <div class="input-group">
                                        <input type="number" class="form-control" id="total_projetado" 
                                               readonly value="280">
                                        <span class="input-group-text">alunos</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mt-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2">Custos das Atividades Extracurriculares</h4>
                            </div>
                            
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Número de atividades:</label>
                                    <select class="form-select" id="num_atividades">
                                        <option value="2">2 atividades</option>
                                        <option value="3" selected>3 atividades</option>
                                        <option value="4">4 atividades</option>
                                        <option value="5">5 atividades</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Custo professor/hora (R$):</label>
                                    <input type="number" class="form-control" id="custo_professor_por_hora" 
                                           value="50" min="30" step="10">
                                </div>
                            </div>
                            
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Horas/semana por atividade:</label>
                                    <input type="number" class="form-control" id="horas_semanais" 
                                           value="10" min="5" step="1">
                                </div>
                            </div>
                            
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Semanas por mês:</label>
                                    <input type="number" class="form-control" id="semanas_mes" 
                                           value="4.3" min="4" max="4.5" step="0.1" readonly>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mt-3">
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Custo infraestrutura (R$):</label>
                                    <input type="number" class="form-control" id="custo_infraestrutura" 
                                           value="1000" min="0" step="100">
                                    <div class="form-text">Adaptações, equipamentos</div>
                                </div>
                            </div>
                            
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Custo material (R$):</label>
                                    <input type="number" class="form-control" id="custo_material" 
                                           value="500" min="0" step="50">
                                    <div class="form-text">Materiais didáticos</div>
                                </div>
                            </div>
                            
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Custo marketing (R$):</label>
                                    <input type="number" class="form-control" id="custo_marketing" 
                                           value="800" min="0" step="100">
                                    <div class="form-text">Divulgação das novas atividades</div>
                                </div>
                            </div>
                            
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Outros custos (R$):</label>
                                    <input type="number" class="form-control" id="outros_custos" 
                                           value="200" min="0" step="50">
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mt-4">
                            <div class="col-12 text-center">
                                <button type="button" class="btn btn-primary btn-lg" 
                                        onclick="calcularSimulacao()" id="btnCalcular">
                                    <i class="fas fa-calculator"></i> Calcular Projeção
                                </button>
                                <button type="reset" class="btn btn-secondary btn-lg ms-2">
                                    <i class="fas fa-redo"></i> Limpar
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
    document.addEventListener('DOMContentLoaded', function() {
        // Atualizar valores iniciais
        atualizarCalculosParciais();
        
        // Configurar eventos
        document.getElementById('alunos_atuais').addEventListener('input', atualizarCalculosParciais);
        document.getElementById('mensalidade_media').addEventListener('input', atualizarCalculosParciais);
        document.getElementById('aumento_esperado_range').addEventListener('input', function() {
            document.getElementById('aumento_esperado_value').textContent = this.value + '%';
            document.getElementById('aumento_esperado').value = this.value;
            atualizarCalculosParciais();
        });
    });

    function atualizarCalculosParciais() {
        const alunos = parseInt(document.getElementById('alunos_atuais').value) || 0;
        const mensalidade = parseFloat(document.getElementById('mensalidade_media').value) || 0;
        const aumento = parseInt(document.getElementById('aumento_esperado').value) || 0;
        
        // Receita atual
        const receitaAtual = alunos * mensalidade;
        document.getElementById('receita_atual').value = receitaAtual.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        // Novos alunos
        const novosAlunos = Math.round(alunos * (aumento / 100));
        document.getElementById('novos_alunos').value = novosAlunos;
        
        // Total projetado
        document.getElementById('total_projetado').value = alunos + novosAlunos;
    }

    async function calcularSimulacao() {
        const btn = document.getElementById('btnCalcular');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculando...';
        btn.disabled = true;
        
        try {
            const dados = {
                alunos_atuais: parseInt(document.getElementById('alunos_atuais').value),
                mensalidade_media: parseFloat(document.getElementById('mensalidade_media').value),
                aumento_esperado: parseInt(document.getElementById('aumento_esperado').value),
                num_atividades: parseInt(document.getElementById('num_atividades').value),
                custo_professor_por_hora: parseFloat(document.getElementById('custo_professor_por_hora').value),
                horas_semanais: parseInt(document.getElementById('horas_semanais').value),
                custo_infraestrutura: parseFloat(document.getElementById('custo_infraestrutura').value),
                custo_material: parseFloat(document.getElementById('custo_material').value),
                custo_marketing: parseFloat(document.getElementById('custo_marketing').value)
            };
            
            const response = await fetch('/calcular', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dados)
            });
            
            const resultados = await response.json();
            
            if (response.ok) {
                mostrarResultados(resultados);
                // Redirecionar para resultado após cálculo
                setTimeout(() => {
                    window.location.href = '/resultado';
                }, 1500);
            } else {
                alert('Erro: ' + (resultados.error || 'Desconhecido'));
            }
        } catch (error) {
            alert('Erro ao calcular: ' + error.message);
        } finally {
            btn.innerHTML = '<i class="fas fa-calculator"></i> Calcular Projeção';
            btn.disabled = false;
        }
    }

    function mostrarResultados(resultados) {
        const divResultado = document.getElementById('resultado');
        
        let html = `
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <h4 class="mb-0"><i class="fas fa-chart-line"></i> Resultados da Simulação</h4>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h5>Resumo Financeiro</h5>
                            <table class="table table-bordered">
                                <tr>
                                    <th>Investimento Total Inicial:</th>
                                    <td class="text-danger">R$ ${resultados.investimento_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                                </tr>
                                <tr>
                                    <th>Retorno Mensal Adicional:</th>
                                    <td class="text-success">R$ ${resultados.retorno_mensal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                                </tr>
                                <tr>
                                    <th>Payback (meses):</th>
                                    <td>${resultados.payback_meses.toFixed(1)} meses</td>
                                </tr>
                                <tr>
                                    <th>ROI Anual (%):</th>
                                    <td class="text-success">${resultados.roi_percentual.toFixed(1)}%</td>
                                </tr>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h5>Projeção de Matrículas</h5>
                            <table class="table table-bordered">
                                <tr>
                                    <th>Alunos Atuais:</th>
                                    <td>${parseInt(document.getElementById('alunos_atuais').value)}</td>
                                </tr>
                                <tr>
                                    <th>Novos Alunos:</th>
                                    <td class="text-success">+${resultados.novos_alunos}</td>
                                </tr>
                                <tr>
                                    <th>Total Projetado:</th>
                                    <td><strong>${parseInt(document.getElementById('alunos_atuais').value) + resultados.novos_alunos}</strong></td>
                                </tr>
                                <tr>
                                    <th>Aumento:</th>
                                    <td>${document.getElementById('aumento_esperado').value}%</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    
                    <div class="alert alert-info mt-3">
                        <i class="fas fa-info-circle"></i> Redirecionando para análise detalhada...
                    </div>
                </div>
            </div>
        `;
        
        divResultado.innerHTML = html;
        divResultado.style.display = 'block';
        
        // Rolar até os resultados
        divResultado.scrollIntoView({ behavior: 'smooth' });
    }
    </script>
    '''
    return get_base_html("Simulação - Business Plan", content)

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        dados = request.json
        
        # Validação básica
        if not dados.get('alunos_atuais') or dados['alunos_atuais'] <= 0:
            return jsonify({'error': 'Número de alunos atual inválido'}), 400
            
        if dados.get('aumento_esperado') < 30 or dados.get('aumento_esperado') > 50:
            return jsonify({'warning': 'Aumento esperado deve estar entre 30% e 50%'})
        
        # Realizar cálculos
        resultados = calcular_projecao(dados)
        
        # Salvar na sessão
        session['ultima_simulacao'] = {
            'dados_entrada': dados,
            'resultados': resultados
        }
        
        # Salvar no banco de dados
        salvar_simulacao(dados, resultados)
        
        return jsonify(resultados)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/resultado')
def resultado():
    if 'ultima_simulacao' not in session:
        return index()
    
    dados = session['ultima_simulacao']
    
    # Criar gráficos em JavaScript
    chart_js = f'''
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Gráfico de Receitas
        const ctx1 = document.getElementById('chartReceitas').getContext('2d');
        new Chart(ctx1, {{
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
        
        // Gráfico de Custos
        const ctx2 = document.getElementById('chartCustos').getContext('2d');
        new Chart(ctx2, {{
            type: 'doughnut',
            data: {{
                labels: ['Infraestrutura', 'Professores', 'Material', 'Marketing'],
                datasets: [{{
                    data: [
                        {dados['resultados']['custo_infraestrutura']},
                        {dados['resultados']['custo_professores']},
                        {dados['resultados']['custo_material']},
                        {dados['resultados']['custo_marketing']}
                    ],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)'
                    ],
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
                                const value = context.parsed;
                                return context.label + ': R$ ' + value.toLocaleString('pt-BR');
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
                        <h3 class="mb-0"><i class="fas fa-chart-pie"></i> Análise Detalhada da Projeção</h3>
                        <span class="badge bg-light text-primary fs-6">Aumento de {dados['dados_entrada']['aumento_esperado']}%</span>
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
                                    <h5 class="mb-0"><i class="fas fa-user-plus"></i> Crescimento de Alunos</h5>
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
                                    <h5 class="mb-0"><i class="fas fa-lightbulb"></i> Recomendações Estratégicas</h5>
                                </div>
                                <div class="card-body">
                                    <div class="alert {'alert-success' if dados['resultados']['roi_percentual'] > 100 else 'alert-warning'}">
                                        <h5><i class="fas {'fa-check-circle' if dados['resultados']['roi_percentual'] > 100 else 'fa-exclamation-triangle'}"></i> 
                                        Viabilidade Financeira: {'ALTA' if dados['resultados']['roi_percentual'] > 100 else 'MODERADA'}</h5>
                                        <p>O ROI de {dados['resultados']['roi_percentual']:.1f}% indica 
                                        {'um excelente retorno sobre o investimento' if dados['resultados']['roi_percentual'] > 100 else 'um retorno satisfatório sobre o investimento'}.</p>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="card mb-3">
                                                <div class="card-body">
                                                    <h6><i class="fas fa-thumbs-up text-success"></i> Pontos Fortes</h6>
                                                    <ul>
                                                        <li>Aumento significativo de matrículas ({dados['dados_entrada']['aumento_esperado']}%)</li>
                                                        <li>Receita adicional mensal: R$ {dados['resultados']['retorno_mensal']:,.2f}</li>
                                                        <li>Melhor utilização da infraestrutura existente</li>
                                                        <li>Diferenciação competitiva no mercado</li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="card mb-3">
                                                <div class="card-body">
                                                    <h6><i class="fas fa-exclamation-triangle text-warning"></i> Considerações</h6>
                                                    <ul>
                                                        <li>Necessidade de contratação de professores especializados</li>
                                                        <li>Investimento inicial necessário: R$ {dados['resultados']['investimento_total']:,.2f}</li>
                                                        <li>Tempo para retorno: {dados['resultados']['payback_meses']:.1f} meses</li>
                                                        <li>Possível necessidade de ajustes na infraestrutura</li>
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
                                        <button class="btn btn-info" onclick="window.print()">
                                            <i class="fas fa-print"></i> Imprimir Análise
                                        </button>
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
    return get_base_html("Resultados da Simulação", content)

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
            
        simulacoes.append({
            'id': s['id'],
            'nome': s['nome'],
            'data_criacao': data_criacao,
            'alunos_atuais': s['alunos_atuais'],
            'mensalidade_media': s['mensalidade_media'],
            'aumento_esperado': s['aumento_esperado'],
            'novos_alunos': s['novos_alunos'],
            'custo_infraestrutura': s['custo_infraestrutura'],
            'custo_professores': s['custo_professores'],
            'custo_material': s['custo_material'],
            'custo_marketing': s['custo_marketing'],
            'receita_mensal_atual': s['receita_mensal_atual'],
            'receita_projetada': s['receita_projetada'],
            'investimento_total': s['investimento_total'],
            'retorno_mensal': s['retorno_mensal'],
            'payback': s['payback'],
            'roi': s['roi']
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
        tabela_html += f'''
        <tr>
            <td>{s['data_criacao'].strftime('%d/%m/%Y')}</td>
            <td>{s['nome']}</td>
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
            <td colspan="9" class="text-center py-5">
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
                                    <h5 class="mb-0"><i class="fas fa-history"></i> Histórico de Simulações</h5>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-hover">
                                            <thead class="table-light">
                                                <tr>
                                                    <th>Data</th>
                                                    <th>Nome</th>
                                                    <th>Alunos Atuais</th>
                                                    <th>Novos Alunos</th>
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
                                    <h5 class="mb-0"><i class="fas fa-bullseye"></i> Metas de Expansão</h5>
                                </div>
                                <div class="card-body">
                                    <div class="alert alert-success">
                                        <h5><i class="fas fa-trophy"></i> Meta Principal</h5>
                                        <p>Aumentar matrículas em <strong>30% a 50%</strong> através de aulas extracurriculares</p>
                                    </div>
                                    
                                    <div class="alert alert-info">
                                        <h5><i class="fas fa-check-circle"></i> KPIs Recomendados</h5>
                                        <ul class="mb-0">
                                            <li>ROI mínimo desejado: 100%+</li>
                                            <li>Payback máximo: 18 meses</li>
                                            <li>Taxa de adesão às atividades: 70%+</li>
                                            <li>Satisfação dos pais: 90%+</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-chart-line"></i> Estatísticas</h5>
                                </div>
                                <div class="card-body">
                                    <p><strong>Total de simulações realizadas:</strong> {total_simulacoes}</p>
                                    <p><strong>Aumento médio projetado:</strong> {media_aumento:.1f}%</p>
                                    <p><strong>ROI médio:</strong> {media_roi:.1f}%</p>
                                    <p><strong>Payback médio:</strong> {media_payback:.1f} meses</p>
                                    
                                    <div class="text-center mt-3">
                                        <a href="/simulacao" class="btn btn-primary">
                                            <i class="fas fa-plus-circle"></i> Nova Simulação
                                        </a>
                                        <a href="/" class="btn btn-secondary ms-2">
                                            <i class="fas fa-home"></i> Página Inicial
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
    '''
    return get_base_html("Dashboard - Business Plan", content)

@app.route('/simulacao/<int:id>')
def ver_simulacao(id):
    simulacao_db = buscar_simulacao_por_id(id)
    if simulacao_db:
        try:
            dados_json = json.loads(simulacao_db['dados'])
        except:
            dados_json = {'entrada': {}, 'resultados': {}}
        
        # Salvar na sessão para a rota /resultado usar
        session['ultima_simulacao'] = dados_json
        return redirect('/resultado')
    return index()

@app.route('/api/simulacoes')
def api_simulacoes():
    simulacoes_db = buscar_simulacoes()
    dados = []
    for s in simulacoes_db:
        dados.append({
            'id': s['id'],
            'nome': s['nome'],
            'data': s['data_criacao'][:10] if s['data_criacao'] else '',
            'alunos_atuais': s['alunos_atuais'],
            'novos_alunos': s['novos_alunos'],
            'aumento': s['aumento_esperado'],
            'investimento': s['investimento_total'],
            'roi': s['roi'],
            'payback': s['payback']
        })
    return jsonify(dados)

# Rota de saúde para monitoramento
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'service': 'Business Plan Escolar',
        'version': '1.0.0',
        'database': 'active',
        'simulations_count': len(buscar_simulacoes())
    })

# Página de informações
@app.route('/info')
def info():
    simulacoes_count = len(buscar_simulacoes())
    
    content = f'''
    <div class="row">
        <div class="col-lg-8 mx-auto">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-info-circle"></i> Informações do Sistema</h3>
                </div>
                <div class="card-body">
                    <h4>Sistema de Business Plan Escolar</h4>
                    <p><strong>Versão:</strong> 1.0.0</p>
                    <p><strong>Status:</strong> Online e operacional</p>
                    <p><strong>Última atualização:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p><strong>Descrição:</strong> Sistema para análise de custo-benefício na implementação de aulas extracurriculares, visando aumentar em 30-50% o número de matrículas.</p>
                    
                    <h5 class="mt-4">Estatísticas do Sistema:</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-body">
                                    <h6>Simulações realizadas:</h6>
                                    <h3>{simulacoes_count}</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-body">
                                    <h6>Status do banco:</h6>
                                    <h3 class="text-success">Ativo</h3>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <h5 class="mt-4">Funcionalidades:</h5>
                    <ul>
                        <li>Simulação financeira completa</li>
                        <li>Cálculo de ROI e Payback</li>
                        <li>Dashboard com histórico</li>
                        <li>Relatórios detalhados</li>
                        <li>Acesso multi-dispositivo</li>
                        <li>Gráficos interativos</li>
                    </ul>
                    
                    <h5 class="mt-4">Tecnologias utilizadas:</h5>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="alert alert-info">
                                <strong>Backend:</strong> Python + Flask
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="alert alert-success">
                                <strong>Frontend:</strong> Bootstrap 5 + Chart.js
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="alert alert-warning">
                                <strong>Banco de Dados:</strong> SQLite
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
                        <a href="/health" class="btn btn-info ms-2">
                            <i class="fas fa-heartbeat"></i> Verificar Saúde
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Informações do Sistema", content)

# Tratamento de erros simplificado
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

# Rota para limpar sessões (útil para desenvolvimento)
@app.route('/limpar-sessoes')
def limpar_sessoes():
    session.clear()
    return '''
    <div class="alert alert-success">
        <h4>Sessões limpas com sucesso!</h4>
        <a href="/" class="btn btn-primary">Voltar ao sistema</a>
    </div>
    '''

if __name__ == '__main__':
    # Inicializar banco de dados
    if init_db():
        print("=" * 60)
        print("🚀 SISTEMA DE BUSINESS PLAN ESCOLAR")
        print("=" * 60)
        
        # Configurações para produção/desenvolvimento
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') != 'production'
        
        if debug:
            print("🔧 Modo: Desenvolvimento")
            print("🌐 Acesse: http://localhost:{}".format(port))
            print("⚠️  Para produção, defina FLASK_ENV=production")
        else:
            print("🚀 Modo: Produção")
            print("✅ Sistema pronto para acesso remoto")
            print("🔒 HTTPS recomendado")
        
        # Informações do sistema
        print("\n📊 Informações do Sistema:")
        print("   Porta: {}".format(port))
        print("   Debug: {}".format(debug))
        print("   Banco de dados: {}".format(DATABASE))
        
        print("\n🎯 Funcionalidades ativas:")
        print("   ✅ Simulação de business plan")
        print("   ✅ Cálculos financeiros automáticos")
        print("   ✅ Dashboard com histórico")
        print("   ✅ Acesso multi-dispositivo")
        print("   ✅ API RESTful")
        
        print("\n💡 Dicas:")
        print("   - Para produção: use gunicorn")
        print("   - Configure SECRET_KEY como variável de ambiente")
        print("   - Faça backup regular do banco de dados")
        
        print("=" * 60)
        print("📢 Sistema iniciado com sucesso!")
        print("=" * 60)
        
        # Executar aplicação
        app.run(
            debug=debug, 
            port=port, 
            host='0.0.0.0',  # Importante: permite acesso externo
            threaded=True  # Melhor performance para múltiplas requisições
        )
    else:
        print("❌ Não foi possível inicializar o sistema.")
        print("Verifique as permissões da pasta 'data'.")