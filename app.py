
from flask import Flask
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import uuid

app = Flask(__name__)

# -----------------------------
# CONEXIÓN GOOGLE SHEETS
# -----------------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

import os
import json
if os.environ.get("GOOGLE_CREDENTIALS"):
    creds_dict = json.loads(
        os.environ["GOOGLE_CREDENTIALS"]
    )
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )
else:
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        r"d:\Mardisresearch\OneDrive - mardisresearch.com\Documentos\99. Personal\ESPOL\quiz-system\sistemaquizzes-123456.json",
        scope
    )


client = gspread.authorize(creds)

# -----------------------------
# LEER ESTUDIANTES
# -----------------------------

sheet_est = client.open("Estudiantes")
worksheet_est = sheet_est.sheet1
data_est = worksheet_est.get_all_records()
df_est = pd.DataFrame(data_est)

# -----------------------------
# LEER BANCO PREGUNTAS
# -----------------------------

sheet_preg = client.open("BancoPreguntas")
worksheet_preg = sheet_preg.sheet1
data_preg = worksheet_preg.get_all_records()
df_preg = pd.DataFrame(data_preg)

# -----------------------------
# LEER QUIZ PREGUNTAS
# -----------------------------

sheet_qp = client.open("QuizPreguntas")
worksheet_qp = sheet_qp.sheet1
data_qp = worksheet_qp.get_all_records()
df_qp = pd.DataFrame(data_qp)

# -----------------------------
# LEER QUIZZES
# -----------------------------
sheet_quiz = client.open("Quizzes")
worksheet_quiz = sheet_quiz.sheet1

# -----------------------------
# LEER ASIGNACION QUIZZES
# -----------------------------
sheet_asig = client.open("AsignacionQuizzes")
worksheet_asig = sheet_asig.sheet1

# -----------------------------
# LEER RESPUESTAS
# -----------------------------
sheet_resp = client.open("Respuestas")
worksheet_resp = sheet_resp.sheet1

# -----------------------------
# RUTA PRINCIPAL
# -----------------------------

