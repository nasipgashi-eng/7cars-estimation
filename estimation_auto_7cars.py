import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF

# --- CONSTANTES CONFIGURABLES ---
MARGE_NETTE = 0.15   # 15% de gain net souhaité
FRAIS_FIXES = 350    # Frais de dossier fixes
TVA_TAUX = 0.081     # TVA 8.1% (Suisse)


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
   def generer_pdf_estimation(
    marque, modele, annee, km, prix_vente, frais_remise,
    type_tva, prix_achat, marge_voulue, tva_etat, couts
):
    """Génère un PDF récapitulatif de l'estimation."""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Logo en haut à gauche
    try:
        pdf.image("logo_7cars.PNG", x=10, y=8, w=40)
    except Exception:
        pass

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Estimation professionnelle de reprise", ln=1, align="R")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "7 Cars Garage Sàrl – Liebistorf", ln=1, align="R")
    pdf.ln(10)

    # Infos générales
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "1. Données véhicule", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Date de l'estimation : {now}", ln=1)
    pdf.cell(0, 6, f"Véhicule : {marque} {modele}", ln=1)
    pdf.cell(0, 6, f"Année : {annee}", ln=1)
    pdf.cell(0, 6, f"Kilométrage : {km:,} km".replace(",", "'"), ln=1)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "2. Hypothèses de revente", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Prix de revente estimé : {format_chf(prix_vente)}", ln=1)
    pdf.cell(0, 6, f"Frais remise en état : {format_chf(frais_remise)}", ln=1)
    pdf.cell(0, 6, f"Origine TVA : {type_tva}", ln=1)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "3. Résultat financier", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Offre d'achat maximale : {format_chf(prix_achat)}", ln=1)
    pdf.cell(0, 6, f"Marge nette visée : {format_chf(marge_voulue)}", ln=1)
    pdf.cell(0, 6, f"TVA à reverser : {format_chf(tva_etat)}", ln=1)
    pdf.cell(0, 6, f"Frais fixes + sécurité : {format_chf(couts)}", ln=1)
    pdf.ln(6)

    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(
        0, 5,
        "Cette offre maximale est la limite à ne pas dépasser à l'achat afin de rester "
        "aligné avec un positionnement qualitatif sans recourir aux remises."
    )

    # Retourne le PDF en mémoire
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return io.BytesIO(pdf_bytes)
 HISTO_CSV = "historique_estimations.csv"


