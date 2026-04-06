from odoo import models, fields, api
from datetime import timedelta


class SmartBenchmark(models.Model):
    _name = 'smartfinance.benchmark'
    _description = 'Smart Benchmarking'
    _order = 'status asc'

    name = fields.Char(string='KPI Name', required=True)
    category = fields.Selection([
        ('invoicing', 'Invoicing'),
        ('cashflow', 'Cash Flow'),
        ('crm', 'CRM & Sales'),
        ('hr', 'Workforce'),
        ('expenses', 'Expenses'),
    ], string='Category')
    your_value = fields.Float(string='Your Value')
    benchmark_value = fields.Float(string='Industry Benchmark')
    unit = fields.Char(string='Unit', default='')
    variance = fields.Float(string='Variance (%)', compute='_compute_variance', store=True)
    status = fields.Selection([
        ('outperforming', 'Outperforming ✅'),
        ('on_track', 'On Track 🟡'),
        ('needs_attention', 'Needs Attention ⚠️'),
        ('critical', 'Critical 🔴'),
    ], string='Status')
    higher_is_better = fields.Boolean(string='Higher is Better', default=True)
    interpretation = fields.Text(string='What This Means')
    recommended_action = fields.Text(string='Recommended Action')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.depends('your_value', 'benchmark_value')
    def _compute_variance(self):
        for rec in self:
            if rec.benchmark_value and rec.benchmark_value != 0:
                rec.variance = ((rec.your_value - rec.benchmark_value) / rec.benchmark_value) * 100
            else:
                rec.variance = 0

    def _get_status(self, your_value, benchmark, higher_is_better):
        """Determine status based on variance from benchmark."""
        if benchmark == 0:
            return 'on_track'
        variance_pct = ((your_value - benchmark) / benchmark) * 100
        if higher_is_better:
            if variance_pct >= 10:
                return 'outperforming'
            elif variance_pct >= -10:
                return 'on_track'
            elif variance_pct >= -25:
                return 'needs_attention'
            else:
                return 'critical'
        else:
            if variance_pct <= -10:
                return 'outperforming'
            elif variance_pct <= 10:
                return 'on_track'
            elif variance_pct <= 25:
                return 'needs_attention'
            else:
                return 'critical'

    @api.model
    def run_benchmarking(self):
        """Collect live data and compare against industry benchmarks."""
        # Delete old benchmarks
        self.search([]).unlink()

        today = fields.Date.today()
        thirty_days_ago = today - timedelta(days=30)

        # ── 1. INVOICE COLLECTION PERIOD ──────────────────────────────
        paid_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['paid', 'in_payment']),
        ])
        if paid_invoices:
            collection_days = []
            for inv in paid_invoices:
                if inv.invoice_date and inv.invoice_date_due:
                    days = (inv.invoice_date_due - inv.invoice_date).days
                    if days > 0:
                        collection_days.append(days)
            avg_collection = sum(collection_days) / len(collection_days) if collection_days else 45
        else:
            avg_collection = 45

        benchmark_collection = 30
        status = self._get_status(avg_collection, benchmark_collection, higher_is_better=False)
        self.create({
            'name': 'Invoice Collection Period',
            'category': 'invoicing',
            'your_value': round(avg_collection, 1),
            'benchmark_value': benchmark_collection,
            'unit': 'days',
            'status': status,
            'higher_is_better': False,
            'interpretation': (
                f'Your average invoice collection period is {avg_collection:.0f} days. '
                f'Industry benchmark is {benchmark_collection} days. '
                f'{"You are collecting faster than average — excellent!" if avg_collection <= benchmark_collection else "You are collecting slower than industry average."}'
            ),
            'recommended_action': (
                'Set up automatic payment reminders at 7, 14, and 30 days. '
                'Offer early payment discounts to incentivize faster collection.'
                if avg_collection > benchmark_collection else
                'Maintain your current collection process — it is performing well.'
            ),
        })

        # ── 2. CRM WIN RATE ───────────────────────────────────────────
        all_opps = self.env['crm.lead'].search([('type', '=', 'opportunity')])
        won_opps = all_opps.filtered(lambda o: o.stage_id.is_won)
        win_rate = (len(won_opps) / len(all_opps) * 100) if all_opps else 0
        benchmark_win_rate = 20

        status = self._get_status(win_rate, benchmark_win_rate, higher_is_better=True)
        self.create({
            'name': 'CRM Win Rate',
            'category': 'crm',
            'your_value': round(win_rate, 1),
            'benchmark_value': benchmark_win_rate,
            'unit': '%',
            'status': status,
            'higher_is_better': True,
            'interpretation': (
                f'Your CRM win rate is {win_rate:.1f}%. '
                f'Industry benchmark is {benchmark_win_rate}%. '
                f'{"You are outperforming industry average!" if win_rate >= benchmark_win_rate else "Your win rate is below industry average."}'
            ),
            'recommended_action': (
                'Maintain your qualification process — your win rate is strong.'
                if win_rate >= benchmark_win_rate else
                'Review lost deals for common reasons. '
                'Improve lead qualification at early stages to focus on better prospects.'
            ),
        })

        # ── 3. OVERDUE INVOICE RATE ───────────────────────────────────
        all_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ])
        overdue = all_invoices.filtered(
            lambda inv: inv.payment_state not in ['paid', 'reversed', 'in_payment']
            and inv.invoice_date_due and inv.invoice_date_due < today
        )
        overdue_rate = (len(overdue) / len(all_invoices) * 100) if all_invoices else 0
        benchmark_overdue = 10

        status = self._get_status(overdue_rate, benchmark_overdue, higher_is_better=False)
        self.create({
            'name': 'Overdue Invoice Rate',
            'category': 'invoicing',
            'your_value': round(overdue_rate, 1),
            'benchmark_value': benchmark_overdue,
            'unit': '%',
            'status': status,
            'higher_is_better': False,
            'interpretation': (
                f'{overdue_rate:.1f}% of your invoices are overdue. '
                f'Industry benchmark is below {benchmark_overdue}%. '
                f'{"Your overdue rate is within acceptable range." if overdue_rate <= benchmark_overdue else "Your overdue rate exceeds industry benchmark."}'
            ),
            'recommended_action': (
                'Your overdue rate is healthy. Keep sending timely payment reminders.'
                if overdue_rate <= benchmark_overdue else
                'Implement stricter credit terms for repeat late payers. '
                'Consider requiring deposits from high-risk customers.'
            ),
        })

        # ── 4. CASH FLOW RATIO ────────────────────────────────────────
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
        cash_ratio = (total_inflow / total_outflow) if total_outflow > 0 else (1.5 if total_inflow > 0 else 1.0)
        benchmark_cash_ratio = 1.2

        status = self._get_status(cash_ratio, benchmark_cash_ratio, higher_is_better=True)
        self.create({
            'name': 'Cash Flow Ratio (Inflow/Outflow)',
            'category': 'cashflow',
            'your_value': round(cash_ratio, 2),
            'benchmark_value': benchmark_cash_ratio,
            'unit': 'x',
            'status': status,
            'higher_is_better': True,
            'interpretation': (
                f'For every AED 1 spent, you collect AED {cash_ratio:.2f}. '
                f'Industry benchmark is {benchmark_cash_ratio}x. '
                f'{"Your cash flow ratio is healthy." if cash_ratio >= benchmark_cash_ratio else "Your cash inflow does not sufficiently exceed outflow."}'
            ),
            'recommended_action': (
                'Your cash flow ratio is strong. Maintain current payment and collection cycles.'
                if cash_ratio >= benchmark_cash_ratio else
                'Accelerate collections and delay non-critical payments to improve ratio.'
            ),
        })

        # ── 5. EMPLOYEE COUNT VS REVENUE ─────────────────────────────
        employees = self.env['hr.employee'].search([('active', '=', True)])
        total_revenue = sum(self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', today.replace(month=1, day=1)),
        ]).mapped('amount_total'))

        revenue_per_employee = (total_revenue / len(employees)) if employees else 0
        benchmark_revenue_per_employee = 200000

        status = self._get_status(
            revenue_per_employee, benchmark_revenue_per_employee, higher_is_better=True
        )
        self.create({
            'name': 'Revenue per Employee (AED)',
            'category': 'hr',
            'your_value': round(revenue_per_employee, 0),
            'benchmark_value': benchmark_revenue_per_employee,
            'unit': 'AED',
            'status': status,
            'higher_is_better': True,
            'interpretation': (
                f'Each employee generates AED {revenue_per_employee:,.0f} in revenue. '
                f'Industry benchmark is AED {benchmark_revenue_per_employee:,.0f} per employee. '
                f'{"Your team is highly productive!" if revenue_per_employee >= benchmark_revenue_per_employee else "Revenue per employee is below industry benchmark."}'
            ),
            'recommended_action': (
                'Your team productivity is excellent. Consider strategic hiring to scale.'
                if revenue_per_employee >= benchmark_revenue_per_employee else
                'Focus on revenue growth before expanding headcount. '
                'Review whether current staff are optimally utilized.'
            ),
        })

        # ── 6. EXPENSE RATIO ─────────────────────────────────────────
        total_expenses = sum(self.env['hr.expense'].search([
            ('state', 'in', ['approved', 'done']),
            ('date', '>=', today.replace(month=1, day=1)),
        ]).mapped('total_amount'))

        expense_ratio = (total_expenses / total_revenue * 100) if total_revenue > 0 else 0
        benchmark_expense_ratio = 15

        status = self._get_status(expense_ratio, benchmark_expense_ratio, higher_is_better=False)
        self.create({
            'name': 'Expense to Revenue Ratio',
            'category': 'expenses',
            'your_value': round(expense_ratio, 1),
            'benchmark_value': benchmark_expense_ratio,
            'unit': '%',
            'status': status,
            'higher_is_better': False,
            'interpretation': (
                f'Your expenses represent {expense_ratio:.1f}% of revenue. '
                f'Industry benchmark is below {benchmark_expense_ratio}%. '
                f'{"Your expense ratio is within healthy range." if expense_ratio <= benchmark_expense_ratio else "Your expenses are high relative to revenue."}'
            ),
            'recommended_action': (
                'Your expense ratio is healthy. Continue monitoring monthly.'
                if expense_ratio <= benchmark_expense_ratio else
                'Review discretionary expenses. '
                'Set department expense budgets and track monthly variances.'
            ),
        })

        return True