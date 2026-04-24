import json
import urllib.error
import urllib.parse
import urllib.request

from odoo import _, fields, models
from odoo.exceptions import UserError

_DPE_DATASET = 'meg-83tjwtg8dyz4vv7h1dqe'
_DPE_API = f'https://data.ademe.fr/data-fair/api/v1/datasets/{_DPE_DATASET}/lines'


class ResPartnerDpe(models.Model):
    _inherit = 'res.partner'

    dpe_data_json = fields.Text(string='Données DPE (JSON)')
    dpe_numero = fields.Char(string='N° DPE', readonly=True)
    dpe_etiquette = fields.Char(string='Classe DPE', readonly=True)
    dpe_etiquette_ges = fields.Char(string='Classe GES', readonly=True)
    dpe_date = fields.Char(string='Date DPE', readonly=True)

    def action_rechercher_dpe(self):
        self.ensure_one()
        address = ' '.join(p for p in [self.street, self.zip, self.city] if p)
        if not address.strip():
            raise UserError(_("Veuillez renseigner l'adresse du client avant de rechercher son DPE."))

        params = urllib.parse.urlencode({
            'q': address,
            'size': 10,
            'sort': '-date_etablissement_dpe',
        })
        try:
            req = urllib.request.Request(
                f'{_DPE_API}?{params}',
                headers={'Accept': 'application/json'},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except urllib.error.URLError as e:
            raise UserError(_("Impossible de contacter l'API DPE ADEME : %s") % str(e))

        results = data.get('results', [])
        if not results:
            raise UserError(_(
                "Aucun DPE trouvé pour l'adresse : %s\n"
                "Vérifiez que l'adresse est correcte et complète (n°, rue, CP, ville)."
            ) % address)

        lines = [(0, 0, {
            'numero_dpe': r.get('numero_dpe', ''),
            'adresse': r.get('adresse_ban') or r.get('adresse_brut', ''),
            'etiquette_dpe': r.get('etiquette_dpe', ''),
            'etiquette_ges': r.get('etiquette_ges', ''),
            'conso_ep': r.get('conso_5_usages_par_m2_ep') or 0.0,
            'surface': r.get('surface_habitable_logement') or 0.0,
            'date_dpe': r.get('date_etablissement_dpe', ''),
            'type_batiment': (r.get('type_batiment') or '').capitalize(),
            'periode_construction': r.get('periode_construction', ''),
            'dpe_data_json': json.dumps(r, ensure_ascii=False),
        }) for r in results]

        wizard = self.env['ibatix.wizard.dpe'].create({
            'partner_id': self.id,
            'line_ids': lines,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _("%d DPE trouvé(s) — Sélectionnez le bon logement") % len(results),
            'res_model': 'ibatix.wizard.dpe',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_regenerer_dpe_pdf(self):
        self.ensure_one()
        if not self.dpe_data_json:
            raise UserError(_("Aucune donnée DPE enregistrée. Veuillez d'abord rechercher un DPE."))
        return self.env.ref('ibatix_dpe.action_report_dpe').report_action(self)