@app.route("/quiz/<quiz_id>")
def home(quiz_id):

    # -----------------------------
    # LISTA ESTUDIANTES
    # -----------------------------

    opciones = ""

    # -----------------------------
    # PARALELOS HABILITADOS
    # -----------------------------
    data_asig = worksheet_asig.get_all_records()
    df_asig = pd.DataFrame(data_asig)
    print(df_asig)
    print(df_asig.dtypes)
    print("QUIZ recibido submit:", quiz_id)
    data_asig = worksheet_asig.get_all_records()
    df_asig = pd.DataFrame(data_asig)
    print(df_asig)
    paralelos_habilitados = df_asig[
        (
            df_asig["id_quiz"]
            .astype(str)
            .str.strip()
            == str(quiz_id).strip()
        )
    ]["paralelo"].tolist()
    print("Paralelos habilitados:", paralelos_habilitados)
    df_est_filtrado = df_est[
        df_est["paralelo"]
        .astype(str)
        .str.strip()
        .isin(
            [str(p).strip() for p in paralelos_habilitados]
        )
    ]
    print(df_est_filtrado[["id_estudiante", "paralelo"]])
    
    for _, row in df_est_filtrado.iterrows():
        nombre = row["apellidos"] + " " + row["nombres"]
        id_estudiante = row["id_estudiante"]
        opciones += f"""
        <option value="{id_estudiante}">
        {nombre}
        </option>
        """

    # -----------------------------
    # PREGUNTAS DEL QUIZ
    # -----------------------------

    # -----------------------------
    # RECARGAR QUIZZES
    # -----------------------------
    data_quiz = worksheet_quiz.get_all_records()
    df_quiz = pd.DataFrame(data_quiz)

    quiz_data = df_quiz[df_quiz["id_quiz"] == quiz_id]
    if quiz_data.empty:
        return "<h1>Quiz no encontrado</h1>"
    quiz_row = quiz_data.iloc[0]
    nombre_quiz = quiz_row["nombre_quiz"]
    materia = quiz_row["materia"]

    tiempo_limite = int(quiz_row["tiempo_limite_min"])
    fecha_inicio = pd.to_datetime(quiz_row["fecha_inicio"])
    fecha_fin = pd.to_datetime(quiz_row["fecha_fin"])
    ahora = datetime.now()
    if ahora < fecha_inicio:
        return """
        <h1>Quiz no disponible</h1>
        <p>
        El quiz todavía no inicia.
        </p>
        """
    if ahora > fecha_fin:
        return """
        <h1>Quiz cerrado</h1>
        <p>
        El tiempo del quiz ya finalizó.
        </p>
        """

    preguntas_quiz = df_qp[df_qp["id_quiz"] == quiz_id]

    html_preguntas = ""

    for _, pq in preguntas_quiz.iterrows():

        id_pregunta = pq["id_pregunta"]

        pregunta_data = df_preg[df_preg["id_pregunta"] == id_pregunta]

        if not pregunta_data.empty:

            row = pregunta_data.iloc[0]

            html_preguntas += f"""
            <div class="question">

            <h3>{row['pregunta']}</h3>

            <div class="option">
            <input type="radio" name="{id_pregunta}" value="A" required>
            {row['opcion_a']}
            </div>

            <div class="option">
            <input type="radio" name="{id_pregunta}" value="B" required>
            {row['opcion_b']}
            </div>

            <div class="option">
            <input type="radio" name="{id_pregunta}" value="C" required>
            {row['opcion_c']}
            </div>

            <div class="option">
            <input type="radio" name="{id_pregunta}" value="D" required>
            {row['opcion_d']}
            </div>

            </div>
            """

    # -----------------------------
    # HTML FINAL
    # -----------------------------

    html = f"""
    
    <html>
 
    <h1>{nombre_quiz}</h1>
    <h2>{materia}</h2>

    <head>

    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>

    <script id="MathJax-script" async
    src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
    </script>

    <script>
    let tiempoRestante = {tiempo_limite * 60};
    let timer = setInterval(actualizarTimer, 1000);
    function actualizarTimer() {{
        let minutos = Math.floor(tiempoRestante / 60);
        let segundos = tiempoRestante % 60;
        segundos = segundos < 10 ? "0" + segundos : segundos;
        document.getElementById("timer").innerHTML =
            "Tiempo restante: " + minutos + ":" + segundos;
        if (tiempoRestante <= 0) {{
            clearInterval(timer);
            alert("Tiempo finalizado");
            document.forms[0].submit();
            return;
        }}
        tiempoRestante--;
    }}
    </script>

    <style>

    body {{
        font-family: Arial, sans-serif;
        background-color: #f4f6f9;
        margin: 40px;
    }}

    .container {{
        max-width: 900px;
        margin: auto;
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
    }}

    .question {{
        background: #fafafa;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }}

    h1 {{
        color: #1f2937;
    }}

    h2 {{
        color: #374151;
    }}

    select {{
        padding: 10px;
        font-size: 16px;
        width: 100%;
        margin-bottom: 25px;
    }}

    button {{
        background-color: #2563eb;
        color: white;
        padding: 12px 20px;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        cursor: pointer;
    }}

    button:hover {{
        background-color: #1d4ed8;
    }}

    .option {{
        margin-top: 10px;
    }}

    </style>

    </head>

    <body>

    <div class="container">

    <h1>Sistema de Quizzes</h1>
    
    <h2 id="timer">
    Tiempo restante:
    </h2>

    <h2>Seleccione estudiante</h2>

    <form method="POST" action="/submit/{quiz_id}">

    <label>
    Código estudiante:
    </label>

    <br><br>

    <input
        type="text"
        name="id_estudiante"
        required
    >

    {html_preguntas}

    <br>

    <button type="submit">
    Enviar Quiz
    </button>

    </form>

    </div>

    </body>

    </html>
    """

    return html


# -----------------------------
# VER RESPUESTAS
# -----------------------------

