import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- CONSTANTES CONFIGURABLES ---
MARGE_NETTE = 0.15   # 15% de gain net souhaité
FRAIS_FIXES = 350    # Frais de dossier fixes
TVA_TAUX = 0.081     # TVA 8.1% (Suisse)

HISTO_FICHIER = "historique_estimations.csv"


def format_chf(val):
    """Formate un nombre en CHF avec apostrophe comme séparateur de milliers."""
    return f"{val:,.0f}".replace(",", "'") + " CHF"


def construire_lien_autoscout(marque, modele, annee, km):
    """Construit l'URL AutoScout24 pour analyse de marché."""
    m_clean = marque.replace(" ", "-").lower()
    mod_clean = modele.replace(" ", "-").lower()

    year_from = annee - 1
    year_to = annee + 1
    km_to = km + 20000

    lien = (
        f"https://www.autoscout24.ch/fr/s/{m_clean}/{mod_clean}"
        f"?yearfrom={year_from}&yearto={year_to}"
        f"&kmto={km_to}&sort=price_asc"
    )
    return lien


def calcul_offre_max(prix_vente, frais_remise, type_tva):
    """Calcule le prix d'achat max selon le type de TVA."""

    couts = FRAIS_FIXES + (frais_remise * 1.05)
    marge_voulue = prix_vente * MARGE_NETTE

    if type_tva == "TVA sur marge (achat à un particulier)":
        coeff = TVA_TAUX / (1 + TVA_TAUX)
        marge_brute = (marge_voulue + couts) / (1 - coeff)
        tva_etat = marge_brute * coeff
        prix_achat = prix_vente - marge_brute
        info_tva = "TVA sur Marge"
    else:
        ht_vente = prix_vente / (1 + TVA_TAUX)
        ht_achat = ht_vente - (ht_vente * MARGE_NETTE) - couts
        prix_achat = ht_achat * (1 + TVA_TAUX)
        tva_etat = prix_vente - ht_vente
        info_tva = "TVA Standard"

    return prix_achat, marge_voulue, tva_etat, info_tva, couts


