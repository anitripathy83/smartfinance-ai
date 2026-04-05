from odoo import models, fields, api
from datetime import timedelta


class InsightEngine(models.Model):
    _name = 'smartfinance.engine'
    _description = 'AI Insight Generation Engine'

    @api.model
    def run_daily_analysis(self):
        self._analyze_overdue_invoices()
        self._analyze_cashflow_trend()
        self._analyze_expense_anomalies()
        self._analyze_crm_pipeline_health()
        self._analyze_purchase_orders()
        self._analyze_hr_workforce()
        self.env['smartfinance.health.score'].compute_health_score()

    def _analyze_overdue_invoices(self):
        today = fields.Date.today()
        overdue = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ['paid', 'reversed', 'in_payment']),
            ('invoice_date_due', '<', today),
        ])
        if not overdue:
            return
        total_overdue = sum(overdue.mapped('amount_residual'))
        oldest_date = min(overdue.mapped('invoice_date_due'))
        days_oldest = (today - oldest_date).days
        if total_overdue > 50000:
            severity = 'critical'
        elif total_overdue > 20000:
            severity = 'high'
        elif total_overdue > 5000:
            severity = 'medium'
        else:
            severity = 'low'
        self.env['smartfinance.insight'].create({
            'name': f'{len(overdue)} overdue invoice(s) — AED {total_overdue:,.0f} outstanding',
            'description': (
                f'You have {len(overdue)} customer invoice(s) past their due date.\n\n'
                f'Total outstanding: AED {total_overdue:,.2f}\n'
                f'Oldest overdue: {days_oldest} days past due'
            ),
            'severity': severity,
            'category': 'invoicing',
            'value': total_overdue,
            'recommended_action': (
                '1. Go to Accounting > Customers > Invoices and filter by Overdue.\n'
                '2. Send payment reminders to all overdue customers.\n'
                '3. Call customers overdue by more than 30 days.'
            ),
        })

    def _analyze_cashflow_trend(self):
        today = fields.Date.today()
        last_30 = today - timedelta(days=30)
        prev_30 = last_30 - timedelta(days=30)

        def get_inflow(date_from, date_to):
            payments = self.env['account.payment'].search([
                ('payment_type', '=', 'inbound'),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('state', '=', 'posted'),
            ])
            return sum(payments.mapped('amount'))

        def get_outflow(date_from, date_to):
            payments = self.env['account.payment'].search([
                ('payment_type', '=', 'outbound'),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('state', '=', 'posted'),
            ])
            return sum(payments.mapped('amount'))

        current_inflow = get_inflow(last_30, today)
        previous_inflow = get_inflow(prev_30, last_30)
        current_outflow = get_outflow(last_30, today)

        if previous_inflow > 0:
            change_pct = ((current_inflow - previous_inflow) / previous_inflow) * 100
            if change_pct < -20:
                severity = 'critical' if change_pct < -40 else 'high'
                self.env['smartfinance.insight'].create({
                    'name': f'Cash inflow dropped {abs(change_pct):.0f}% vs last month',
                    'description': (
                        f'Incoming payments this month: AED {current_inflow:,.0f}\n'
                        f'Previous month: AED {previous_inflow:,.0f}\n'
                        f'Change: {change_pct:.1f}%'
                    ),
                    'severity': severity,
                    'category': 'cashflow',
                    'value': change_pct,
                    'recommended_action': (
                        '1. Review your CRM pipeline for stalled deals.\n'
                        '2. Accelerate collection on outstanding invoices.\n'
                        '3. Check if major recurring customers have not paid this month.'
                    ),
                })

        if current_inflow > 0 and current_outflow > current_inflow * 1.2:
            self.env['smartfinance.insight'].create({
                'name': f'Outflow exceeds inflow — AED {current_outflow - current_inflow:,.0f} deficit',
                'description': (
                    f'Inflow: AED {current_inflow:,.0f}\n'
                    f'Outflow: AED {current_outflow:,.0f}\n'
                    f'Net position: AED {current_inflow - current_outflow:,.0f}'
                ),
                'severity': 'high',
                'category': 'cashflow',
                'value': current_outflow - current_inflow,
                'recommended_action': (
                    '1. Delay non-critical vendor payments if possible.\n'
                    '2. Chase overdue customer invoices immediately.'
                ),
            })

    def _analyze_expense_anomalies(self):
        today = fields.Date.today()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

        current_expenses = self.env['hr.expense'].search([
            ('date', '>=', this_month_start),
            ('state', 'in', ['approved', 'done']),
        ])
        last_expenses = self.env['hr.expense'].search([
            ('date', '>=', last_month_start),
            ('date', '<', this_month_start),
            ('state', 'in', ['approved', 'done']),
        ])

        current_total = sum(current_expenses.mapped('total_amount'))
        last_total = sum(last_expenses.mapped('total_amount'))

        if last_total > 0 and current_total > last_total * 1.5:
            spike_pct = ((current_total / last_total) - 1) * 100
            self.env['smartfinance.insight'].create({
                'name': f'Employee expenses up {spike_pct:.0f}% this month',
                'description': (
                    f'This month: AED {current_total:,.0f}\n'
                    f'Last month: AED {last_total:,.0f}\n'
                    f'Increase: {spike_pct:.1f}%'
                ),
                'severity': 'medium' if spike_pct < 100 else 'high',
                'category': 'expenses',
                'value': current_total,
                'recommended_action': (
                    '1. Review expense reports for unusual items.\n'
                    '2. Check if the spike is project-related or anomalous.'
                ),
            })

    def _analyze_crm_pipeline_health(self):
        today = fields.Date.today()
        stale_threshold = today - timedelta(days=14)

        stale_opps = self.env['crm.lead'].search([
            ('type', '=', 'opportunity'),
            ('active', '=', True),
            ('stage_id.is_won', '=', False),
            ('write_date', '<=', stale_threshold),
        ])

        if len(stale_opps) >= 3:
            total_value = sum(stale_opps.mapped('expected_revenue'))
            self.env['smartfinance.insight'].create({
                'name': f'{len(stale_opps)} deals stale for 14+ days — AED {total_value:,.0f} at risk',
                'description': (
                    f'{len(stale_opps)} CRM opportunities not updated in over 2 weeks.\n'
                    f'Total pipeline value at risk: AED {total_value:,.0f}'
                ),
                'severity': 'medium',
                'category': 'crm',
                'value': total_value,
                'recommended_action': (
                    '1. Go to CRM > Pipeline and filter by last activity.\n'
                    '2. Contact each stale opportunity immediately.\n'
                    '3. Move dead deals to Lost to keep pipeline accurate.'
                ),
            })

        all_opps = self.env['crm.lead'].search([('type', '=', 'opportunity')])
        won_opps = all_opps.filtered(lambda o: o.stage_id.is_won)

        if len(all_opps) >= 5:
            win_rate = (len(won_opps) / len(all_opps)) * 100
            if win_rate < 20:
                self.env['smartfinance.insight'].create({
                    'name': f'CRM win rate is only {win_rate:.1f}%',
                    'description': (
                        f'Win rate: {win_rate:.1f}% (below 20% benchmark)\n'
                        f'Total opportunities: {len(all_opps)}\n'
                        f'Won: {len(won_opps)}'
                    ),
                    'severity': 'medium',
                    'category': 'crm',
                    'value': win_rate,
                    'recommended_action': (
                        '1. Review lost deals for common reasons.\n'
                        '2. Improve qualification at early pipeline stages.'
                    ),
                })

    def _analyze_purchase_orders(self):
        today = fields.Date.today()
        thirty_days_ago = today - timedelta(days=30)

        unbilled_pos = self.env['purchase.order'].search([
            ('state', 'in', ('purchase', 'done')),
            ('invoice_status', '=', 'to invoice'),
            ('date_approve', '>=', thirty_days_ago),
        ])

        if len(unbilled_pos) >= 2:
            total_value = sum(unbilled_pos.mapped('amount_total'))
            self.env['smartfinance.insight'].create({
                'name': f'{len(unbilled_pos)} purchase order(s) awaiting vendor bill — AED {total_value:,.0f}',
                'description': (
                    f'{len(unbilled_pos)} confirmed POs have not received a vendor bill.\n'
                    f'Total value: AED {total_value:,.2f}'
                ),
                'severity': 'low',
                'category': 'purchase',
                'value': total_value,
                'recommended_action': (
                    '1. Go to Purchase > Orders > Purchase Orders.\n'
                    '2. Filter by Billing Status = To Bill.\n'
                    '3. Follow up with vendors to send their invoices.'
                ),
            })

    def _analyze_hr_workforce(self):
        employees = self.env['hr.employee'].search([('active', '=', True)])

        incomplete = employees.filtered(
            lambda e: not e.job_id or not e.work_email or not e.department_id
        )

        if len(incomplete) >= 2:
            self.env['smartfinance.insight'].create({
                'name': f'{len(incomplete)} employee profile(s) incomplete',
                'description': (
                    f'{len(incomplete)} of {len(employees)} active employees '
                    f'are missing job position, work email, or department.'
                ),
                'severity': 'low',
                'category': 'hr',
                'value': len(incomplete),
                'recommended_action': (
                    '1. Go to Employees and complete each profile.\n'
                    '2. Ensure Job Position, Work Email, and Department are filled.'
                ),
            })

        departments = self.env['hr.department'].search([('active', '=', True)])
        no_manager = departments.filtered(lambda d: not d.manager_id)

        if no_manager:
            self.env['smartfinance.insight'].create({
                'name': f'{len(no_manager)} department(s) have no manager assigned',
                'description': (
                    f'Departments without managers:\n'
                    + '\n'.join(f'  - {d.name}' for d in no_manager)
                ),
                'severity': 'medium',
                'category': 'hr',
                'value': len(no_manager),
                'recommended_action': (
                    '1. Go to Employees > Departments.\n'
                    '2. Edit each department and assign a manager.'
                ),
            })