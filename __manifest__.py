{
    'name': 'DPE — Diagnostic de Performance Énergétique',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Recherche DPE par adresse (API ADEME), sélection et génération PDF attaché à la fiche client',
    'author': 'ibatix',
    'depends': ['base', 'contacts', 'ibatix_adresse'],
    'data': [
        'security/ir.model.access.csv',
        'report/report_dpe_actions.xml',
        'report/report_dpe_document.xml',
        'views/wizard_dpe_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
