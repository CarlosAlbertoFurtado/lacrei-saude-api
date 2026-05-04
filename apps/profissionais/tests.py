"""
Testes automatizados para o app de Profissionais da Saúde.

Utiliza APITestCase do Django REST Framework conforme exigido pelo desafio.
Cobertura expandida:
- CRUD completo de profissionais
- Edge cases e limites de campos
- Validações robustas e sanitização
- Cenários de erro detalhados (400, 401, 404, 405, 409)
- Proteção de autenticação (JWT)
- Testes da camada de serviço isolada
- Concorrência e integridade referencial
- Paginação, filtros e ordenação
"""

from unittest.mock import patch

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.consultas.models import Consulta
from django.utils import timezone
from datetime import timedelta

from .models import Profissional
from .services import ProfissionalService
from core.domain import ProfissionalComConsultasException, NotFoundException


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


# =============================================================================
# TESTES DE CRIAÇÃO (POST)
# =============================================================================
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

    # --- NOVOS EDGE CASES ---

    def test_criar_profissional_nome_social_no_limite_maximo(self):
        """Deve criar profissional com nome de 255 caracteres (limite máximo)."""
        data = self.valid_data.copy()
        data["nome_social"] = "A" * 255
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["nome_social"]), 255)

    def test_criar_profissional_nome_social_excede_limite(self):
        """Deve retornar erro com nome acima de 255 caracteres."""
        data = self.valid_data.copy()
        data["nome_social"] = "A" * 256
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_com_caracteres_unicode(self):
        """Deve aceitar caracteres Unicode (acentos, cedilha)."""
        data = self.valid_data.copy()
        data["nome_social"] = "Drª. María José Müller-Conceição"
        data["profissao"] = "Nutrição Funcional"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nome_social"], data["nome_social"])

    def test_criar_profissional_com_emojis_no_nome(self):
        """Deve aceitar emojis no nome (inclusividade)."""
        data = self.valid_data.copy()
        data["nome_social"] = "Dr. Carlos 🏳️‍🌈"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_criar_profissional_nome_apenas_espacos(self):
        """Deve retornar erro quando nome contém apenas espaços."""
        data = self.valid_data.copy()
        data["nome_social"] = "   "
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_contato_muito_curto(self):
        """Deve retornar erro quando contato tem menos de 5 caracteres."""
        data = self.valid_data.copy()
        data["contato"] = "ab"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_endereco_muito_curto(self):
        """Deve retornar erro quando endereço tem menos de 5 caracteres."""
        data = self.valid_data.copy()
        data["endereco"] = "Rua"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_profissional_sanitiza_todos_os_campos(self):
        """Deve sanitizar tags HTML em TODOS os campos de texto."""
        data = {
            "nome_social": '<b>Nome</b><script>alert("x")</script> Social',
            "profissao": '<img src=x onerror=alert("x")>Medicina',
            "endereco": '<a href="evil">Rua</a> das Flores, 123',
            "contato": '<script>steal()</script>contato@email.com',
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("<script>", response.data["nome_social"])
        self.assertNotIn("<img", response.data["profissao"])
        self.assertNotIn("<a ", response.data["endereco"])
        self.assertNotIn("<script>", response.data["contato"])

    def test_criar_profissional_campos_readonly_ignorados(self):
        """Deve ignorar campos read-only (id, created_at, updated_at)."""
        data = self.valid_data.copy()
        data["id"] = 99999
        data["created_at"] = "2020-01-01T00:00:00Z"
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], 99999)


