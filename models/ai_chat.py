from odoo import models, fields, api
from datetime import timedelta


class AIChat(models.Model):
    _name = 'smartfinance.chat'
    _description = 'AI Financial Chat'
    _order = 'create_date desc'

    name = fields.Char(string='Session', default='Chat Session')
    user_question = fields.Char(string='Your Question')
    message_ids = fields.One2many('smartfinance.chat.message', 'chat_id', string='Messages')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def _send(self, question):
        """Save user message and generate AI reply."""
        self.env['smartfinance.chat.message'].create({
            'chat_id': self.id,
            'role': 'user',
            'content': question,
        })
        response = self.env['smartfinance.chat.message']._generate_response(question)
        self.env['smartfinance.chat.message'].create({
            'chat_id': self.id,
            'role': 'assistant',
            'content': response,
        })
        self.user_question = ''

    def action_send_message(self):
        if self.user_question:
            self._send(self.user_question)

    def action_ask_overdue(self):
        self._send("What are my overdue invoices?")

    def action_ask_cashflow(self):
        self._send("How is my cash flow?")

    def action_ask_risks(self):
        self._send("What are my biggest financial risks?")

    def action_ask_recommendations(self):
        self._send("What do you recommend I do?")

    def action_ask_health(self):
        self._send("What is my financial health score?")


