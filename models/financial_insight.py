from odoo import models, fields, api
from datetime import datetime, timedelta
import json


class FinancialInsight(models.Model):
    _name = 'smartfinance.insight'
    _description = 'AI Financial Insight'
    _order = 'severity desc, create_date desc'

    name = fields.Char(string='Insight Title', required=True)
    description = fields.Text(string='AI Analysis')
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Severity', default='low')
    category = fields.Selection([
        ('cashflow', 'Cash Flow'),
        ('invoicing', 'Invoicing'),
        ('expenses', 'Expenses'),
        ('crm', 'CRM Pipeline'),
        ('hr', 'Workforce'),
        ('purchase', 'Purchasing'),
    ], string='Category')
    value = fields.Float(string='Metric Value')
    recommended_action = fields.Text(string='Recommended Action')
    is_resolved = fields.Boolean(string='Resolved', default=False)
    resolved_date = fields.Datetime(string='Resolved On')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    def mark_resolved(self):
        self.write({
            'is_resolved': True,
            'resolved_date': fields.Datetime.now(),
        })


class FinancialHealthScore(models.Model):
    _name = 'smartfinance.health.score'
    _description = 'Business Financial Health Score'
    _order = 'date desc'

    date = fields.Date(
        string='Date',
        default=fields.Date.today
    )
    overall_score = fields.Float(string='Overall Score (0-100)')
    cashflow_score = fields.Float(string='Cash Flow Score')
    invoicing_score = fields.Float(string='Invoicing Score')
    hr_score = fields.Float(string='Workforce Score')
    crm_score = fields.Float(string='CRM Score')
    purchase_score = fields.Float(string='Purchase Score')
    score_breakdown = fields.Text(string='Score Breakdown JSON')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.model
    def compute_health_score(self):
        """
        Core AI scoring engine.
        Reads live data from accounting, HR, CRM, expenses, and purchases.
        Returns a 0-100 composite health score.
        """
        scores = {}
        today = fields.Date.today()
        thirty_days_ago = today - timedelta(days=30)
        prev_thirty_start = thirty_days_ago - timedelta(days=30)

        # ── 1. CASH FLOW SCORE (weight: 35%) ──────────────────────────────
        # Ratio of inbound vs outbound payments in last 30 days
        inbound_payments = self.env['account.payment'].search([
            ('payment_type', '=', 'inbound'),
            ('date', '>=', thirty_days_ago),
            ('state', 'in', ['posted', 'in_process', 'paid']),
        ])
        outbound_payments = self.env['account.payment'].search([
            ('payment_type', '=', 'outbound'),
            ('date', '>=', thirty_days_ago),
            ('state', 'in', ['posted', 'in_process', 'paid']),
        ])
        total_inflow = sum(inbound_payments.mapped('amount'))
        total_outflow = sum(outbound_payments.mapped('amount'))

        if total_inflow > 0:
            ratio = total_inflow / max(total_outflow, 1)
            # ratio >= 2 = perfect score, ratio = 1 = 50, ratio < 0.5 = low
            scores['cashflow'] = round(min(ratio * 50, 100), 1)
        else:
            scores['cashflow'] = 20.0  # No inflow is a bad sign

        # ── 2. INVOICING SCORE (weight: 30%) ──────────────────────────────
        # Penalise for overdue invoices as a percentage of total
        all_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', 'in', ['posted', 'in_process', 'paid']),
        ])
        overdue_invoices = all_invoices.filtered(
            lambda inv: (
                inv.payment_state not in ('paid', 'reversed', 'in_payment')
                and inv.invoice_date_due
                and inv.invoice_date_due < today
            )
        )
        if all_invoices:
            overdue_rate = len(overdue_invoices) / len(all_invoices)
            scores['invoicing'] = round(max(100 - (overdue_rate * 150), 0), 1)
        else:
            scores['invoicing'] = 50.0  # No invoices yet — neutral

        # ── 3. WORKFORCE / HR SCORE (weight: 20%) ─────────────────────────
        # Check employee records completeness — job position, work email set
        employees = self.env['hr.employee'].search([('active', '=', True)])
        if employees:
            complete = employees.filtered(
                lambda e: e.job_id and e.work_email
            )
            scores['hr'] = round((len(complete) / len(employees)) * 100, 1)
        else:
            scores['hr'] = 50.0

        # ── 4. CRM PIPELINE SCORE (weight: 10%) ───────────────────────────
        # Based on win rate of opportunities
        opportunities = self.env['crm.lead'].search([
            ('type', '=', 'opportunity'),
        ])
        won = opportunities.filtered(lambda o: o.stage_id.is_won)
        if opportunities:
            win_rate = len(won) / len(opportunities)
            # 50% win rate = 100 score
            scores['crm'] = round(min(win_rate * 200, 100), 1)
        else:
            scores['crm'] = 50.0

        # ── 5. PURCHASE SCORE (weight: 5%) ────────────────────────────────
        # Penalise for purchase orders without a vendor bill
        purchase_orders = self.env['purchase.order'].search([
            ('state', 'in', ('purchase', 'done')),
            ('date_approve', '>=', thirty_days_ago),
        ])
        unbilled = purchase_orders.filtered(
            lambda po: po.invoice_status == 'to invoice'
        )
        if purchase_orders:
            unbilled_rate = len(unbilled) / len(purchase_orders)
            scores['purchase'] = round(max(100 - (unbilled_rate * 100), 0), 1)
        else:
            scores['purchase'] = 100.0

        # ── COMPOSITE SCORE ────────────────────────────────────────────────
        overall = (
            scores.get('cashflow', 0) * 0.35 +
            scores.get('invoicing', 0) * 0.30 +
            scores.get('hr', 0) * 0.20 +
            scores.get('crm', 0) * 0.10 +
            scores.get('purchase', 0) * 0.05
        )

        record = self.create({
            'overall_score': round(overall, 1),
            'cashflow_score': scores.get('cashflow', 0),
            'invoicing_score': scores.get('invoicing', 0),
            'hr_score': scores.get('hr', 0),
            'crm_score': scores.get('crm', 0),
            'purchase_score': scores.get('purchase', 0),
            'score_breakdown': json.dumps(scores, indent=2),
        })
        return record