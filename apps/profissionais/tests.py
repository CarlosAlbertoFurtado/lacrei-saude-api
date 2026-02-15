"""
Testes automatizados para o app de Profissionais da Saúde.

Utiliza APITestCase do Django REST Framework conforme exigido pelo desafio.
Cobertura:
- CRUD completo de profissionais
- Testes de erro (requisição inválida, dados ausentes)
- Validação e sanitização de dados
- Proteção de autenticação
"""

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Profissional


class ProfissionalBaseTestCase(APITestCase):
    """Classe base com setup comum para testes de Profissional."""

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

        # Dados válidos para criação de profissional
        self.valid_data = {
            "nome_social": "Dra. Maria Silva",
            "profissao": "Medicina - Clínica Geral",
            "endereco": "Rua das Flores, 123 - São Paulo, SP",
            "contato": "maria.silva@email.com",
        }

        # Criar um profissional para testes de leitura/atualização/exclusão
        self.profissional = Profissional.objects.create(
            nome_social="Dr. João Santos",
            profissao="Psicologia",
            endereco="Av. Paulista, 1000 - São Paulo, SP",
            contato="joao.santos@email.com",
        )

        # URLs
        self.list_url = reverse("profissional-list")
        self.detail_url = reverse(
            "profissional-detail", kwargs={"pk": self.profissional.pk}
        )


class ProfissionalCreateTests(ProfissionalBaseTestCase):
    """Testes de criação (POST) de profissionais."""

    def test_criar_profissional_com_dados_validos(self):
        """Deve criar um profissional com sucesso quando dados são válidos."""
        response = self.client.post(self.list_url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nome_social"], self.valid_data["nome_social"])
        self.assertEqual(response.data["profissao"], self.valid_data["profissao"])
        self.assertEqual(response.data["endereco"], self.valid_data["endereco"])
        self.assertEqual(response.data["contato"], self.valid_data["contato"])
        self.assertIn("id", response.data)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_criar_profissional_sem_nome_social(self):
        """Deve retornar erro quando nome_social não é fornecido."""
        data = self.valid_data.copy()
        del data["nome_social"]
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_sem_profissao(self):
        """Deve retornar erro quando profissão não é fornecida."""
        data = self.valid_data.copy()
        del data["profissao"]
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_sem_endereco(self):
        """Deve retornar erro quando endereço não é fornecido."""
        data = self.valid_data.copy()
        del data["endereco"]
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_sem_contato(self):
        """Deve retornar erro quando contato não é fornecido."""
        data = self.valid_data.copy()
        del data["contato"]
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_com_body_vazio(self):
        """Deve retornar erro quando o corpo da requisição está vazio."""
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_nome_social_muito_curto(self):
        """Deve retornar erro quando nome_social tem menos de 2 caracteres."""
        data = self.valid_data.copy()
        data["nome_social"] = "A"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_sanitiza_html(self):
        """Deve sanitizar tags HTML do nome_social."""
        data = self.valid_data.copy()
        data["nome_social"] = '<script>alert("xss")</script>Dra. Maria'
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("<script>", response.data["nome_social"])
        self.assertIn("Dra. Maria", response.data["nome_social"])


class ProfissionalReadTests(ProfissionalBaseTestCase):
    """Testes de leitura (GET) de profissionais."""

    def test_listar_profissionais(self):
        """Deve retornar lista paginada de profissionais."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_detalhar_profissional(self):
        """Deve retornar detalhes de um profissional existente."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.profissional.pk)
        self.assertEqual(response.data["nome_social"], self.profissional.nome_social)

    def test_detalhar_profissional_inexistente(self):
        """Deve retornar 404 para profissional inexistente."""
        url = reverse("profissional-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_buscar_profissional_por_profissao(self):
        """Deve filtrar profissionais pela profissão."""
        response = self.client.get(self.list_url, {"profissao": "Psicologia"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_buscar_profissional_por_nome(self):
        """Deve buscar profissionais pelo nome social."""
        response = self.client.get(self.list_url, {"search": "João"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)


class ProfissionalUpdateTests(ProfissionalBaseTestCase):
    """Testes de atualização (PUT/PATCH) de profissionais."""

    def test_atualizar_profissional_completo(self):
        """Deve atualizar todos os campos de um profissional."""
        updated_data = {
            "nome_social": "Dr. João Santos Atualizado",
            "profissao": "Psicologia Clínica",
            "endereco": "Rua Nova, 456 - São Paulo, SP",
            "contato": "joao.novo@email.com",
        }
        response = self.client.put(self.detail_url, updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome_social"], updated_data["nome_social"])

    def test_atualizar_profissional_parcial(self):
        """Deve atualizar parcialmente um profissional (PATCH)."""
        response = self.client.patch(
            self.detail_url,
            {"profissao": "Psicologia Infantil"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profissao"], "Psicologia Infantil")

    def test_atualizar_profissional_inexistente(self):
        """Deve retornar 404 ao atualizar profissional inexistente."""
        url = reverse("profissional-detail", kwargs={"pk": 99999})
        response = self.client.put(url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfissionalDeleteTests(ProfissionalBaseTestCase):
    """Testes de exclusão (DELETE) de profissionais."""

    def test_excluir_profissional(self):
        """Deve excluir um profissional sem consultas vinculadas."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Profissional.objects.filter(pk=self.profissional.pk).exists())

    def test_excluir_profissional_inexistente(self):
        """Deve retornar 404 ao excluir profissional inexistente."""
        url = reverse("profissional-detail", kwargs={"pk": 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfissionalAuthTests(APITestCase):
    """Testes de autenticação para endpoints de profissionais."""

    def test_listar_profissionais_sem_autenticacao(self):
        """Deve retornar 401 quando não autenticado."""
        url = reverse("profissional-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_criar_profissional_sem_autenticacao(self):
        """Deve retornar 401 quando não autenticado."""
        url = reverse("profissional-list")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_acessar_com_token_invalido(self):
        """Deve retornar 401 com token inválido."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token-invalido")
        url = reverse("profissional-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
