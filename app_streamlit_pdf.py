import streamlit as st
import subprocess
import tempfile
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

# ---------------------------
# Configuration des exercices
# ---------------------------
EXERCICES = {
    "exo1": {"titre": "Multiples de 5"},
    "exo2": {"titre": "Analyse de hauteurs"},
    "exo3": {"titre": "Gestion d’une bibliothèque"}
}

MAX_POINTS = 10

# ---------------------------
# Helpers
# ---------------------------
def detect_minor_syntax(stderr_text):
    if not stderr_text:
        return False
    patterns = [r"expected ';'", r"expected '\)'", r"expected '}'"]
    text = stderr_text.lower()
    return any(re.search(p, text) for p in patterns)

def assess_structure_and_logic(source_text, exo_key):
    src_low = source_text.lower()
    comments = []
    s_pts = 3 if "for" in src_low or "while" in src_low else 2
    l_pts = 3 if "somme" in src_low or "moyenne" in src_low or "struct" in src_low else 2
    style_pts = 1 if "//" in source_text or "/*" in source_text else 0
    if s_pts < 3:
        comments.append("Structure incomplète détectée")
    if l_pts < 3:
        comments.append("Logique partielle détectée")
    if style_pts == 0:
        comments.append("Style minimal absent")
    return s_pts, l_pts, style_pts, comments

def compile_code(code_path):
    exe_path = code_path.replace(".c", ".out")
    compile_cmd = ["gcc", code_path, "-o", exe_path, "-Wall"]
    try:
        compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=12)
        return compile_proc.returncode == 0, compile_proc.stderr, exe_path
    except FileNotFoundError:
        return False, "gcc introuvable", exe_path

def evaluate_file(code_path, exo_key):
    with open(code_path, "r", encoding="utf-8", errors="ignore") as f:
        source_text = f.read()
    compile_ok, stderr, exe_path = compile_code(code_path)
    points = {"compilation": 0, "structure": 0, "logique": 0, "style": 0}
    comments = []

    if compile_ok:
        points["compilation"] = 2
        comments.append("Compilation réussie")
    else:
        if detect_minor_syntax(stderr):
            points["compilation"] = 1
            comments.append("Erreur mineure de syntaxe détectée")
        else:
            points["compilation"] = 0
            comments.append("Échec de compilation")

    s_pts, l_pts, style_pts, analysis_comments = assess_structure_and_logic(source_text, exo_key)
    points["structure"] = s_pts
    points["logique"] = l_pts
    points["style"] = style_pts
    comments.extend(analysis_comments)

    total = sum(points.values())
    if total > MAX_POINTS:
        total = MAX_POINTS

    return total, points, comments

def make_pdf(results, student_name, missing_exos=None):
    safe_name = "".join(c for c in (student_name or "eleve") if c.isalnum() or c in ("_", "-"))
    filename = f"correction_{safe_name}.pdf"

    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica", 12)
    y = 800
    c.drawString(50, y, f"Correction automatique multi-exercices")
    y -= 20
    c.drawString(50, y, f"Élève : {student_name or '---'}")
    y -= 20
    c.drawString(50, y, f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 30
    for exo_key, res in results.items():
        c.drawString(50, y, f"{EXERCICES[exo_key]['titre']} : {res['total']}/10")
        y -= 18
        c.drawString(60, y, f"Compilation (2 pts) : {res['points']['compilation']}")
        y -= 14
        c.drawString(60, y, f"Structure (3 pts) : {res['points']['structure']}")
        y -= 14
        c.drawString(60, y, f"Logique (3 pts) : {res['points']['logique']}")
        y -= 14
        c.drawString(60, y, f"Style (1 pt) : {res['points']['style']}")
        y -= 14
        c.drawString(60, y, "Commentaires :")
        y -= 14
        for cm in res['comments']:
            c.drawString(70, y, "- " + cm)
            y -= 14
        y -= 10

    if missing_exos:
        y -= 20
        c.drawString(50, y, f"Exercices non rendus : {', '.join(missing_exos)}")

    # Calcul note finale sur 20
    total_points_rendus = sum(res['total'] for res in results.values())
    total_points_sur_3 = total_points_rendus + 0*len(missing_exos)
    moyenne = total_points_sur_3 / 3
    note_20 = round(total_points_sur_3 * 2 / 3, 1)

    y -= 40
    c.drawString(50, y, f"Moyenne : {moyenne:.1f}/10")
    y -= 20
    c.drawString(50, y, f"Note finale : {note_20:.1f}/20")

    c.save()
    return filename

# ---------------------------
# Interface Streamlit
# ---------------------------
st.set_page_config(page_title="Correcteur multi-exercices", layout="wide")
st.title("Correcteur automatique tolérant — 3 exercices C")
st.markdown("""
Upload **1 à 3 fichiers C** de l'élève.  
Pour chaque fichier, indiquez à quel exercice il correspond.
""")

student_name = st.text_input("Nom / ID de l'élève")

uploaded_files = []
for exo_key in EXERCICES.keys():
    file = st.file_uploader(f"Fichier {EXERCICES[exo_key]['titre']}", type=["c"], key=exo_key)
    if file:
        uploaded_files.append((exo_key, file))

if uploaded_files:
    results = {}
    for exo_key, file in uploaded_files:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".c")
        tmp_file.write(file.read())
        tmp_file.close()
        total, points, comments = evaluate_file(tmp_file.name, exo_key)
        results[exo_key] = {"total": total, "points": points, "comments": comments}

    # Identifier les exercices non rendus
    missing_exos = [exo for exo in EXERCICES.keys() if exo not in results]
    if missing_exos:
        st.warning(f"Exercices non rendus : {', '.join(missing_exos)}")

    # Affichage résultats
    st.subheader(f"Résultats de {student_name}")
    for exo_key, res in results.items():
        st.markdown(f"### {EXERCICES[exo_key]['titre']} : {res['total']}/10")
        st.write("**Détail du barème :**")
        st.write(f"- Compilation (2 pts) : {res['points']['compilation']}")
        st.write(f"- Structure (3 pts) : {res['points']['structure']}")
        st.write(f"- Logique (3 pts) : {res['points']['logique']}")
        st.write(f"- Style (1 pt) : {res['points']['style']}")
        st.write("**Commentaires :**")
        for c in res['comments']:
            st.write("- " + c)

    # Calcul de la note finale sur 20
    total_points_rendus = sum(res['total'] for res in results.values())
    total_points_sur_3 = total_points_rendus + 0*len(missing_exos)
    moyenne = total_points_sur_3 / 3
    note_20 = round(total_points_sur_3 * 2 / 3, 1)

    st.markdown(f"### Moyenne générale : {moyenne:.1f}/10")
    st.markdown(f"### Note finale : {note_20:.1f}/20")

    # PDF uniquement quand on clique sur le bouton
    if st.button("Télécharger le rapport PDF"):
        pdf_file = make_pdf(results, student_name, missing_exos)
        with open(pdf_file, "rb") as f:
            st.download_button("Cliquez ici pour télécharger le PDF", f.read(), file_name=pdf_file)

else:
    st.info("Merci de téléverser au moins 1 fichier C.")
