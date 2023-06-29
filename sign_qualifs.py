import os
import shutil
import tempfile
import uuid

import streamlit as st
from fitz import fitz
from streamlit_drawable_canvas import st_canvas

from utils import canvas_to_bytes_images, create_filename

st.title('Signer des qualifications')
st.markdown("""
Cet outils a vocation à aider les territoires SGDF à générer les qualifications.

Sur l'intranet, vous pouvez exporter les qualifications de votre territoire mais il est impossible de mélanger les qualifications d'animateur et de directeur.

La proposition de cet outils est d'exporter depuis l'intranet toute les qualifications d'animateur puis de directeur. Ensuite, vous pouvez signer et tamponner ces qualifications dans cet outils.

En sortie, vous obtiendrez une archive zip avec un fichier nominatif par personne (et précisé si c'est une qualification d'animateur ou de directeur).
Les fichers seront nommées `Nom Prénom -Anim.pdf` ou `Nom Prénom -Dir.pdf`.

Sur l'intranet, vous pouvez exporter facilement toutes les qualifications d'animateur, pour cela:
- Aller sur l'intranet et sur `Editer les qualifications Scoutisme Français`
- Selectionner `Chercher dans les structures dépendantes` et cliquer sur `Afficher`
- Faire clique droit, cliquer sur `inpecter`, sur la fenêtre qui s'ouvre à droite cliquer sur l'onglet `console`
- Coller ce code:
```js
[
  ...document.getElementsByClassName("ligne1"),
  ...document.getElementsByClassName("ligne2")
].forEach(
    el => {
        if (el.innerHTML.includes("Directeur Action de Formation") || el.innerHTML.includes("Formateur SF (CAFFSF)") || el.innerHTML.includes("Responsable Unité SF (CAFRUSF)") || el.innerHTML.includes("Directeur SF (CAFDSF)")) {
            el.remove()
        }
    });
```
- Appuyer sur entrée et il vous reste uniquement les qualifications d'animateur de votre territoire
- Vous pouvez désormais cliquer sur la case `Tout cocher / décocher` en haut à droite et exporter toutes les qualifications d'animateur.

Pour exporter les qualifications de directeur, il faut suivre la même procédure mais avec le code suivant:
```js
[
  ...document.getElementsByClassName("ligne1"),
  ...document.getElementsByClassName("ligne2")
].forEach(
    el => {
        if (el.innerHTML.includes("Directeur Action de Formation") || el.innerHTML.includes("Formateur SF (CAFFSF)") || el.innerHTML.includes("Responsable Unité SF (CAFRUSF)") || el.innerHTML.includes("Animateur SF (CAFASF)")) {
            el.remove()
        }
    });
```

Aucune donnée n'est conservé par cet outil.
""")

st.text('Dessinez votre signature ici:')
signature = st_canvas(
    fill_color="rgba(255, 255, 255, 1)",
    height=250,
    width=250,
    stroke_width=6,
    key="canvas",
    update_streamlit=True
)

st.text('Importer votre tampon ici:')
tampon = st.file_uploader("Tampon", type=["png", "jpg"])

st.text("Importer ici le fichier généré par l'intranet:")
form = st.form("my_form", clear_on_submit=True)
uploaded_file = form.file_uploader('Qualifications', type='pdf', accept_multiple_files=False)
submit = form.form_submit_button("Lancer la signature")

if submit:
    if uploaded_file is not None and signature.image_data is not None and tampon is not None:
        stamp_rectangle = fitz.Rect(450, 540, 550, 640)
        signature_rectangle = fitz.Rect(80, 520, 140, 580)

        file_handle = fitz.open(stream=uploaded_file.read())
        stamp_xref = 0
        signature_xref = 0
        if not file_handle.is_pdf:
            st.error("Le fichier n'est pas un PDF lisible")

        progress_text = "Signature en cours ..."
        my_bar = st.progress(0, text=progress_text)

        with tempfile.TemporaryDirectory() as tmpdirname:
            for i in range(0, file_handle.page_count, 2):
                page = file_handle[i]
                stamp_xref = page.insert_image(
                    stamp_rectangle,
                    stream=tampon.read(),
                    xref=stamp_xref,
                    alpha=0,
                    overlay=False
                )

                signature_xref = page.insert_image(
                    signature_rectangle,
                    stream=canvas_to_bytes_images(signature.image_data),
                    xref=signature_xref,
                    alpha=0,
                    overlay=False
                )
                output_filename = ""
                for x0, y0, x1, y1, text, block_no, block_type in page.get_text("blocks"):
                    if text.startswith("Mlle, Mme, M. : "):
                        output_filename = create_filename(text.replace('Mlle, Mme, M. : ', ''), "Anim")
                    if text.startswith("Mlle-Mme-M. : "):
                        output_filename = create_filename(text.replace('Mlle-Mme-M. : ', ''), "Dir")
                new_doc = fitz.open()
                new_doc.insert_pdf(file_handle, from_page=i, to_page=i + 1)
                new_doc.save(tmpdirname + "/" + output_filename, garbage=4)

                my_bar.progress(i / file_handle.page_count, text=progress_text)
            my_bar.progress(100, text="Création de l'archive en cours...")
            output_file = shutil.make_archive(str(uuid.uuid4()), 'zip', tmpdirname)
            my_bar.empty()

        f = open(output_file, 'rb')


        def on_click():
            f.close()
            os.remove(output_file)

        st.download_button(
            'Télécharger les qualifications signées',
            f,
            mime='application/zip',
            file_name='sign_qualifs.zip',
            on_click=on_click
        )
    else:
        st.warning("Il faut renseigner un tampon et une signature afin de lancer le traitement des qualifications.")
