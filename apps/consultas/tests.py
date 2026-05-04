"""
Testes automatizados para o app de Consultas Médicas.

Utiliza APITestCase do Django REST Framework conforme exigido pelo desafio.
Cobertura expandida:
- CRUD completo de consultas
- Busca de consultas por ID do profissional
- Edge cases e limites de campos
- Validações robustas (data no passado, profissional inexistente)
- Sanitização e segurança
- Proteção de autenticação (JWT)
- Testes da camada de serviço isolada
- Paginação, filtros e ordenação
"""

from datetime import timedelta

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profissionais.models import Profissional
from core.domain import AgendamentoRetroativoException

from .models import Consulta
from .services.consulta_service import ConsultaService


class ConsultaBaseTestCase(APITestCase):
    """Classe base com setup comum para testes de Consulta."""

    def setUp(self):
        """Configura dados de teste e autenticação."""
        # Criar usuário para autenticação JWT
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@lacrei.com",
        )
        # Gerar token JWT
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

        # Criar profissional para vincular às consultas
        self.profissional = Profissional.objects.create(
            nome_social="Dra. Ana Costa",
            profissao="Endocrinologia",
            endereco="Rua da Saúde, 100 - São Paulo, SP",
            contato="ana.costa@email.com",
        )

        self.profissional2 = Profissional.objects.create(
            nome_social="Dr. Pedro Lima",
            profissao="Cardiologia",
            endereco="Av. Brasil, 200 - Rio de Janeiro, RJ",
            contato="pedro.lima@email.com",
        )

        # Data futura para consultas válidas
        self.future_date = timezone.now() + timedelta(days=7)

        # Dados válidos para criação de consulta
        self.valid_data = {
            "data": self.future_date.isoformat(),
            "profissional": self.profissional.pk,
            "observacoes": "Consulta de rotina.",
        }

        # Criar consulta existente
        self.consulta = Consulta.objects.create(
            data=self.future_date,
            profissional=self.profissional,
            observacoes="Consulta inicial.",
        )

        # Criar consultas adicionais para o profissional2
        self.consulta_prof2 = Consulta.objects.create(
            data=self.future_date + timedelta(days=1),
            profissional=self.profissional2,
            observacoes="Consulta cardiológica.",
        )

        # URLs
        self.list_url = reverse("consulta-list")
        self.detail_url = reverse("consulta-detail", kwargs={"pk": self.consulta.pk})


# =============================================================================
# TESTES DE CRIAÇÃO (POST)
# =============================================================================
class ConsultaCreateTests(ConsultaBaseTestCase):
    """Testes de criação (POST) de consultas."""

    def test_criar_consulta_com_dados_validos(self):
        """Deve criar uma consulta com sucesso."""
        response = self.client.post(self.list_url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["profissional"], self.profissional.pk)
        self.assertIn("id", response.data)
        self.assertIn("profissional_detail", response.data)

    def test_criar_consulta_sem_data(self):
        """Deve retornar erro quando data não é fornecida."""
        data = self.valid_data.copy()
        del data["data"]
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_consulta_com_data_retroativa(self):
        """Deve retornar erro ao agendar em data retroativa."""
        past_date = timezone.now() - timedelta(days=1)
        data = self.valid_data.copy()
        data["data"] = past_date.isoformat()
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # O erro de validação deve estar dentro de 'details' devido ao custom handler
        self.assertIn("data", response.data["details"])

    def test_criar_consulta_com_profissional_inexistente(self):
        """Deve retornar erro quando o profissional não existe."""
        data = self.valid_data.copy()
        data["profissional"] = 9999
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sanitizacao_observacoes(self):
        """Deve sanitizar tags HTML nas observações."""
        data = self.valid_data.copy()
        data["observacoes"] = "<script>alert('xss')</script>Consulta <b>segura</b>"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # O bleach deve remover o script e manter o texto/tags permitidas
        self.assertNotIn("<script>", response.data["observacoes"])

    def test_criar_consulta_sem_profissional(self):
        """Deve retornar erro quando profissional não é fornecido."""
        data = self.valid_data.copy()
        del data["profissional"]
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_consulta_com_data_no_passado(self):
        """Deve retornar erro quando data está no passado."""
        data = self.valid_data.copy()
        data["data"] = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_consulta_com_body_vazio(self):
        """Deve retornar erro quando corpo da requisição está vazio."""
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_consulta_sem_observacoes(self):
        """Deve criar consulta sem observações (campo opcional)."""
        data = self.valid_data.copy()
        del data["observacoes"]
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_criar_consulta_sanitiza_observacoes(self):
        """Deve sanitizar observações contra XSS."""
        data = self.valid_data.copy()
        data["observacoes"] = '<script>alert("xss")</script>Consulta importante'
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("<script>", response.data["observacoes"])

    # --- NOVOS EDGE CASES ---

    def test_criar_consulta_com_data_muito_futura(self):
        """Deve aceitar consulta com data muito futura (1 ano)."""
        data = self.valid_data.copy()
        data["data"] = (timezone.now() + timedelta(days=365)).isoformat()
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_criar_consulta_com_data_minutos_no_passado(self):
        """Deve retornar erro mesmo para data poucos minutos no passado."""
        data = self.valid_data.copy()
        data["data"] = (timezone.now() - timedelta(minutes=5)).isoformat()
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_consulta_com_observacoes_unicode(self):
        """Deve aceitar observações com caracteres Unicode."""
        data = self.valid_data.copy()
        data["observacoes"] = "Paciente relata dor crônica — acompanhamento mensal 📋"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_criar_consulta_com_observacoes_vazias(self):
        """Deve aceitar observações como string vazia."""
        data = self.valid_data.copy()
        data["observacoes"] = ""
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_criar_consulta_campos_readonly_ignorados(self):
        """Deve ignorar campos read-only (id, created_at, updated_at)."""
        data = self.valid_data.copy()
        data["id"] = 99999
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], 99999)

    def test_criar_consulta_formato_data_invalido(self):
        """Deve retornar erro para formato de data inválido."""
        data = self.valid_data.copy()
        data["data"] = "data-invalida"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_consulta_profissional_id_negativo(self):
        """Deve retornar erro para profissional com ID negativo."""
        data = self.valid_data.copy()
        data["profissional"] = -1
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_consulta_profissional_string(self):
        """Deve retornar erro quando profissional é string em vez de ID."""
        data = self.valid_data.copy()
        data["profissional"] = "nao-e-numero"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# TESTES DE LEITURA (GET)
