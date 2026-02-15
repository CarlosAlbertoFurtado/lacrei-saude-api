"""
Proposta de Integração com Assas (Gateway de Pagamentos).

Decisão técnica: Esta é uma proposta arquitetural de integração com a API
da Assas para split de pagamento. A implementação utiliza mock para
demonstrar o fluxo sem necessidade de credenciais reais.

Documentação pública Assas: https://docs.asaas.com/

Fluxo proposto:
1. Paciente agenda consulta via API
2. Sistema cria cobrança na Assas vinculada à consulta
3. Pagamento é processado pela Assas
4. Webhook da Assas notifica o sistema sobre status do pagamento
5. Split de pagamento: valor é dividido entre Lacrei e profissional
"""

import logging
from dataclasses import dataclass
from datetime import date
from enum import Enum

from decouple import config

logger = logging.getLogger("apps")

# Configuração da API Assas
ASSAS_API_KEY = config("ASSAS_API_KEY", default="mock-api-key")
ASSAS_API_URL = config("ASSAS_API_URL", default="https://sandbox.asaas.com/api/v3")


class PaymentStatus(Enum):
    """Status possíveis de um pagamento na Assas."""

    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    CONFIRMED = "CONFIRMED"
    OVERDUE = "OVERDUE"
    REFUNDED = "REFUNDED"
    RECEIVED_IN_CASH = "RECEIVED_IN_CASH"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    CHARGEBACK_REQUESTED = "CHARGEBACK_REQUESTED"
    CHARGEBACK_DISPUTE = "CHARGEBACK_DISPUTE"
    AWAITING_CHARGEBACK_REVERSAL = "AWAITING_CHARGEBACK_REVERSAL"
    DUNNING_REQUESTED = "DUNNING_REQUESTED"
    DUNNING_RECEIVED = "DUNNING_RECEIVED"
    AWAITING_RISK_ANALYSIS = "AWAITING_RISK_ANALYSIS"


@dataclass
class PaymentData:
    """Dados para criação de cobrança na Assas."""

    customer_id: str
    billing_type: str  # BOLETO, CREDIT_CARD, PIX
    value: float
    due_date: str
    description: str
    external_reference: str  # ID da consulta no nosso sistema


@dataclass
class SplitData:
    """Dados para split de pagamento."""

    wallet_id: str  # Wallet do profissional na Assas
    fixed_value: float | None = None
    percent_value: float | None = None


class AssasService:
    """
    Serviço de integração com a API da Assas (Mock).

    Em produção, este serviço faria chamadas HTTP reais à API da Assas.
    Para este desafio, implementamos com mock para demonstrar a arquitetura.

    Endpoints da Assas utilizados:
    - POST /customers       - Cadastrar cliente
    - POST /payments        - Criar cobrança
    - POST /payments/{id}/splits - Configurar split
    - GET  /payments/{id}   - Consultar status
    """

    def __init__(self):
        self.api_key = ASSAS_API_KEY
        self.base_url = ASSAS_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "access_token": self.api_key,
        }

    def create_customer(self, name: str, cpf: str, email: str) -> dict:
        """
        Cria um cliente na Assas.

        Em produção: POST https://api.asaas.com/v3/customers
        """
        logger.info("Assas Mock: Criando cliente %s", name)

        # Mock response
        return {
            "id": "cus_mock_123456",
            "name": name,
            "cpfCnpj": cpf,
            "email": email,
            "status": "ACTIVE",
        }

    def create_payment(self, payment_data: PaymentData) -> dict:
        """
        Cria uma cobrança na Assas.

        Em produção: POST https://api.asaas.com/v3/payments
        """
        logger.info(
            "Assas Mock: Criando cobrança de R$%.2f para consulta %s",
            payment_data.value,
            payment_data.external_reference,
        )

        # Mock response
        return {
            "id": "pay_mock_789012",
            "customer": payment_data.customer_id,
            "billingType": payment_data.billing_type,
            "value": payment_data.value,
            "dueDate": payment_data.due_date,
            "description": payment_data.description,
            "externalReference": payment_data.external_reference,
            "status": PaymentStatus.PENDING.value,
            "invoiceUrl": "https://sandbox.asaas.com/i/mock_invoice",
            "bankSlipUrl": "https://sandbox.asaas.com/b/mock_boleto",
        }

    def configure_split(self, payment_id: str, splits: list[SplitData]) -> dict:
        """
        Configura split de pagamento.

        O split divide o valor entre a Lacrei Saúde e o profissional.
        Exemplo: 80% profissional, 20% taxa Lacrei.

        Em produção: POST https://api.asaas.com/v3/payments/{id}/splits
        """
        logger.info("Assas Mock: Configurando split para pagamento %s", payment_id)

        split_configs = []
        for split in splits:
            split_configs.append(
                {
                    "walletId": split.wallet_id,
                    "fixedValue": split.fixed_value,
                    "percentualValue": split.percent_value,
                }
            )

        # Mock response
        return {
            "payment_id": payment_id,
            "splits": split_configs,
            "status": "CONFIGURED",
        }

    def get_payment_status(self, payment_id: str) -> dict:
        """
        Consulta status de um pagamento.

        Em produção: GET https://api.asaas.com/v3/payments/{id}
        """
        logger.info("Assas Mock: Consultando status do pagamento %s", payment_id)

        # Mock response
        return {
            "id": payment_id,
            "status": PaymentStatus.CONFIRMED.value,
            "value": 200.00,
            "confirmedDate": str(date.today()),
        }

    def process_webhook(self, payload: dict) -> dict:
        """
        Processa webhook recebido da Assas.

        A Assas envia notificações via webhook quando o status
        de um pagamento muda. Este método processa o payload
        e atualiza o status da consulta no nosso sistema.

        Eventos relevantes:
        - PAYMENT_CONFIRMED: Pagamento confirmado
        - PAYMENT_RECEIVED: Pagamento recebido
        - PAYMENT_OVERDUE: Pagamento atrasado
        - PAYMENT_REFUNDED: Pagamento estornado
        """
        event = payload.get("event")
        payment = payload.get("payment", {})

        logger.info(
            "Assas Webhook: Evento=%s, Pagamento=%s",
            event,
            payment.get("id"),
        )

        return {
            "event": event,
            "payment_id": payment.get("id"),
            "status": payment.get("status"),
            "processed": True,
        }


# ============================================================
# Exemplo de uso da integração com o fluxo de consultas
# ============================================================
#
# Quando uma consulta é criada:
#
# assas = AssasService()
#
# # 1. Criar cliente (paciente)
# customer = assas.create_customer(
#     name="Paciente Teste",
#     cpf="12345678901",
#     email="paciente@email.com"
# )
#
# # 2. Criar cobrança
# payment = assas.create_payment(PaymentData(
#     customer_id=customer["id"],
#     billing_type="PIX",
#     value=200.00,
#     due_date="2026-02-20",
#     description="Consulta médica - Dra. Ana Costa",
#     external_reference="consulta_123"
# ))
#
# # 3. Configurar split (80% profissional, 20% Lacrei)
# split = assas.configure_split(
#     payment_id=payment["id"],
#     splits=[
#         SplitData(wallet_id="wal_profissional_123", percent_value=80.0),
#         SplitData(wallet_id="wal_lacrei_456", percent_value=20.0),
#     ]
# )
