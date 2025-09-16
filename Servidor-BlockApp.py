from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import json
import os
import ipaddress
from datetime import datetime

ARQUIVO_LISTA = "palavras.json"
ARQUIVO_LOGS = "logs.json"

# ==============================
# Carregamento inicial
# ==============================
if os.path.exists(ARQUIVO_LISTA):
    with open(ARQUIVO_LISTA, "r", encoding="utf-8") as f:
        dados = json.load(f)
else:
    dados = {}

if os.path.exists(ARQUIVO_LOGS):
    with open(ARQUIVO_LOGS, "r", encoding="utf-8") as f:
        logs = json.load(f)
else:
    logs = []


def salvar_dados():
    for grupo in dados:
        dados[grupo]["palavras"].sort()
    with open(ARQUIVO_LISTA, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def salvar_logs():
    with open(ARQUIVO_LOGS, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


app = Flask(__name__)

# ==============================
# HTML principal
# ==============================
html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>🚫 Bloqueador de Processos</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-secondary-subtle">
<div class="container mt-4">
    <h5 class="text-center text-danger">🚫 Bloqueador de Processos</h5>
    <ul class="nav nav-tabs">
      <li class="nav-item">
        <b><a class="nav-link {% if aba == 'palavras' %}active{% endif %}" href="{{ url_for('index', grupo=grupo_atual) }}">Palavras</a></b>
      </li>
      <li class="nav-item">
        <b><a class="nav-link {% if aba == 'grupos' %}active{% endif %}" href="{{ url_for('gerenciar_grupos') }}">Grupos</a></b>
      </li>
      <li class="nav-item">
        <b><a class="nav-link {% if aba == 'logs' %}active{% endif %}" href="{{ url_for('ver_logs') }}">Logs</a></b>
      </li>
    </ul>

    {% if aba == 'palavras' %}
    <div class="card shadow-sm mt-4">
        <div class="card-body">
            <form method="get" class="mb-3">
                <label>Grupo:</label>
                <select name="grupo" onchange="this.form.submit()" class="form-select">
                    {% for g in grupos %}
                        <option value="{{g}}" {% if g==grupo_atual %}selected{% endif %}>{{g}}</option>
                    {% endfor %}
                </select>
            </form>
            {% if grupo_atual %}
            <a><b>Grupo atual: </b><span style="color: red; font-weight: bold;">{{ grupo_atual }}</span><a/>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Palavra</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
                    {% for palavra in palavras %}
                    <tr>
                        <td>{{ palavra }}</td>
                        <td><a href="{{ url_for('remover_palavra', grupo=grupo_atual, palavra=palavra) }}" class="btn btn-sm btn-danger">Remover</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <form action="{{ url_for('adicionar_palavra', grupo=grupo_atual) }}" method="post" class="mt-3 d-flex">
                <input type="text" name="palavra" class="form-control me-2" placeholder="Nova palavra" required>
                <button type="submit" class="btn btn-primary">Adicionar</button>
            </form>
            {% else %}
            <p class="text-muted">Nenhum grupo selecionado. Crie um grupo para começar.</p>
            {% endif %}
        </div>
    </div>

    {% elif aba == 'grupos' %}
    <div class="card shadow-sm mt-4">
        <div class="card-body">
            <h5>Gerenciar Grupos</h5>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Grupo</th>
                        <th>Faixas de IP</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {% for g, info in grupos_dict.items() %}
                    <tr>
                        <td>{{ g }}</td>
                        <td>{{ ", ".join(info.ips) if info.ips else "-" }}</td>
                        <td>
                            <a href="{{ url_for('editar_grupo', grupo=g) }}" class="btn btn-sm btn-warning">Editar</a>
                            <a href="{{ url_for('remover_grupo', grupo=g) }}" class="btn btn-sm btn-danger">Excluir</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <hr>
            <form action="{{ url_for('criar_grupo') }}" method="post" class="mt-3">
                <h6>Novo Grupo</h6>
                <input type="text" name="nome" class="form-control mb-2" placeholder="Nome do grupo" required>
                <button type="submit" class="btn btn-success">Criar</button>
            </form>
        </div>
    </div>

    {% elif aba == 'logs' %}
    <div class="card shadow-sm mt-4">
        <div class="card-body">
            <h5>📜 Logs de Processos Encerrados</h5>

            <!-- Filtro de data -->
            <form method="get" action="{{ url_for('ver_logs') }}" class="mb-3 d-flex">
                <input type="date" name="dia" class="form-control me-2"
                       value="{{ dia_selecionado }}">
                <button type="submit" class="btn btn-primary">Filtrar</button>
                {% if dia_selecionado %}
                    <a href="{{ url_for('ver_logs') }}" class="btn btn-secondary ms-2">Limpar</a>
                {% endif %}
            </form>

            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Hora</th>
                        <th>Computador</th>
                        <th>IP</th>
                        <th>Grupo</th>
                        <th>Processo</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs|reverse %}
                    <tr>
                        <td>{{ log.hora }}</td>
                        <td>{{ log.computador }}</td>
                        <td>{{ log.ip }}</td>
                        <td>{{ log.grupo }}</td>
                        <td><b style="color:red">{{ log.processo }}</b></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
</div>
</body>
</html>
"""

# ==============================
# Rotas principais
# ==============================
@app.route("/")
def index():
    grupos = sorted(dados.keys(), key=str.lower)
    grupo = request.args.get("grupo", "")
    if not grupo and grupos:
        grupo = grupos[0]
    return render_template_string(
        html,
        aba="palavras",
        grupos=grupos,
        grupo_atual=grupo if grupo in dados else "",
        palavras=dados.get(grupo, {}).get("palavras", []),
        grupos_dict=dados,
        logs=logs,
        dia_selecionado=""
    )


@app.route("/adicionar/<grupo>", methods=["POST"])
def adicionar_palavra(grupo):
    if grupo not in dados:
        return redirect(url_for('index'))
    palavra = request.form.get("palavra", "").strip().lower()
    if palavra and palavra not in dados[grupo]["palavras"]:
        dados[grupo]["palavras"].append(palavra)
        salvar_dados()
    return redirect(url_for('index', grupo=grupo))


@app.route("/remover/<grupo>/<palavra>")
def remover_palavra(grupo, palavra):
    if grupo in dados and palavra in dados[grupo]["palavras"]:
        dados[grupo]["palavras"].remove(palavra)
        salvar_dados()
    return redirect(url_for('index', grupo=grupo))


@app.route("/grupos")
def gerenciar_grupos():
    return render_template_string(
        html,
        aba="grupos",
        grupos_dict={g: type("obj", (object,), v) for g, v in sorted(dados.items(), key=lambda x: x[0].lower())},
        grupo_atual="",
        grupos=sorted(dados.keys(), key=str.lower),
        palavras=[],
        logs=logs,
        dia_selecionado=""
    )


@app.route("/criar_grupo", methods=["POST"])
def criar_grupo():
    nome = request.form.get("nome", "").strip()
    if nome and nome not in dados:
        dados[nome] = {"ips": [], "palavras": []}
        salvar_dados()
    return redirect(url_for('gerenciar_grupos'))


@app.route("/remover_grupo/<grupo>")
def remover_grupo(grupo):
    if grupo in dados:
        del dados[grupo]
        salvar_dados()
    return redirect(url_for('gerenciar_grupos'))


@app.route("/editar_grupo/<grupo>", methods=["GET", "POST"])
def editar_grupo(grupo):
    if grupo not in dados:
        return redirect(url_for('gerenciar_grupos'))
    if request.method == "POST":
        ips_str = request.form.get("ips", "").strip()
        ips_list = [ip.strip() for ip in ips_str.split(",") if ip.strip()]
        dados[grupo]["ips"] = ips_list
        salvar_dados()
        return redirect(url_for('gerenciar_grupos'))

    ips_str = ", ".join(dados[grupo]["ips"])
    return f"""
    <h3>Editar Grupo: {grupo}</h3>
    <form method="post">
        <label>Faixas de IP (IPinicial-IPfinal, IP/CIDR, IPúnico)</label>
        <input type="text" name="ips" value="{ips_str}" style="width:400px">
        <br><br>
        <button type="submit">Salvar</button>
    </form>
    """

# ==============================
# Detectar grupo por IP
# ==============================
def detectar_grupo(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        for grupo, info in dados.items():
            for faixa in info["ips"]:
                faixa = faixa.strip()
                if "/" in faixa:
                    try:
                        if ip_obj in ipaddress.ip_network(faixa, strict=False):
                            return grupo
                    except ValueError:
                        pass
                elif "-" in faixa:
                    try:
                        inicio_str, fim_str = faixa.split("-", 1)
                        ip_inicio = ipaddress.ip_address(inicio_str.strip())
                        ip_fim = ipaddress.ip_address(fim_str.strip())
                        if ip_inicio <= ip_obj <= ip_fim:
                            return grupo
                    except ValueError:
                        pass
                else:
                    try:
                        if ip_obj == ipaddress.ip_address(faixa):
                            return grupo
                    except ValueError:
                        pass
    except ValueError:
        pass
    return None

# ==============================
# Logs
# ==============================
@app.route("/log", methods=["POST"])
def registrar_log():
    ip = request.remote_addr
    data = request.json
    grupo = detectar_grupo(ip)

    log = {
        "hora": data.get("hora", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "computador": data.get("computador", "desconhecido"),
        "ip": ip,
        "grupo": grupo or "-",
        "processo": data.get("processo", "???")
    }
    logs.append(log)
    salvar_logs()
    return jsonify({"status": "ok"}), 200


@app.route("/logs")
def ver_logs():
    dia = request.args.get("dia", "")  # parâmetro da data
    logs_filtrados = logs

    if dia:
        logs_filtrados = [
            l for l in logs
            if l.get("hora", "").startswith(dia)
        ]

    return render_template_string(
        html,
        aba="logs",
        grupos=sorted(dados.keys(), key=str.lower),
        grupo_atual="",
        palavras=[],
        grupos_dict=dados,
        logs=logs_filtrados,
        dia_selecionado=dia
    )

# ==============================
# Endpoint para cliente buscar lista
# ==============================
@app.route("/lista")
def lista():
    ip_cliente = request.remote_addr
    grupo = detectar_grupo(ip_cliente)
    if grupo and grupo in dados:
        return jsonify(dados[grupo]["palavras"])
    return jsonify([])

# ==============================
# Main
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, threaded=True)