def enregistrer_historique(
    marque, modele, annee, km, prix_vente, frais_remise,
    type_tva, prix_achat, marge_voulue, tva_etat, couts
):
    """Ajoute l'estimation à un fichier CSV local."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ligne = {
        "Date estimation": now,
        "Marque": marque,
        "Modèle": modele,
        "Année": annee,
        "Kilométrage": km,
        "Prix revente": prix_vente,
        "Frais remise": frais_remise,
        "Type TVA": type_tva,
        "Prix achat max": prix_achat,
        "Marge nette": marge_voulue,
        "TVA": tva_etat,
        "Frais totaux": couts,
    }

    try:
        df_exist = pd.read_csv(HISTO_CSV)
    except FileNotFoundError:
        df_exist = pd.DataFrame()

    df_nouveau = pd.concat([df_exist, pd.DataFrame([ligne])], ignore_index=True)
    df_nouveau.to_csv(HISTO_CSV, index=False)

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


def injecter_css():
    """CSS pour un look plus haut de gamme."""
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top left, #202020, #080808);
            color: #f5f5f5;
        }
        h1, h2, h3 {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
        }
        .bloc-carte {
            border-radius: 14px;
            padding: 1.2rem 1.4rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: linear-gradient(145deg, rgba(20,20,20,0.96), rgba(12,12,12,0.94));
        }
        [data-testid="stMetricValue"] {
            font-size: 1.4rem;
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
        # Affiche le logo qui est dans le dépôt sous le nom "logo_7cars.PNG"
        st.image("logo_7cars.PNG", use_container_width=True)

    with col_titre:
        st.markdown(
            '<div style="font-size:0.9rem;text-transform:uppercase;letter-spacing:0.18em;color:#b3b3b3;">'
            "7 Cars Garage Sàrl – Liebistorf"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("## Estimation professionnelle de reprise")
        st.caption(
            "Outil interne pour calculer une offre d’achat cohérente avec un positionnement haut de gamme, "
            "sans recours aux remises ni rabais."
        )

    st.markdown("")

    # --- COLONNES PRINCIPALES ---
    col1, col2 = st.columns([1.05, 1])

    with col1:
        st.markdown('<div class="bloc-carte">', unsafe_allow_html=True)
        st.markdown("### 1. Données véhicule")

        marque = st.text_input("Marque", value="Audi")
        modele = st.text_input("Modèle", value="A3")
        annee = st.number_input("Année", min_value=1980, max_value=2100, value=2019, step=1)
        km = st.number_input("Kilométrage (km)", min_value=0, max_value=500_000, value=80_000, step=500)

        if marque and modele and annee:
            lien = construire_lien_autoscout(marque, modele, int(annee), int(km))
            st.markdown("**Analyse de marché :**")
            st.link_button("🔎 Ouvrir la recherche AutoScout24", lien)

        st.markdown("---")
        st.markdown("### 2. Hypothèses de revente")

        prix_vente = st.number_input(
            "Prix de revente estimé (CHF)",
            min_value=0.0,
            value=22000.0,
            step=500.0,
        )

        frais_remise = st.number_input(
            "Frais de remise en état (CHF)",
            min_value=0.0,
            value=1500.0,
            step=100.0,
        )

        type_tva = st.radio(
            "Origine du véhicule / traitement TVA",
            options=[
                "TVA sur marge (achat à un particulier)",
                "TVA standard (achat à un garage/entreprise)",
            ],
        )

        calculer = st.button("💰 Calculer l'offre d'achat maximale")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="bloc-carte">', unsafe_allow_html=True)
        st.markdown("### 3. Résultat estimation")

        if calculer:
            if prix_vente <= 0:
                st.error("Le prix de revente estimé doit être supérieur à 0.")
            else:
                prix_achat, marge_voulue, tva_etat, info_tva, couts = calcul_offre_max(
                    prix_vente, frais_remise, type_tva
                )

                if prix_achat <= 0:
                    st.warning(
                        "Avec ces paramètres, le prix d'achat ressort négatif ou nul.\n\n"
                        "➡ Revois soit la marge, soit le prix de revente estimé, soit les frais."
                    )
                else:
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
                        st.metric("Marge visée (net en poche)", format_chf(marge_voulue))

                    with colR2:
                        st.metric(f"TVA à reverser ({info_tva})", format_chf(tva_etat))
                        st.metric("Frais fixes + sécurité", format_chf(couts))

                    st.markdown("---")
                    st.markdown(
                        "- Cette **offre max** est la limite à ne pas dépasser à l'achat pour rester "
                        "aligné avec un positionnement qualitatif.\n"
                        "- Aucune remise n’est appliquée au client final : la valeur perçue reste haute, "
                        "la marge est protégée."
                    )

                    fichier_excel = generer_excel_estimation(
                        marque=marque,
                        modele=modele,
                        annee=int(annee),
                        km=int(km),
                        prix_vente=prix_vente,
                        frais_remise=frais_remise,
                        type_tva=type_tva,
                        prix_achat=prix_achat,
                        marge_voulue=marge_voulue,
                        tva_etat=tva_etat,
                        couts=couts,
                    )

                    nom_fichier = f"estimation_{marque}_{modele}_{int(annee)}.xlsx".replace(" ", "_")

                    st.download_button(
                        label="📥 Télécharger l’estimation (Excel)",
                        data=fichier_excel,
                        file_name=nom_fichier,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
        else:
            st.info("Renseigne les informations à gauche puis clique sur **« Calculer l'offre d'achat maximale »**.")

        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
