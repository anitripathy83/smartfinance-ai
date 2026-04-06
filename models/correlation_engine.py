from odoo import models, fields, api
from datetime import timedelta, date
import math


class CorrelationEngine(models.Model):
    _name = 'smartfinance.correlation'
    _description = 'Cross-Module Correlation Engine'
    _order = 'correlation_score desc'

    name = fields.Char(string='Correlation', required=True)
    module_a = fields.Char(string='Module A')
    module_b = fields.Char(string='Module B')
    metric_a = fields.Char(string='Metric A')
    metric_b = fields.Char(string='Metric B')
    correlation_score = fields.Float(string='Correlation Score (-1 to +1)')
    strength = fields.Selection([
        ('strong_positive', 'Strong Positive'),
        ('moderate_positive', 'Moderate Positive'),
        ('weak', 'Weak / No Correlation'),
        ('moderate_negative', 'Moderate Negative'),
        ('strong_negative', 'Strong Negative'),
    ], string='Correlation Strength')
    interpretation = fields.Text(string='What This Means')
    recommended_action = fields.Text(string='Recommended Action')
    data_points = fields.Integer(string='Months Analyzed')
    is_significant = fields.Boolean(string='Significant Correlation')
    create_date = fields.Datetime(string='Detected On', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model
    def _get_monthly_data(self, months=6):
        """
        Build a list of monthly data points for the last N months.
        Returns a dict with lists of values per metric.
        """
        today = date.today()
        data = {
            'headcount': [],
            'win_rate': [],
            'inflow': [],
            'invoice_count': [],
            'expense_total': [],
            'overdue_count': [],
            'pipeline_value': [],
            'purchase_total': [],
            'outflow': [],
        }

        for i in range(months - 1, -1, -1):
            # Calculate month start and end
            month_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            # Headcount — employees active during that month
            employees = self.env['hr.employee'].search([
                ('active', '=', True),
            ])
            data['headcount'].append(len(employees))

            # CRM win rate
            all_opps = self.env['crm.lead'].search([
                ('type', '=', 'opportunity'),
                ('create_date', '>=', str(month_start)),
                ('create_date', '<', str(month_end)),
            ])
            won_opps = all_opps.filtered(lambda o: o.stage_id.is_won)
            win_rate = (len(won_opps) / len(all_opps) * 100) if all_opps else 0
            data['win_rate'].append(win_rate)

            # Cash inflow
            inbound = self.env['account.payment'].search([
                ('payment_type', '=', 'inbound'),
                ('date', '>=', month_start),
                ('date', '<', month_end),
                ('state', 'in', ['posted', 'in_process', 'paid']),
            ])
            data['inflow'].append(sum(inbound.mapped('amount')))

            # Cash outflow
            outbound = self.env['account.payment'].search([
                ('payment_type', '=', 'outbound'),
                ('date', '>=', month_start),
                ('date', '<', month_end),
                ('state', 'in', ['posted', 'in_process', 'paid']),
            ])
            data['outflow'].append(sum(outbound.mapped('amount')))

            # Invoice count
            invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', 'in', ['posted', 'in_process', 'paid']),
                ('invoice_date', '>=', month_start),
                ('invoice_date', '<', month_end),
            ])
            data['invoice_count'].append(len(invoices))

            # Overdue count at end of month
            overdue = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', 'in', ['posted', 'in_process', 'paid']),
                ('payment_state', 'not in', ['paid', 'reversed', 'in_payment']),
                ('invoice_date_due', '<', month_end),
            ])
            data['overdue_count'].append(len(overdue))

            # Expense total
            expenses = self.env['hr.expense'].search([
                ('date', '>=', month_start),
                ('date', '<', month_end),
                ('state', 'in', ['approved', 'done']),
            ])
            data['expense_total'].append(sum(expenses.mapped('total_amount')))

            # Pipeline value
            opps = self.env['crm.lead'].search([
                ('type', '=', 'opportunity'),
                ('active', '=', True),
            ])
            data['pipeline_value'].append(sum(opps.mapped('expected_revenue')))

            # Purchase total
            pos = self.env['purchase.order'].search([
                ('state', 'in', ('purchase', 'done')),
                ('date_approve', '>=', month_start),
                ('date_approve', '<', month_end),
            ])
            data['purchase_total'].append(sum(pos.mapped('amount_total')))

        return data

    def _pearson_correlation(self, x, y):
        """Calculate Pearson correlation coefficient between two lists."""
        n = len(x)
        if n < 2:
            return 0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

        if denom_x == 0 or denom_y == 0:
            return 0

        return numerator / (denom_x * denom_y)

    def _get_strength(self, score):
        """Classify correlation score into strength category."""
        abs_score = abs(score)
        if abs_score >= 0.7:
            return 'strong_positive' if score > 0 else 'strong_negative'
        elif abs_score >= 0.4:
            return 'moderate_positive' if score > 0 else 'moderate_negative'
        else:
            return 'weak'

    @api.model
    def run_correlation_analysis(self):
        """Main method — runs all correlations and saves results."""
        # Delete old correlations before generating new ones
        self.search([]).unlink()

        data = self._get_monthly_data(months=6)
        months = len(data['headcount'])

        correlations = [
            {
                'metric_a': 'headcount',
                'metric_b': 'win_rate',
                'module_a': 'HR',
                'module_b': 'CRM',
                'name': 'Headcount vs CRM Win Rate',
                'positive_interpretation': (
                    'When your team grows, your CRM win rate improves. '
                    'More staff is positively impacting sales performance.'
                ),
                'negative_interpretation': (
                    'When headcount decreases, your CRM win rate drops. '
                    'Staff reductions may be hurting your sales capacity.'
                ),
                'weak_interpretation': (
                    'No significant relationship detected between team size '
                    'and CRM win rate over the last 6 months.'
                ),
                'positive_action': (
                    'Consider hiring in sales or support roles to further '
                    'improve win rates.'
                ),
                'negative_action': (
                    'Review whether recent staff reductions have reduced '
                    'sales capacity. Consider hiring or redistributing workload.'
                ),
                'weak_action': 'Continue monitoring — more data needed.',
            },
            {
                'metric_a': 'invoice_count',
                'metric_b': 'inflow',
                'module_a': 'Invoicing',
                'module_b': 'Accounting',
                'name': 'Invoice Volume vs Cash Inflow',
                'positive_interpretation': (
                    'More invoices sent leads to more cash collected. '
                    'Your invoicing process is working effectively.'
                ),
                'negative_interpretation': (
                    'Sending more invoices is not translating to more cash. '
                    'Collection efficiency may be declining.'
                ),
                'weak_interpretation': (
                    'No clear relationship between invoice volume and cash '
                    'inflow. Review your payment collection process.'
                ),
                'positive_action': (
                    'Keep invoice volume high and maintain current '
                    'collection processes.'
                ),
                'negative_action': (
                    'Review your collections process. More invoices should '
                    'mean more cash — investigate why payments are delayed.'
                ),
                'weak_action': (
                    'Audit your invoicing and collection workflow for gaps.'
                ),
            },
            {
                'metric_a': 'expense_total',
                'metric_b': 'overdue_count',
                'module_a': 'Expenses',
                'module_b': 'Invoicing',
                'name': 'Expense Spikes vs Overdue Invoices',
                'positive_interpretation': (
                    'When expenses increase, overdue invoices also increase. '
                    'High spending periods may coincide with cash collection problems.'
                ),
                'negative_interpretation': (
                    'When expenses increase, overdue invoices decrease. '
                    'Higher spending appears to correlate with better cash collection.'
                ),
                'weak_interpretation': (
                    'No significant relationship between expense levels '
                    'and overdue invoices.'
                ),
                'positive_action': (
                    'During high-expense months, prioritize invoice collection '
                    'to avoid cash flow stress.'
                ),
                'negative_action': (
                    'Investigate why higher expenses correlate with fewer '
                    'overdue invoices — this may indicate seasonal patterns.'
                ),
                'weak_action': 'Continue monitoring expense and collection trends.',
            },
            {
                'metric_a': 'pipeline_value',
                'metric_b': 'inflow',
                'module_a': 'CRM',
                'module_b': 'Accounting',
                'name': 'CRM Pipeline Value vs Cash Inflow',
                'positive_interpretation': (
                    'A stronger CRM pipeline correlates with higher cash inflow. '
                    'Your sales pipeline is a reliable predictor of future revenue.'
                ),
                'negative_interpretation': (
                    'Higher pipeline value does not translate to higher cash inflow. '
                    'Deals may be stalling at the closing stage.'
                ),
                'weak_interpretation': (
                    'No clear relationship between pipeline value and cash inflow. '
                    'Pipeline quality may be more important than quantity.'
                ),
                'positive_action': (
                    'Keep CRM pipeline healthy — it is a good leading indicator '
                    'of future cash flow.'
                ),
                'negative_action': (
                    'Focus on closing deals rather than adding new ones. '
                    'Review why pipeline value is not converting to cash.'
                ),
                'weak_action': (
                    'Focus on pipeline quality over quantity. '
                    'Qualify leads more strictly.'
                ),
            },
            {
                'metric_a': 'purchase_total',
                'metric_b': 'outflow',
                'module_a': 'Purchase',
                'module_b': 'Accounting',
                'name': 'Purchase Volume vs Cash Outflow',
                'positive_interpretation': (
                    'Higher purchasing activity directly drives cash outflow. '
                    'Buying spikes are causing predictable cash pressure.'
                ),
                'negative_interpretation': (
                    'Purchase volume and cash outflow move in opposite directions. '
                    'Review your vendor payment terms.'
                ),
                'weak_interpretation': (
                    'No significant relationship between purchase volume '
                    'and cash outflow.'
                ),
                'positive_action': (
                    'Plan purchases carefully around expected inflow periods '
                    'to avoid cash crunches.'
                ),
                'negative_action': (
                    'Review vendor payment terms — outflow may be delayed '
                    'relative to purchasing activity.'
                ),
                'weak_action': (
                    'Monitor purchasing patterns monthly to detect emerging trends.'
                ),
            },
        ]

        for c in correlations:
            x = data[c['metric_a']]
            y = data[c['metric_b']]
            score = self._pearson_correlation(x, y)
            strength = self._get_strength(score)
            is_significant = abs(score) >= 0.4

            if score >= 0.4:
                interpretation = c['positive_interpretation']
                action = c['positive_action']
            elif score <= -0.4:
                interpretation = c['negative_interpretation']
                action = c['negative_action']
            else:
                interpretation = c['weak_interpretation']
                action = c['weak_action']

            self.create({
                'name': c['name'],
                'module_a': c['module_a'],
                'module_b': c['module_b'],
                'metric_a': c['metric_a'].replace('_', ' ').title(),
                'metric_b': c['metric_b'].replace('_', ' ').title(),
                'correlation_score': round(score, 3),
                'strength': strength,
                'interpretation': interpretation,
                'recommended_action': action,
                'data_points': months,
                'is_significant': is_significant,
            })

        return True