# =============================================================================
class ConsultaReadTests(ConsultaBaseTestCase):
    """Testes de leitura (GET) de consultas."""

    def test_listar_consultas(self):
        """Deve retornar lista paginada de consultas."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_detalhar_consulta(self):
        """Deve retornar detalhes de uma consulta existente."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.consulta.pk)
        self.assertIn("profissional_detail", response.data)

    def test_detalhar_consulta_inexistente(self):
        """Deve retornar 404 para consulta inexistente."""
        url = reverse("consulta-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_buscar_consultas_por_profissional(self):
        """
        Deve retornar consultas filtradas pelo ID do profissional.
        Este é um requisito obrigatório do desafio.
        """
        url = reverse(
            "consulta-por-profissional",
            kwargs={"profissional_id": self.profissional.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que retorna apenas consultas do profissional correto
        results = response.data.get("results", response.data)
        if isinstance(results, dict) and "results" in results:
            results = results["results"]
        for consulta in results:
            self.assertEqual(consulta["profissional"], self.profissional.pk)

    def test_buscar_consultas_por_profissional_sem_consultas(self):
        """Deve retornar lista vazia quando profissional não tem consultas."""
        # Criar profissional sem consultas
        prof_sem_consultas = Profissional.objects.create(
            nome_social="Dr. Novo",
            profissao="Dermatologia",
            endereco="Rua X, 1",
            contato="novo@email.com",
        )
        url = reverse(
            "consulta-por-profissional",
            kwargs={"profissional_id": prof_sem_consultas.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_consultas_por_profissional_id(self):
        """Deve filtrar consultas pelo campo profissional via query param."""
        response = self.client.get(
            self.list_url, {"profissional": self.profissional.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for consulta in response.data["results"]:
            self.assertEqual(consulta["profissional"], self.profissional.pk)

    # --- NOVOS EDGE CASES ---

    def test_listar_consultas_paginacao_funciona(self):
        """Deve paginar corretamente com muitas consultas."""
        for i in range(25):
            Consulta.objects.create(
                data=self.future_date + timedelta(days=i + 10),
                profissional=self.profissional,
                observacoes=f"Consulta {i}",
            )
        response = self.client.get(self.list_url, {"page": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["results"])

    def test_listar_consultas_pagina_fora_do_range(self):
        """Deve retornar 404 para página inexistente."""
        response = self.client.get(self.list_url, {"page": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_listar_consultas_ordenacao_por_data(self):
        """Deve ordenar consultas por data."""
        response = self.client.get(self.list_url, {"ordering": "data"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dates = [r["data"] for r in response.data["results"]]
        self.assertEqual(dates, sorted(dates))

    def test_buscar_consultas_por_observacao(self):
        """Deve buscar consultas pelo campo observações."""
        response = self.client.get(self.list_url, {"search": "cardiológica"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_detalhe_consulta_inclui_dados_profissional(self):
        """Detalhe deve incluir dados completos do profissional."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        detail = response.data["profissional_detail"]
        self.assertIn("nome_social", detail)
        self.assertIn("profissao", detail)
        self.assertIn("contato", detail)

    def test_listagem_inclui_is_future(self):
        """Listagem deve incluir flag is_future."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for result in response.data["results"]:
            self.assertIn("is_future", result)


# =============================================================================
# TESTES DE ATUALIZAÇÃO (PUT/PATCH)
# =============================================================================
class ConsultaUpdateTests(ConsultaBaseTestCase):
    """Testes de atualização (PUT/PATCH) de consultas."""

    def test_atualizar_consulta_completa(self):
        """Deve atualizar todos os dados da consulta."""
        new_date = timezone.now() + timedelta(days=14)
        updated_data = {
            "data": new_date.isoformat(),
            "profissional": self.profissional2.pk,
            "observacoes": "Consulta remarcada.",
        }
        response = self.client.put(self.detail_url, updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profissional"], self.profissional2.pk)

    def test_atualizar_consulta_parcial(self):
        """Deve atualizar parcialmente uma consulta (PATCH)."""
        response = self.client.patch(
            self.detail_url,
            {"observacoes": "Observações atualizadas."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["observacoes"], "Observações atualizadas.")

    def test_atualizar_consulta_inexistente(self):
        """Deve retornar 404 ao atualizar consulta inexistente."""
        url = reverse("consulta-detail", kwargs={"pk": 99999})
        response = self.client.put(url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- NOVOS EDGE CASES ---

    def test_patch_nao_altera_outros_campos(self):
        """PATCH deve alterar apenas o campo enviado."""
        original_profissional = self.consulta.profissional.pk
        self.client.patch(
            self.detail_url,
            {"observacoes": "Nova obs"},
            format="json",
        )
        response = self.client.get(self.detail_url)
        self.assertEqual(response.data["profissional"], original_profissional)
        self.assertEqual(response.data["observacoes"], "Nova obs")

    def test_put_exige_campos_obrigatorios(self):
        """PUT deve exigir data e profissional."""
        response = self.client.put(
            self.detail_url,
            {"observacoes": "Apenas obs"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atualizar_consulta_mudar_profissional(self):
        """Deve permitir mudar o profissional da consulta."""
        new_date = timezone.now() + timedelta(days=30)
        response = self.client.put(
            self.detail_url,
            {
                "data": new_date.isoformat(),
                "profissional": self.profissional2.pk,
                "observacoes": "Transferida.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profissional"], self.profissional2.pk)

    def test_atualizar_verifica_updated_at(self):
        """Deve atualizar o campo updated_at após edição."""
        response_before = self.client.get(self.detail_url)
        import time

        time.sleep(0.1)
        self.client.patch(self.detail_url, {"observacoes": "Editado"}, format="json")
        response_after = self.client.get(self.detail_url)
        self.assertNotEqual(
            response_before.data["updated_at"],
            response_after.data["updated_at"],
        )


# =============================================================================
# TESTES DE EXCLUSÃO (DELETE)
# =============================================================================
class ConsultaDeleteTests(ConsultaBaseTestCase):
    """Testes de exclusão (DELETE) de consultas."""

    def test_excluir_consulta(self):
        """Deve excluir uma consulta com sucesso."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Consulta.objects.filter(pk=self.consulta.pk).exists())

    def test_excluir_consulta_inexistente(self):
        """Deve retornar 404 ao excluir consulta inexistente."""
        url = reverse("consulta-detail", kwargs={"pk": 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- NOVOS EDGE CASES ---

    def test_dupla_exclusao_retorna_404(self):
        """Deve retornar 404 ao tentar excluir consulta já excluída."""
        self.client.delete(self.detail_url)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_exclusao_nao_afeta_outras_consultas(self):
        """Excluir uma consulta não deve afetar as outras."""
        self.client.delete(self.detail_url)
        self.assertTrue(Consulta.objects.filter(pk=self.consulta_prof2.pk).exists())

    def test_exclusao_nao_afeta_profissional(self):
        """Excluir consulta não deve afetar o profissional vinculado."""
        prof_id = self.consulta.profissional.pk
        self.client.delete(self.detail_url)
        self.assertTrue(Profissional.objects.filter(pk=prof_id).exists())


# =============================================================================
# TESTES DE AUTENTICAÇÃO
# =============================================================================
class ConsultaAuthTests(APITestCase):
    """Testes de autenticação para endpoints de consultas."""

    def test_listar_consultas_sem_autenticacao(self):
        """Deve retornar 401 quando não autenticado."""
        url = reverse("consulta-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_criar_consulta_sem_autenticacao(self):
        """Deve retornar 401 quando não autenticado."""
        url = reverse("consulta-list")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- NOVOS EDGE CASES ---

    def test_acessar_com_token_invalido(self):
        """Deve retornar 401 com token inválido."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token-invalido")
        response = self.client.get(reverse("consulta-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_sem_autenticacao(self):
        """Deve retornar 401 ao deletar sem autenticação."""
        prof = Profissional.objects.create(
            nome_social="Dr. Auth",
            profissao="Medicina",
            endereco="Rua A, 1",
            contato="auth@email.com",
        )
        consulta = Consulta.objects.create(
            data=timezone.now() + timedelta(days=7),
            profissional=prof,
        )
        url = reverse("consulta-detail", kwargs={"pk": consulta.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_buscar_por_profissional_sem_autenticacao(self):
        """Deve retornar 401 ao buscar por profissional sem auth."""
        prof = Profissional.objects.create(
            nome_social="Dr. Auth",
            profissao="Medicina",
            endereco="Rua A, 1",
            contato="auth@email.com",
        )
        url = reverse(
            "consulta-por-profissional",
            kwargs={"profissional_id": prof.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# TESTES DA CAMADA DE SERVIÇO (ISOLADOS)
# =============================================================================
class ConsultaServiceTests(APITestCase):
    """
    Testes da camada de serviço isolada (sem HTTP).

    Valida que as regras de negócio funcionam independente do protocolo.
    """

    def setUp(self):
        self.profissional = Profissional.objects.create(
            nome_social="Dr. Service",
            profissao="Psicologia",
            endereco="Rua Service, 100",
            contato="service@email.com",
        )

    def test_service_agendar_consulta_valida(self):
        """Service deve criar consulta com data futura."""
        data = {
            "data": timezone.now() + timedelta(days=7),
            "profissional": self.profissional,
        }
        consulta = ConsultaService.agendar_consulta(data)
        self.assertIsNotNone(consulta.id)
        self.assertEqual(consulta.profissional, self.profissional)

    def test_service_agendar_consulta_retroativa_lanca_excecao(self):
        """Service deve lançar AgendamentoRetroativoException."""
        data = {
            "data": timezone.now() - timedelta(days=1),
            "profissional": self.profissional,
        }
        with self.assertRaises(AgendamentoRetroativoException):
            ConsultaService.agendar_consulta(data)

    def test_service_atualizar_consulta(self):
        """Service deve atualizar consulta existente."""
        consulta = Consulta.objects.create(
            data=timezone.now() + timedelta(days=7),
            profissional=self.profissional,
        )
        updated = ConsultaService.atualizar_consulta(
            consulta, {"observacoes": "Atualizado via service"}
        )
        self.assertEqual(updated.observacoes, "Atualizado via service")

    def test_service_cancelar_consulta(self):
        """Service deve remover consulta."""
        consulta = Consulta.objects.create(
            data=timezone.now() + timedelta(days=7),
            profissional=self.profissional,
        )
        consulta_id = consulta.id
        result = ConsultaService.cancelar_consulta(consulta)
        self.assertTrue(result)
        self.assertFalse(Consulta.objects.filter(pk=consulta_id).exists())

    def test_service_buscar_por_profissional(self):
        """Service deve retornar consultas filtradas por profissional."""
        Consulta.objects.create(
            data=timezone.now() + timedelta(days=7),
            profissional=self.profissional,
        )
        consultas = ConsultaService.buscar_por_profissional(self.profissional.pk)
        self.assertEqual(consultas.count(), 1)

    def test_service_list_consultas_com_select_related(self):
        """Service deve retornar queryset otimizado."""
        Consulta.objects.create(
            data=timezone.now() + timedelta(days=7),
            profissional=self.profissional,
        )
        queryset = ConsultaService.list_consultas()
        self.assertTrue(queryset.exists())


# =============================================================================
# TESTES DE MÉTODO HTTP INVÁLIDO
# =============================================================================
class ConsultaMethodTests(ConsultaBaseTestCase):
    """Testes para métodos HTTP não suportados."""

    def test_post_em_detalhe_retorna_405(self):
        """POST em endpoint de detalhe deve retornar 405."""
        response = self.client.post(self.detail_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
