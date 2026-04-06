from odoo import models, fields, api
from datetime import timedelta


class FinancialReport(models.Model):
    _name = 'smartfinance.report'
    _description = 'One-Click Financial Report'

    name = fields.Char(string='Report Name', default='Financial Summary Report')
    date_generated = fields.Datetime(string='Generated On', default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # Report data fields
    total_overdue = fields.Float(string='Total Overdue (AED)')
    overdue_count = fields.Integer(string='Overdue Invoice Count')
    total_inflow = fields.Float(string='Cash Inflow (AED)')
    total_outflow = fields.Float(string='Cash Outflow (AED)')
    net_cash = fields.Float(string='Net Cash Position (AED)')
    employee_count = fields.Integer(string='Active Employees')
    open_opportunities = fields.Integer(string='Open CRM Deals')
    pipeline_value = fields.Float(string='Pipeline Value (AED)')
    health_score = fields.Float(string='Health Score')
    insights_critical = fields.Integer(string='Critical Alerts')
    insights_high = fields.Integer(string='High Alerts')
    insights_medium = fields.Integer(string='Medium Alerts')
    report_notes = fields.Text(string='Executive Summary')

    @api.model
    def generate_report(self):
        """Collect all live data and create a report record."""
        today = fields.Date.today()
        thirty_days_ago = today - timedelta(days=30)

        # Overdue invoices
        overdue = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', 'in', ['posted', 'in_process', 'paid']),
            ('payment_state', 'not in', ['paid', 'reversed', 'in_payment']),
            ('invoice_date_due', '<', today),
        ])
        total_overdue = sum(overdue.mapped('amount_residual'))

        # Cash flow
        inbound = self.env['account.payment'].search([
            ('payment_type', '=', 'inbound'),
            ('date', '>=', thirty_days_ago),
            ('state', 'in', ['posted', 'in_process', 'paid']),
        ])
        outbound = self.env['account.payment'].search([
            ('payment_type', '=', 'outbound'),
            ('date', '>=', thirty_days_ago),
            ('state', 'in', ['posted', 'in_process', 'paid']),
        ])
        total_inflow = sum(inbound.mapped('amount'))
        total_outflow = sum(outbound.mapped('amount'))

        # Employees
        employees = self.env['hr.employee'].search([('active', '=', True)])

        # CRM
        opps = self.env['crm.lead'].search([('type', '=', 'opportunity')])
        pipeline_value = sum(opps.mapped('expected_revenue'))

        # Health score
        health = self.env['smartfinance.health.score'].search(
            [], limit=1, order='date desc'
        )

        # Insights by severity
        insights = self.env['smartfinance.insight'].search([
            ('is_resolved', '=', False)
        ])
        critical = len(insights.filtered(lambda i: i.severity == 'critical'))
        high = len(insights.filtered(lambda i: i.severity == 'high'))
        medium = len(insights.filtered(lambda i: i.severity == 'medium'))

        # Auto-generate executive summary
        net_cash = total_inflow - total_outflow
        summary_lines = []
        if total_overdue > 0:
            summary_lines.append(
                f"• URGENT: AED {total_overdue:,.0f} in overdue invoices requires immediate collection action."
            )
        if net_cash < 0:
            summary_lines.append(
                f"• Cash outflow exceeds inflow by AED {abs(net_cash):,.0f}. Review payment scheduling."
            )
        if critical > 0:
            summary_lines.append(
                f"• {critical} critical alert(s) detected requiring immediate management attention."
            )
        if pipeline_value > 0:
            summary_lines.append(
                f"• CRM pipeline stands at AED {pipeline_value:,.0f} across {len(opps)} open opportunities."
            )
        if not summary_lines:
            summary_lines.append("• All financial indicators are within healthy ranges.")

        summary = "\n".join(summary_lines)

        report = self.create({
            'name': f'Financial Report — {today.strftime("%B %d, %Y")}',
            'total_overdue': total_overdue,
            'overdue_count': len(overdue),
            'total_inflow': total_inflow,
            'total_outflow': total_outflow,
            'net_cash': net_cash,
            'employee_count': len(employees),
            'open_opportunities': len(opps),
            'pipeline_value': pipeline_value,
            'health_score': health.overall_score if health else 0,
            'insights_critical': critical,
            'insights_high': high,
            'insights_medium': medium,
            'report_notes': summary,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'smartfinance.report',
            'res_id': report.id,
            'view_mode': 'form',
            'target': 'current',
        }
