"""
Testes automatizados para o app de Consultas Médicas.

Utiliza APITestCase do Django REST Framework conforme exigido pelo desafio.
Cobertura:
- CRUD completo de consultas
- Busca de consultas por ID do profissional
- Testes de erro (requisição inválida, dados ausentes)
- Validação de dados (data no passado, profissional inexistente)
- Proteção de autenticação
"""

from datetime import timedelta

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profissionais.models import Profissional

from .models import Consulta


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

    def test_criar_consulta_sem_profissional(self):
        """Deve retornar erro quando profissional não é fornecido."""
        data = self.valid_data.copy()
        del data["profissional"]
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_consulta_com_profissional_inexistente(self):
        """Deve retornar erro quando profissional não existe."""
        data = self.valid_data.copy()
        data["profissional"] = 99999
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