def generer_excel_estimation(
    marque, modele, annee, km, prix_vente, frais_remise,
    type_tva, prix_achat, marge_voulue, tva_etat, couts
):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    data = {
        "Date estimation": [now],
        "Garage": ["7 Cars Garage Sàrl"],
        "Marque": [marque],
        "Modèle": [modele],
        "Année": [annee],
        "Kilométrage": [km],
        "Origine TVA": [type_tva],
        "Prix de revente estimé (CHF)": [prix_vente],
        "Frais remise en état (CHF)": [frais_remise],
        "Frais fixes + sécurité (CHF)": [couts],
        "Marge visée nette (CHF)": [marge_voulue],
        "TVA à reverser (CHF)": [tva_etat],
        "Offre d'achat maximale (CHF)": [prix_achat],
    }

    df = pd.DataFrame(data)
    fichier = io.BytesIO()
    with pd.ExcelWriter(fichier, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Estimation")
    fichier.seek(0)
    return fichier


def generer_pdf_estimation(
    marque, modele, annee, km, prix_vente, frais_remise,
    type_tva, prix_achat, marge_voulue, tva_etat, couts
):
    """Génère un PDF propre de l'estimation et renvoie un BytesIO."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x_margin = 40
    y = height - 50

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # En-tête
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x_margin, y, "7 CARS GARAGE SÀRL – LIEBISTORF")
    y -= 25
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_margin, y, "Estimation professionnelle de reprise")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(x_margin, y, f"Date de l'estimation : {now}")
    y -= 30

    # Infos véhicule
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "1. Données véhicule")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(x_margin, y, f"Marque / Modèle : {marque} {modele}")
    y -= 14
    c.drawString(x_margin, y, f"Année : {int(annee)}")
    y -= 14
    c.drawString(x_margin, y, f"Kilométrage : {int(km):,} km".replace(",", "'"))
    y -= 25

    # Hypothèses
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "2. Hypothèses de revente")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(x_margin, y, f"Prix de revente estimé : {format_chf(prix_vente)}")
    y -= 14
    c.drawString(x_margin, y, f"Frais remise en état : {format_chf(frais_remise)}")
    y -= 14
    c.drawString(x_margin, y, f"Origine TVA : {type_tva}")
    y -= 25

    # Résultat
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "3. Résultat d'estimation")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(x_margin, y, f"Offre d'achat maximale : {format_chf(prix_achat)}")
    y -= 14
    c.drawString(x_margin, y, f"Marge visée (net en poche) : {format_chf(marge_voulue)}")
    y -= 14
    c.drawString(x_margin, y, f"TVA à reverser : {format_chf(tva_etat)}")
    y -= 14
    c.drawString(x_margin, y, f"Frais fixes + sécurité : {format_chf(couts)}")
    y -= 25

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        x_margin,
        y,
        "Cette estimation est un outil interne pour garantir un positionnement haut de gamme, sans remises.",
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def ajouter_a_historique(
    marque, modele, annee, km, prix_vente, frais_remise,
    type_tva, prix_achat, marge_voulue, tva_etat, couts
):
    """Ajoute l'estimation à un fichier CSV local."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    ligne = {
        "Date": now,
        "Marque": marque,
        "Modèle": modele,
        "Année": int(annee),
        "Kilométrage": int(km),
        "Origine TVA": type_tva,
        "Prix revente": prix_vente,
        "Frais remise": frais_remise,
        "Frais fixes + sécurité": couts,
        "Marge visée": marge_voulue,
        "TVA à reverser": tva_etat,
        "Offre max achat": prix_achat,
    }

    df = pd.DataFrame([ligne])
    existe = os.path.exists(HISTO_FICHIER)
    df.to_csv(
        HISTO_FICHIER,
        mode="a",
        header=not existe,
        index=False,
        encoding="utf-8-sig",
    )