# =============================================================================
# TESTES DE LEITURA (GET)
# =============================================================================
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

    # --- NOVOS EDGE CASES ---

    def test_listar_profissionais_paginacao_segunda_pagina(self):
        """Deve retornar página 2 quando existem profissionais suficientes."""
        # Criar profissionais suficientes para 2 páginas (page_size=20)
        for i in range(21):
            Profissional.objects.create(
                nome_social=f"Dr. Teste {i}",
                profissao="Medicina",
                endereco=f"Rua {i}, 100",
                contato=f"teste{i}@email.com",
            )
        response = self.client.get(self.list_url, {"page": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["results"])

    def test_listar_profissionais_pagina_alem_do_range(self):
        """Deve retornar 404 quando a página está fora do range."""
        response = self.client.get(self.list_url, {"page": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filtrar_profissao_inexistente(self):
        """Deve retornar lista vazia para profissão que não existe."""
        response = self.client.get(
            self.list_url, {"profissao": "ProfissaoInexistente"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_buscar_por_nome_inexistente(self):
        """Deve retornar lista vazia para busca sem resultados."""
        response = self.client.get(self.list_url, {"search": "NomeQueNaoExiste12345"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_ordenar_profissionais_por_nome(self):
        """Deve ordenar profissionais por nome social."""
        Profissional.objects.create(
            nome_social="Ana",
            profissao="Medicina",
            endereco="Rua A, 1",
            contato="ana@email.com",
        )
        Profissional.objects.create(
            nome_social="Zélia",
            profissao="Psicologia",
            endereco="Rua Z, 1",
            contato="zelia@email.com",
        )
        response = self.client.get(self.list_url, {"ordering": "nome_social"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [r["nome_social"] for r in response.data["results"]]
        self.assertEqual(names, sorted(names))

    def test_listagem_inclui_total_consultas(self):
        """Deve incluir contagem de consultas na listagem."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for result in response.data["results"]:
            self.assertIn("total_consultas", result)

    def test_detalhe_inclui_timestamps(self):
        """Deve incluir created_at e updated_at no detalhe."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)


# =============================================================================
# TESTES DE ATUALIZAÇÃO (PUT/PATCH)
# =============================================================================
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

    # --- NOVOS EDGE CASES ---

    def test_patch_nao_altera_outros_campos(self):
        """PATCH deve alterar apenas o campo enviado, mantendo os demais."""
        original_nome = self.profissional.nome_social
        self.client.patch(
            self.detail_url, {"profissao": "Nova Profissão"}, format="json"
        )
        response = self.client.get(self.detail_url)
        self.assertEqual(response.data["nome_social"], original_nome)
        self.assertEqual(response.data["profissao"], "Nova Profissão")

    def test_put_exige_todos_os_campos(self):
        """PUT deve exigir todos os campos obrigatórios."""
        response = self.client.put(
            self.detail_url,
            {"nome_social": "Apenas nome"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atualizar_verifica_updated_at_muda(self):
        """Deve atualizar o campo updated_at após edição."""
        response_before = self.client.get(self.detail_url)
        updated_at_before = response_before.data["updated_at"]

        import time

        time.sleep(0.1)

        self.client.patch(
            self.detail_url, {"profissao": "Psicologia Forense"}, format="json"
        )
        response_after = self.client.get(self.detail_url)
        updated_at_after = response_after.data["updated_at"]

        self.assertNotEqual(updated_at_before, updated_at_after)


# =============================================================================
# TESTES DE EXCLUSÃO (DELETE)
# =============================================================================
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

    # --- NOVOS EDGE CASES ---

    def test_excluir_profissional_com_consultas_retorna_409(self):
        """Deve retornar 409 quando profissional tem consultas vinculadas."""
        # Criar consulta vinculada ao profissional
        Consulta.objects.create(
            data=timezone.now() + timedelta(days=7),
            profissional=self.profissional,
            observacoes="Consulta de teste.",
        )
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error", response.data)
        # Profissional NÃO deve ter sido excluído
        self.assertTrue(
            Profissional.objects.filter(pk=self.profissional.pk).exists()
        )

    def test_dupla_exclusao_retorna_404(self):
        """Deve retornar 404 ao tentar excluir profissional já excluído."""
        self.client.delete(self.detail_url)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_exclusao_nao_afeta_outros_profissionais(self):
        """Excluir um profissional não deve afetar os outros."""
        outro = Profissional.objects.create(
            nome_social="Dra. Outra",
            profissao="Medicina",
            endereco="Rua B, 2",
            contato="outra@email.com",
        )
        self.client.delete(self.detail_url)
        self.assertTrue(Profissional.objects.filter(pk=outro.pk).exists())


# =============================================================================
# TESTES DE AUTENTICAÇÃO
# =============================================================================
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

    # --- NOVOS EDGE CASES ---

    def test_acessar_com_token_expirado(self):
        """Deve retornar 401 com token expirado/malformado."""
        # Token com formato JWT válido mas assinatura/conteúdo inválido
        expired_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxMDAwMDAwMDAwfQ."
            "invalid-signature-here"
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {expired_token}"
        )
        response = self.client.get(reverse("profissional-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_acessar_detalhe_sem_autenticacao(self):
        """Deve retornar 401 ao acessar detalhe sem token."""
        prof = Profissional.objects.create(
            nome_social="Test",
            profissao="Medicina",
            endereco="Rua X, 1",
            contato="test@email.com",
        )
        url = reverse("profissional-detail", kwargs={"pk": prof.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_sem_autenticacao(self):
        """Deve retornar 401 ao deletar sem autenticação."""
        prof = Profissional.objects.create(
            nome_social="Test",
            profissao="Medicina",
            endereco="Rua X, 1",
            contato="test@email.com",
        )
        url = reverse("profissional-detail", kwargs={"pk": prof.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# TESTES DA CAMADA DE SERVIÇO (ISOLADOS)
# =============================================================================
class ProfissionalServiceTests(APITestCase):
    """
    Testes da camada de serviço isolada (sem HTTP).

    Valida que as regras de negócio funcionam independente do protocolo HTTP,
    garantindo que a lógica pode ser reutilizada em CLI, tasks, etc.
    """

    def setUp(self):
        self.profissional = Profissional.objects.create(
            nome_social="Dr. Teste Service",
            profissao="Psicologia",
            endereco="Rua Service, 100",
            contato="service@email.com",
        )

    def test_service_create_profissional(self):
        """Service deve criar profissional e retornar instância."""
        data = {
            "nome_social": "Dra. Service",
            "profissao": "Medicina",
            "endereco": "Rua Nova, 1",
            "contato": "nova@email.com",
        }
        prof = ProfissionalService.create_profissional(data)
        self.assertIsNotNone(prof.id)
        self.assertEqual(prof.nome_social, "Dra. Service")

    def test_service_update_profissional(self):
        """Service deve atualizar campos do profissional."""
        updated = ProfissionalService.update_profissional(
            self.profissional, {"nome_social": "Dr. Atualizado"}
        )
        self.assertEqual(updated.nome_social, "Dr. Atualizado")

    def test_service_delete_profissional_sem_consultas(self):
        """Service deve excluir profissional sem consultas."""
        prof_id = self.profissional.id
        result = ProfissionalService.delete_profissional(self.profissional)
        self.assertTrue(result)
        self.assertFalse(Profissional.objects.filter(pk=prof_id).exists())

    def test_service_delete_profissional_com_consultas_lanca_excecao(self):
        """Service deve lançar ProfissionalComConsultasException."""
        Consulta.objects.create(
            data=timezone.now() + timedelta(days=7),
            profissional=self.profissional,
        )
        with self.assertRaises(ProfissionalComConsultasException) as ctx:
            ProfissionalService.delete_profissional(self.profissional)
        self.assertIn("1 consulta(s)", ctx.exception.message)

    def test_service_list_profissionais_com_anotacao(self):
        """Service deve retornar queryset com total_consultas anotado."""
        queryset = ProfissionalService.list_profissionais()
        self.assertTrue(queryset.exists())
        prof = queryset.first()
        self.assertTrue(hasattr(prof, "total_consultas"))


# =============================================================================
# TESTES DE MÉTODO HTTP INVÁLIDO
# =============================================================================
class ProfissionalMethodTests(ProfissionalBaseTestCase):
    """Testes para métodos HTTP não suportados."""

    def test_method_not_allowed_post_em_detalhe(self):
        """POST em endpoint de detalhe deve retornar 405."""
        response = self.client.post(self.detail_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
