import json

from odoo import api, models

# ── Couleurs officielles DPE (arrêté du 31 mars 2021) ───────────────────────
_DPE_COLORS = {
    'A': '#009B4E', 'B': '#51AE44', 'C': '#B7D23E',
    'D': '#F5D000', 'E': '#EEB119', 'F': '#E76F2A', 'G': '#D7221F',
}
_DPE_TEXT = {
    'A': '#fff', 'B': '#fff', 'C': '#1a1a1a',
    'D': '#1a1a1a', 'E': '#1a1a1a', 'F': '#fff', 'G': '#fff',
}
_ENERGIE_RANGES = {
    'A': '≤ 70', 'B': '71-110', 'C': '111-180',
    'D': '181-250', 'E': '251-330', 'F': '331-420', 'G': '> 420',
}
_GES_RANGES = {
    'A': '≤ 6', 'B': '7-11', 'C': '12-30',
    'D': '31-50', 'E': '51-70', 'F': '71-100', 'G': '> 100',
}
_BAR_WIDTHS = {'A': 42, 'B': 51, 'C': 60, 'D': 69, 'E': 78, 'F': 87, 'G': 96}


def _build_scale(current_class, ranges):
    return [{
        'letter': ltr,
        'color': _DPE_COLORS.get(ltr, '#ccc'),
        'text_color': _DPE_TEXT.get(ltr, '#333'),
        'range': ranges.get(ltr, ''),
        'width': _BAR_WIDTHS.get(ltr, 60),
        'selected': ltr == (current_class or '').upper(),
    } for ltr in 'ABCDEFG']


def _qualite_style(val):
    v = (val or '').lower()
    if 'insuffisant' in v:
        return 'background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;'
    if 'moyenne' in v or 'moyen' in v:
        return 'background:#FEF3C7;color:#92400E;border:1px solid #FCD34D;'
    if 'bonne' in v or 'bon' in v or 'très' in v:
        return 'background:#D1FAE5;color:#065F46;border:1px solid #6EE7B7;'
    return 'background:#F1F5F9;color:#475569;border:1px solid #CBD5E1;'


def _fmt(val, decimals=0):
    if val is None or val == '' or val == 0:
        return '—'
    try:
        v = float(val)
        if v == 0:
            return '—'
        if decimals == 0:
            return f"{int(round(v)):,}".replace(',', ' ')
        return f"{v:.{decimals}f}".replace('.', ',')
    except Exception:
        return str(val)


def _fmt_date(s):
    if not s or len(s) < 10:
        return s or '—'
    try:
        y, m, d = s[:10].split('-')
        return f"{d}/{m}/{y}"
    except Exception:
        return s


_QUALITE_FIELDS = [
    ('qualite_isolation_enveloppe', 'Enveloppe'),
    ('qualite_isolation_murs', 'Murs'),
    ('qualite_isolation_menuiseries', 'Menuiseries / Fenêtres'),
    ('qualite_isolation_plancher_bas', 'Plancher bas'),
    ('qualite_isolation_plancher_haut_comble_amenage', 'Plancher haut / Combles'),
]


class ReportDpe(models.AbstractModel):
    _name = 'report.ibatix_dpe.report_dpe_document'
    _description = 'Rapport DPE PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        partners = self.env['res.partner'].browse(docids)
        docs = []

        for partner in partners:
            dpe = {}
            if partner.dpe_data_json:
                try:
                    dpe = json.loads(partner.dpe_data_json)
                except Exception:
                    pass

            etiquette = (dpe.get('etiquette_dpe') or '').upper()
            etiquette_ges = (dpe.get('etiquette_ges') or '').upper()

            qualite = [
                {
                    'label': label,
                    'value': (dpe.get(field) or 'N/D').capitalize(),
                    'style': _qualite_style(dpe.get(field, '')),
                }
                for field, label in _QUALITE_FIELDS
                if dpe.get(field)
            ]

            # Consommations par usage
            usages = []
            for code, label in [
                ('chauffage', 'Chauffage'),
                ('ecs', 'Eau chaude sanitaire'),
                ('eclairage', 'Éclairage'),
                ('auxiliaires', 'Auxiliaires'),
            ]:
                ef = dpe.get(f'conso_{code}_ef') or dpe.get(f'conso_{code}_ef_energie_n1')
                ep = dpe.get(f'conso_{code}_ep') or dpe.get(f'conso_{code}_ep_energie_n1')
                ges = dpe.get(f'emission_ges_{code}')
                cout = dpe.get(f'cout_{code}') or dpe.get(f'cout_{code}_energie_n1')
                if ef or ep:
                    usages.append({
                        'label': label,
                        'ef': _fmt(ef),
                        'ep': _fmt(ep),
                        'ges': _fmt(ges),
                        'cout': _fmt(cout),
                    })

            # Déperditions
            deperditions = []
            for field, label in [
                ('deperditions_murs', 'Murs'),
                ('deperditions_baies_vitrees', 'Baies vitrées'),
                ('deperditions_planchers_bas', 'Planchers bas'),
                ('deperditions_planchers_hauts', 'Planchers hauts / Toiture'),
                ('deperditions_portes', 'Portes'),
                ('deperditions_ponts_thermiques', 'Ponts thermiques'),
                ('deperditions_renouvellement_air', 'Renouvellement d\'air'),
            ]:
                val = dpe.get(field)
                if val:
                    deperditions.append({'label': label, 'value': _fmt(val, 1), 'unit': 'W/K'})

            docs.append({
                'partner': partner,
                'dpe': dpe,
                'scale_energie': _build_scale(etiquette, _ENERGIE_RANGES),
                'scale_ges': _build_scale(etiquette_ges, _GES_RANGES),
                'dpe_color': _DPE_COLORS.get(etiquette, '#94A3B8'),
                'ges_color': _DPE_COLORS.get(etiquette_ges, '#94A3B8'),
                'dpe_text_color': _DPE_TEXT.get(etiquette, '#333'),
                'ges_text_color': _DPE_TEXT.get(etiquette_ges, '#333'),
                'is_passoire': etiquette in ('F', 'G'),
                'qualite': qualite,
                'usages': usages,
                'deperditions': deperditions,
                # Valeurs formatées
                'conso_ep': _fmt(dpe.get('conso_5_usages_par_m2_ep')),
                'conso_ef': _fmt(dpe.get('conso_5_usages_par_m2_ef')),
                'emission_ges': _fmt(dpe.get('emission_ges_5_usages_par_m2')),
                'cout_total': _fmt(dpe.get('cout_total_5_usages')),
                'surface': _fmt(dpe.get('surface_habitable_logement'), 1),
                'surface_immeuble': _fmt(dpe.get('surface_habitable_immeuble'), 1),
                'ubat': _fmt(dpe.get('ubat_w_par_m2_k'), 2),
                'hauteur_plafond': _fmt(dpe.get('hauteur_sous_plafond'), 1),
                'date_dpe': _fmt_date(dpe.get('date_etablissement_dpe', '')),
                'date_validite': _fmt_date(dpe.get('date_fin_validite_dpe', '')),
                'date_visite': _fmt_date(dpe.get('date_visite_diagnostiqueur', '')),
                'besoin_chauffage': _fmt(dpe.get('besoin_chauffage'), 1),
                'besoin_ecs': _fmt(dpe.get('besoin_ecs'), 1),
                'apport_solaire': _fmt(dpe.get('apport_solaire_saison_chauffe'), 1),
                'apport_interne': _fmt(dpe.get('apport_interne_saison_chauffe'), 1),
            })

        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': docs,
        }
