from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizardDpe(models.TransientModel):
    _name = 'ibatix.wizard.dpe'
    _description = 'Sélection du DPE à attacher au partenaire'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    line_ids = fields.One2many('ibatix.wizard.dpe.line', 'wizard_id', string='DPE trouvés')
    nb_resultats = fields.Integer(compute='_compute_nb', string='Résultats')

    @api.depends('line_ids')
    def _compute_nb(self):
        for rec in self:
            rec.nb_resultats = len(rec.line_ids)

    def action_generer_pdf(self):
        self.ensure_one()
        selected = self.line_ids.filtered('selected')[:1]
        if not selected:
            raise UserError(_("Veuillez sélectionner un DPE dans la liste avant de générer le rapport."))

        self.partner_id.write({
            'dpe_data_json': selected.dpe_data_json,
            'dpe_numero': selected.numero_dpe,
            'dpe_etiquette': selected.etiquette_dpe,
            'dpe_etiquette_ges': selected.etiquette_ges,
            'dpe_date': selected.date_dpe,
        })
        return self.env.ref('ibatix_dpe.action_report_dpe').report_action(self.partner_id)


class WizardDpeLine(models.TransientModel):
    _name = 'ibatix.wizard.dpe.line'
    _description = 'Résultat DPE'

    wizard_id = fields.Many2one('ibatix.wizard.dpe', ondelete='cascade', required=True)
    selected = fields.Boolean(string='Choisir')
    numero_dpe = fields.Char(string='N° DPE', readonly=True)
    adresse = fields.Char(string='Adresse', readonly=True)
    etiquette_dpe = fields.Char(string='DPE', readonly=True)
    etiquette_ges = fields.Char(string='GES', readonly=True)
    conso_ep = fields.Float(string='kWh/m²/an', digits=(10, 0), readonly=True)
    surface = fields.Float(string='Surface m²', digits=(10, 1), readonly=True)
    date_dpe = fields.Char(string='Date', readonly=True)
    type_batiment = fields.Char(string='Type', readonly=True)
    periode_construction = fields.Char(string='Période', readonly=True)
    dpe_data_json = fields.Text()

    @api.onchange('selected')
    def _onchange_selected(self):
        if self.selected:
            for line in self.wizard_id.line_ids:
                if line != self:
                    line.selected = False
