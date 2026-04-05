from odoo import models, fields, api
from datetime import timedelta
import json


class KPIDashboard(models.Model):
    _name = 'smartfinance.kpi'
    _description = 'KPI Dashboard'

    name = fields.Char(default='KPI Dashboard')

    # Computed KPI fields
    total_overdue = fields.Float(string='Overdue Invoices (AED)', compute='_compute_kpis')
    overdue_count = fields.Integer(string='Overdue Count', compute='_compute_kpis')
    total_inflow = fields.Float(string='Cash Inflow (AED)', compute='_compute_kpis')
    total_outflow = fields.Float(string='Cash Outflow (AED)', compute='_compute_kpis')
    net_cash = fields.Float(string='Net Cash (AED)', compute='_compute_kpis')
    employee_count = fields.Integer(string='Active Employees', compute='_compute_kpis')
    open_opportunities = fields.Integer(string='Open Deals', compute='_compute_kpis')
    pipeline_value = fields.Float(string='Pipeline Value (AED)', compute='_compute_kpis')
    health_score = fields.Float(string='Health Score', compute='_compute_kpis')
    chart_data = fields.Text(string='Chart Data JSON', compute='_compute_kpis')

    @api.depends()
    def _compute_kpis(self):
        for rec in self:
            today = fields.Date.today()
            thirty_days_ago = today - timedelta(days=30)

            # Overdue invoices
            overdue = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ['paid', 'reversed', 'in_payment']),
                ('invoice_date_due', '<', today),
            ])
            rec.total_overdue = sum(overdue.mapped('amount_residual'))
            rec.overdue_count = len(overdue)

            # Cash flow
            inbound = self.env['account.payment'].search([
                ('payment_type', '=', 'inbound'),
                ('date', '>=', thirty_days_ago),
                ('state', '=', 'posted'),
            ])
            outbound = self.env['account.payment'].search([
                ('payment_type', '=', 'outbound'),
                ('date', '>=', thirty_days_ago),
                ('state', '=', 'posted'),
            ])
            rec.total_inflow = sum(inbound.mapped('amount'))
            rec.total_outflow = sum(outbound.mapped('amount'))
            rec.net_cash = rec.total_inflow - rec.total_outflow

            # Employees
            employees = self.env['hr.employee'].search([('active', '=', True)])
            rec.employee_count = len(employees)

            # CRM
            opps = self.env['crm.lead'].search([('type', '=', 'opportunity')])
            rec.open_opportunities = len(opps)
            rec.pipeline_value = sum(opps.mapped('expected_revenue'))

            # Health score
            health = self.env['smartfinance.health.score'].search(
                [], limit=1, order='date desc'
            )
            rec.health_score = health.overall_score if health else 0

            # Chart data for last 6 months invoices
            months = []
            for i in range(5, -1, -1):
                month_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1)
                invoices = self.env['account.move'].search([
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', month_start),
                    ('invoice_date', '<', month_end),
                ])
                months.append({
                    'month': month_start.strftime('%b %Y'),
                    'amount': sum(invoices.mapped('amount_total')),
                })
            rec.chart_data = json.dumps(months)

    @api.model
    def get_dashboard_data(self):
        """Called by the dashboard view to get all KPI data."""
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({'name': 'Main Dashboard'})
        return {
            'total_overdue': rec.total_overdue,
            'overdue_count': rec.overdue_count,
            'total_inflow': rec.total_inflow,
            'total_outflow': rec.total_outflow,
            'net_cash': rec.net_cash,
            'employee_count': rec.employee_count,
            'open_opportunities': rec.open_opportunities,
            'pipeline_value': rec.pipeline_value,
            'health_score': rec.health_score,
            'chart_data': rec.chart_data,
        }