def injecter_css():
    """CSS premium."""
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top left, #202020, #080808);
            color: #f5f5f5;
        }
        .bloc-carte {
            border-radius: 14px;
            padding: 1.2rem 1.4rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: linear-gradient(145deg, rgba(20,20,20,0.96), rgba(12,12,12,0.94));
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def main():

    st.set_page_config(
        page_title="Estimation reprise – 7 Cars Garage",
        page_icon="🚗",
        layout="wide",
    )

    injecter_css()

    # --- ENTÊTE / BRANDING ---
    col_logo, col_titre = st.columns([0.25, 0.75])

    with col_logo:
        st.image("logo_7cars.PNG", use_container_width=True)

    with col_titre:
        st.markdown(
            '<div style="font-size:0.9rem;text-transform:uppercase;letter-spacing:0.18em;color:#b3b3b3;">'
            "7 Cars Garage Sàrl – Liebistorf"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("## Estimation professionnelle de reprise")

    st.markdown("")

    # --- COLONNES PRINCIPALES ---
    col1, col2 = st.columns([1.05, 1])

    with col1:
        st.markdown('<div class="bloc-carte">', unsafe_allow_html=True)

        st.markdown("### 1. Données véhicule")
        marque = st.text_input("Marque", value="Audi")
        modele = st.text_input("Modèle", value="A3")
        annee = st.number_input("Année", 1980, 2100, 2019)
        km = st.number_input("Kilométrage (km)", 0, 500000, 80000)

        if marque and modele and annee:
            lien = construire_lien_autoscout(marque, modele, int(annee), int(km))
            st.markdown("**Analyse de marché :**")
            st.link_button("🔎 Ouvrir la recherche AutoScout24", lien)

        st.markdown("---")

        st.markdown("### 2. Hypothèses de revente")
        prix_vente = st.number_input("Prix de revente estimé (CHF)", 0.0, value=22000.0, step=500.0)
        frais_remise = st.number_input("Frais de remise en état (CHF)", 0.0, value=1500.0, step=100.0)

        type_tva = st.radio(
            "Origine du véhicule / traitement TVA",
            [
                "TVA sur marge (achat à un particulier)",
                "TVA standard (achat à un garage/entreprise)",
            ],
        )

        calculer = st.button("💰 Calculer l'offre d'achat maximale")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="bloc-carte">', unsafe_allow_html=True)
        st.markdown("### 3. Résultat estimation")

        estimation_ok = False

        if calculer:
            if prix_vente <= 0:
                st.error("Le prix de revente estimé doit être supérieur à 0.")

            else:
                prix_achat, marge_voulue, tva_etat, info_tva, couts = calcul_offre_max(
                    prix_vente, frais_remise, type_tva
                )

                if prix_achat <= 0:
                    st.warning(
                        "Offre d'achat négative ou nulle. Ajuste la marge ou le prix."
                    )
                else:
                    estimation_ok = True

                    st.markdown(
                        f"""
                        <div style="border-radius:18px;padding:1.3rem 1.5rem;
                                   border:1px solid rgba(255,255,255,0.14);
                                   background: radial-gradient(circle at top left,#262626,#101010);">
                            <div style="font-size:0.78rem;letter-spacing:0.18em;text-transform:uppercase;
                                        color:#bdbdbd;margin-bottom:0.3rem;">
                                Offre maximale conseillée
                            </div>
                            <div style="font-size:1.0rem;margin-bottom:0.2rem;">
                                {marque} {modele} • {int(annee)} • {int(km):,} km
                            </div>
                            <div style="font-size:1.8rem;font-weight:700;margin-top:0.2rem;">
                                {format_chf(prix_achat)}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("### Détail financier")
                    colR1, colR2 = st.columns(2)

                    with colR1:
                        st.metric("Prix de revente prévu", format_chf(prix_vente))
                        st.metric("Marge visée (net)", format_chf(marge_voulue))

                    with colR2:
                        st.metric(f"TVA à reverser ({info_tva})", format_chf(tva_etat))
                        st.metric("Frais fixes + sécurité", format_chf(couts))

                    # Stocker résultats pour les téléchargements
                    valeurs_calculees = (
                        prix_achat, marge_voulue, tva_etat, info_tva, couts
                    )

        else:
            st.info("Remplis les champs à gauche puis clique sur « Calculer ».")

        # Téléchargements
        if estimation_ok:
            prix_achat, marge_voulue, tva_etat, info_tva, couts = valeurs_calculees

            nom_base = f"estimation_{marque}_{modele}_{int(annee)}".replace(" ", "_")

            # Excel
            fichier_excel = generer_excel_estimation(
                marque, modele, annee, km, prix_vente, frais_remise,
                type_tva, prix_achat, marge_voulue, tva_etat, couts
            )
            st.download_button(
                "📥 Télécharger l’estimation (Excel)",
                fichier_excel,
                file_name=nom_base + ".xlsx",
            )

            # PDF
            fichier_pdf = generer_pdf_estimation(
                marque, modele, annee, km, prix_vente, frais_remise,
                type_tva, prix_achat, marge_voulue, tva_etat, couts
            )
            st.download_button(
                "📄 Télécharger l’estimation (PDF)",
                fichier_pdf,
                file_name=nom_base + ".pdf",
            )

            # Historique
            ajouter_a_historique(
                marque, modele, annee, km, prix_vente, frais_remise,
                type_tva, prix_achat, marge_voulue, tva_etat, couts
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # --- 4. HISTORIQUE DES ESTIMATIONS ---
    st.markdown("### 4. Historique des estimations")

    if os.path.exists(HISTO_FICHIER):
        df_histo = pd.read_csv(HISTO_FICHIER)
        st.dataframe(df_histo, use_container_width=True)
    else:
        st.caption("Aucune estimation enregistrée pour le moment.")


if __name__ == "__main__":
    main()