@app.route("/respuestas")
def ver_respuestas():

    data_resp = worksheet_resp.get_all_records()

    df_resp = pd.DataFrame(data_resp)

    if df_resp.empty:

        return "<h1>No hay respuestas todavía</h1>"

    # eliminar duplicados por estudiante + quiz
    resumen = df_resp[
        ["id_quiz", "id_estudiante", "fecha_hora"]
    ].drop_duplicates()

    html = """
    <html>

    <head>

    <style>

    body {
        font-family: Arial;
        margin: 40px;
        background-color: #f4f6f9;
    }

    table {
        border-collapse: collapse;
        width: 100%;
        background: white;
    }

    th, td {
        border: 1px solid #ddd;
        padding: 12px;
    }

    th {
        background-color: #2563eb;
        color: white;
    }

    </style>

    </head>

    <body>

    <h1>Respuestas registradas</h1>

    <table>

    <tr>
        <th>Quiz</th>
        <th>Estudiante</th>
        <th>Fecha</th>
    </tr>
    """

    for _, row in resumen.iterrows():

        html += f"""
        <tr>
            <td>{row['id_quiz']}</td>
            <td>{row['id_estudiante']}</td>
            <td>{row['fecha_hora']}</td>
        </tr>
        """

    html += """
    </table>

    </body>

    </html>
    """

    return html

# -----------------------------

from flask import request

# -----------------------------
# RECIBIR RESPUESTAS
# -----------------------------

@app.route("/submit/<quiz_id>", methods=["POST"])

def submit(quiz_id):
    respuestas = request.form

    id_estudiante = respuestas["id_estudiante"]
    print("ID ingresado:", id_estudiante)
    
    print("QUIZ recibido submit:", quiz_id)
    data_asig = worksheet_asig.get_all_records()
    df_asig = pd.DataFrame(data_asig)
    print(df_asig)

    paralelos_habilitados = df_asig[
        (
            df_asig["id_quiz"]
            .astype(str)
            .str.strip()
            == str(quiz_id).strip()
        )
    ]["paralelo"].tolist()

    print("Paralelos habilitados:", paralelos_habilitados)

    df_est_filtrado = df_est[
        df_est["paralelo"]
        .astype(str)
        .str.strip()
        .isin(
            [str(p).strip() for p in paralelos_habilitados]
        )
    ]

    print(df_est_filtrado[["id_estudiante", "paralelo"]])

    estudiante_data = df_est_filtrado[
        df_est_filtrado["id_estudiante"]
        .astype(str)
        .str.strip()
        == str(id_estudiante).strip()
    ]

    print(estudiante_data)

    if estudiante_data.empty:
        return """
        <h1>
        Código estudiante inválido para este quiz
        </h1>
        """
    
    # -----------------------------
    # RECARGAR RESPUESTAS
    # -----------------------------
    data_resp = worksheet_resp.get_all_records()
    df_resp = pd.DataFrame(data_resp)

    if df_resp.empty:
        df_resp = pd.DataFrame(
            columns=[
                "id_quiz",
                "id_estudiante"
            ]
        )

    intentos_previos = df_resp[
        (df_resp["id_quiz"] == quiz_id) &
        (df_resp["id_estudiante"].astype(str) == str(id_estudiante))
    ]

    if not intentos_previos.empty:
        return """
        <h1>Intento ya registrado</h1>
        <p>
        Ya respondiste este quiz anteriormente.
        </p>
        """

    puntaje = 0

    total = 0

    html = """
    <h1>Resultado Quiz</h1>
    <hr>
    """

    for pregunta, respuesta in respuestas.items():

        if pregunta == "id_estudiante":
            continue

        pregunta_data = df_preg[df_preg["id_pregunta"] == pregunta]

        if not pregunta_data.empty:

            row = pregunta_data.iloc[0]

            correcta = row["correcta"]

            total += 1

            if respuesta == correcta:

                puntaje += 1

                estado = "✅ Correcta"

            else:

                estado = f"""
                ❌ Incorrecta.
                Correcta: {correcta}
                """

            id_estudiante = respuestas["id_estudiante"]
            id_respuesta = str(uuid.uuid4())
            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            correcta_bool = respuesta == correcta
            puntaje_pregunta = 1 if correcta_bool else 0
            worksheet_resp.append_row([
                id_respuesta,
                quiz_id,
                id_estudiante,
                pregunta,
                respuesta,
                correcta_bool,
                puntaje_pregunta,
                fecha_hora,
                1
            ])

            html += f"""
            <p>
            <b>{pregunta}</b><br>
            Respuesta estudiante: {respuesta}<br>
            {estado}
            </p>
            <hr>
            """

    html += f"""
    <h2>Puntaje: {puntaje}/{total}</h2>
    """

    return html

if __name__ == "__main__":
    app.run(debug=True)