class AIChatMessage(models.Model):
    _name = 'smartfinance.chat.message'
    _description = 'AI Chat Message'
    _order = 'create_date asc'

    chat_id = fields.Many2one('smartfinance.chat', string='Chat', ondelete='cascade')
    role = fields.Selection([('user', 'User'), ('assistant', 'AI')], string='Role')
    content = fields.Text(string='Message')
    create_date = fields.Datetime(string='Time', readonly=True)

    @api.model
    def _generate_response(self, question):
        """Rule-based AI response engine using live Odoo data."""
        q = question.lower()
        today = fields.Date.today()
        thirty_days_ago = today - timedelta(days=30)

        # Live data
        overdue = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ['paid', 'reversed', 'in_payment']),
            ('invoice_date_due', '<', today),
        ])
        total_overdue = sum(overdue.mapped('amount_residual'))

        inbound = self.env['account.payment'].search([
            ('payment_type', '=', 'inbound'),
            ('date', '>=', thirty_days_ago),
            ('state', '=', 'posted'),
        ])
        total_inflow = sum(inbound.mapped('amount'))

        outbound = self.env['account.payment'].search([
            ('payment_type', '=', 'outbound'),
            ('date', '>=', thirty_days_ago),
            ('state', '=', 'posted'),
        ])
        total_outflow = sum(outbound.mapped('amount'))

        opportunities = self.env['crm.lead'].search([('type', '=', 'opportunity')])
        won = opportunities.filtered(lambda o: o.stage_id.is_won)
        pipeline_value = sum(opportunities.mapped('expected_revenue'))
        employees = self.env['hr.employee'].search([('active', '=', True)])
        health = self.env['smartfinance.health.score'].search([], limit=1, order='date desc')

        if any(w in q for w in ['overdue', 'unpaid', 'outstanding', 'invoice']):
            if total_overdue == 0:
                return "✅ Great news! You have no overdue invoices. All customer payments are up to date."
            oldest = min(overdue.mapped('invoice_date_due')) if overdue else None
            days = (today - oldest).days if oldest else 0
            return (
                f"⚠️ You have {len(overdue)} overdue invoice(s) totaling AED {total_overdue:,.0f}.\n\n"
                f"Oldest invoice is {days} days overdue.\n\n"
                f"Recommended actions:\n"
                f"1. Send payment reminders immediately\n"
                f"2. Call customers overdue by 30+ days\n"
                f"3. Consider offering early payment discounts"
            )

        elif any(w in q for w in ['cash', 'flow', 'money', 'inflow', 'outflow', 'liquidity']):
            net = total_inflow - total_outflow
            status = "positive ✅" if net >= 0 else "negative ⚠️"
            return (
                f"💰 Cash Flow Summary (last 30 days):\n\n"
                f"Inflow: AED {total_inflow:,.0f}\n"
                f"Outflow: AED {total_outflow:,.0f}\n"
                f"Net position: AED {net:,.0f} ({status})\n\n"
                f"{'Your cash position is healthy.' if net >= 0 else 'Outflow exceeds inflow. Delay non-critical payments and accelerate collections.'}"
            )

        elif any(w in q for w in ['crm', 'pipeline', 'deal', 'opportunity', 'sales', 'revenue']):
            win_rate = (len(won) / len(opportunities) * 100) if opportunities else 0
            return (
                f"📊 CRM Pipeline Summary:\n\n"
                f"Open opportunities: {len(opportunities)}\n"
                f"Total pipeline value: AED {pipeline_value:,.0f}\n"
                f"Won deals: {len(won)}\n"
                f"Win rate: {win_rate:.1f}%\n\n"
                f"{'Good win rate!' if win_rate >= 20 else 'Win rate below 20%. Focus on qualifying leads better.'}"
            )

        elif any(w in q for w in ['employee', 'staff', 'hr', 'workforce', 'headcount']):
            incomplete = employees.filtered(
                lambda e: not e.job_id or not e.work_email or not e.department_id
            )
            return (
                f"👥 Workforce Summary:\n\n"
                f"Active employees: {len(employees)}\n"
                f"Incomplete profiles: {len(incomplete)}\n\n"
                f"{'All profiles complete ✅' if not incomplete else f'{len(incomplete)} employee(s) missing key profile info.'}"
            )

        elif any(w in q for w in ['health', 'score', 'overall', 'performance']):
            if health:
                return (
                    f"🏥 Financial Health Score: {health.overall_score}/100\n\n"
                    f"Cash Flow: {health.cashflow_score}/100\n"
                    f"Invoicing: {health.invoicing_score}/100\n"
                    f"Workforce: {health.hr_score}/100\n"
                    f"CRM: {health.crm_score}/100\n"
                    f"Purchasing: {health.purchase_score}/100\n\n"
                    f"{'Business performing well.' if health.overall_score >= 60 else 'Several areas need attention. Check AI Insights for details.'}"
                )
            return "No health score yet. Please run the Daily Analysis first."

        elif any(w in q for w in ['risk', 'problem', 'issue', 'concern', 'alert']):
            risks = []
            if total_overdue > 0:
                risks.append(f"• AED {total_overdue:,.0f} in overdue invoices")
            if total_outflow > total_inflow:
                risks.append(f"• Cash outflow exceeds inflow by AED {total_outflow - total_inflow:,.0f}")
            if len(opportunities) > 0 and len(won) / len(opportunities) < 0.2:
                risks.append(f"• Low CRM win rate ({len(won)/len(opportunities)*100:.1f}%)")
            if not risks:
                return "✅ No major financial risks detected. Your business metrics look healthy!"
            return "🚨 Current Financial Risks:\n\n" + "\n".join(risks)

        elif any(w in q for w in ['recommend', 'advice', 'suggest', 'improve', 'should']):
            advice = []
            if total_overdue > 0:
                advice.append(f"1. Chase AED {total_overdue:,.0f} in overdue invoices immediately")
            if total_outflow > total_inflow:
                advice.append("2. Review and delay non-critical vendor payments")
            if len(opportunities) > 5:
                advice.append("3. Follow up on stale CRM opportunities")
            advice.append("4. Ensure all employee profiles are complete in HR")
            if not advice:
                return "✅ Your financials look healthy! Keep monitoring daily."
            return "💡 Top Recommendations:\n\n" + "\n".join(advice)

        else:
            return (
                "I'm SmartFinance AI. I can answer questions about:\n\n"
                "• 📄 Overdue invoices\n"
                "• 💰 Cash flow\n"
                "• 📊 CRM pipeline\n"
                "• 👥 Workforce\n"
                "• 🏥 Health score\n"
                "• 🚨 Financial risks\n"
                "• 💡 Recommendations\n\n"
                "Try: 'What are my biggest risks?' or 'How is my cash flow?'"
            )