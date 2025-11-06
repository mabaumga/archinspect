"""
Unit tests for domain entities.
"""
from domain.entities import ART, Application, Repository, Prompt, KIProvider


def test_art_creation():
    """Test ART entity creation."""
    art = ART(
        name="Test ART",
        business_owner_it="Test Owner"
    )
    assert art.name == "Test ART"
    assert art.business_owner_it == "Test Owner"


def test_application_creation():
    """Test Application entity creation."""
    app = Application(
        name="Test App",
        alphabet_id="TEST",
        description="Test application"
    )
    assert app.name == "Test App"
    assert app.alphabet_id == "TEST"


def test_repository_creation():
    """Test Repository entity creation."""
    repo = Repository(
        name="test-repo",
        external_id="1234",
        url="https://example.com/repo",
        tech_stack="python,django"
    )
    assert repo.name == "test-repo"
    assert repo.external_id == "1234"
    assert repo.is_active is True  # default value


def test_prompt_creation():
    """Test Prompt entity creation."""
    prompt = Prompt(
        title="Test Prompt",
        short_description="Test description",
        category="techstack",
        prompt_text="Analyze this code"
    )
    assert prompt.title == "Test Prompt"
    assert prompt.category == "techstack"


def test_ki_provider_creation():
    """Test KIProvider entity creation."""
    provider = KIProvider(
        name="Test Provider",
        base_url="https://api.example.com",
        model_name="test-model",
        auth_token_env_var="TEST_TOKEN"
    )
    assert provider.name == "Test Provider"
    assert provider.timeout_s == 30  # default value
