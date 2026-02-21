# REIGN - Getting Started Plan

## Immediate First Steps (Week 1)

### Step 1: Project Setup (Day 1)
**Objective**: Create project structure and initialize repository

```powershell
# Create project directory structure
mkdir reign-agent
cd reign-agent

# Initialize git repository
git init

# Create core directory structure
mkdir src
mkdir src\reign
mkdir src\reign\core
mkdir src\reign\docker_manager
mkdir src\reign\bash_executor
mkdir src\reign\helm_manager
mkdir src\reign\kubernetes_client
mkdir src\reign\terraform_manager
mkdir src\reign\github_manager
mkdir src\reign\cicd_manager
mkdir src\reign\utils
mkdir tests
mkdir tests\unit
mkdir tests\integration
mkdir config
mkdir templates
mkdir templates\docker
mkdir templates\helm
mkdir templates\terraform
mkdir templates\github_actions
mkdir docs
mkdir scripts
```

**Project Structure**:
```
reign-agent/
├── src/
│   └── reign/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agent.py              # Main ReignAgent class
│       │   ├── llm_client.py         # LLM interface
│       │   ├── intent_classifier.py  # Intent recognition
│       │   ├── planning_engine.py    # Task planning
│       │   └── safety_validator.py   # Security checks
│       ├── docker_manager/
│       ├── bash_executor/
│       ├── helm_manager/
│       ├── kubernetes_client/
│       ├── terraform_manager/
│       ├── github_manager/
│       ├── cicd_manager/
│       └── utils/
├── tests/
├── config/
├── templates/
├── docs/
├── requirements.txt
├── pyproject.toml
├── README.md
└── .env.example
```

---

### Step 2: Python Environment Setup (Day 1)

**Create virtual environment**:
```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Or activate (Linux/Mac)
# source venv/bin/activate
```

**Create requirements.txt**:
```txt
# Core Framework
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# LLM Integration
anthropic==0.7.0
openai==1.3.0

# Async & Utilities
asyncio==3.4.3
aiohttp==3.9.0
python-dotenv==1.0.0

# Cloud & Container
docker==6.1.0
kubernetes==28.0.0
PyYAML==6.0

# Git & GitHub
PyGithub==2.1.0
GitPython==3.1.0

# Database & State
sqlalchemy==2.0.0
alembic==1.12.0

# Logging & Monitoring
structlog==23.2.0
python-json-logger==2.0.7

# Testing
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
pytest-mock==3.12.0

# Development
black==23.11.0
flake8==6.1.0
mypy==1.7.0
pre-commit==3.5.0
```

**Install dependencies**:
```powershell
pip install -r requirements.txt
```

---

### Step 3: Configuration Files (Day 1-2)

**Create .env.example**:
```env
# LLM Configuration
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=anthropic  # or openai

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/reign_db

# GitHub
GITHUB_TOKEN=your_github_token_here
GITHUB_ORG=your_organization

# Docker
DOCKER_HOST=unix:///var/run/docker.sock

# Kubernetes
KUBECONFIG_PATH=~/.kube/config

# Security
ALLOWED_COMMANDS_WHITELIST=ls,pwd,echo,cat,grep
MAX_EXECUTION_TIMEOUT=300
ENABLE_DESTRUCTIVE_COMMANDS=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/reign.log
```

**Create pyproject.toml**:
```toml
[tool.poetry]
name = "reign-agent"
version = "0.1.0"
description = "AI-powered infrastructure orchestration agent"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.9"

[tool.black]
line-length = 100
target-version = ['py39']

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
```

---

### Step 4: Core Agent Skeleton (Day 2-3)

**Create src/reign/core/agent.py**:
```python
"""
Main Reign Agent - Orchestrates all operations
"""
from typing import Dict, List, Optional
import structlog

from .llm_client import ReignLLMClient
from .intent_classifier import IntentClassifier
from .planning_engine import PlanningEngine
from .safety_validator import SafetyValidator

logger = structlog.get_logger()


class ReignAgent:
    """
    Main agent class that orchestrates infrastructure operations
    """
    
    def __init__(
        self,
        llm_provider: str = "anthropic",
        api_key: Optional[str] = None
    ):
        self.llm_client = ReignLLMClient(provider=llm_provider, api_key=api_key)
        self.intent_classifier = IntentClassifier(self.llm_client)
        self.planning_engine = PlanningEngine()
        self.safety_validator = SafetyValidator()
        
        logger.info("Reign Agent initialized", provider=llm_provider)
    
    async def process_request(self, user_input: str) -> Dict:
        """
        Process a user request from natural language to execution
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Dict with execution results and metadata
        """
        logger.info("Processing request", input=user_input)
        
        # Step 1: Classify intent
        intent = await self.intent_classifier.classify(user_input)
        logger.info("Intent classified", intent=intent.name)
        
        # Step 2: Create execution plan
        plan = await self.planning_engine.create_plan(intent, user_input)
        logger.info("Plan created", steps=len(plan.steps))
        
        # Step 3: Validate for safety
        validation = await self.safety_validator.validate(plan)
        if not validation.is_safe:
            logger.warning("Plan rejected", reason=validation.reason)
            return {
                "success": False,
                "error": f"Safety check failed: {validation.reason}"
            }
        
        # Step 4: Execute plan
        result = await self._execute_plan(plan)
        
        return result
    
    async def _execute_plan(self, plan) -> Dict:
        """Execute a validated plan"""
        # TODO: Implement execution logic
        return {"success": True, "message": "Execution placeholder"}
```

**Create src/reign/core/llm_client.py**:
```python
"""
LLM Client for interacting with Claude/GPT-4
"""
from typing import Optional, AsyncIterator
import anthropic
import openai
import structlog

logger = structlog.get_logger()


class ReignLLMClient:
    """
    Unified interface for LLM providers
    """
    
    def __init__(self, provider: str, api_key: Optional[str] = None):
        self.provider = provider.lower()
        
        if self.provider == "anthropic":
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        elif self.provider == "openai":
            self.client = openai.AsyncOpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        logger.info("LLM client initialized", provider=self.provider)
    
    async def invoke(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Send a prompt to the LLM and get response
        
        Args:
            prompt: User prompt
            system: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum response length
            
        Returns:
            LLM response text
        """
        try:
            if self.provider == "anthropic":
                response = await self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif self.provider == "openai":
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                
                response = await self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
        
        except Exception as e:
            logger.error("LLM invocation failed", error=str(e))
            raise
    
    async def stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream LLM responses"""
        # TODO: Implement streaming
        raise NotImplementedError("Streaming not yet implemented")
```

**Create src/reign/core/intent_classifier.py**:
```python
"""
Intent Classification - Determine what the user wants to do
"""
from enum import Enum
from typing import Dict
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()


class IntentType(Enum):
    """Supported intent types"""
    CREATE_INFRA = "create_infrastructure"
    DEPLOY = "deploy_service"
    SCALE = "scale_service"
    MONITOR = "monitor_status"
    DESTROY = "destroy_infrastructure"
    UPDATE = "update_service"
    BACKUP = "create_backup"
    DEBUG = "troubleshoot"
    UNKNOWN = "unknown"


class Intent(BaseModel):
    """Intent classification result"""
    name: IntentType
    confidence: float
    entities: Dict[str, str]
    raw_input: str


class IntentClassifier:
    """
    Classifies user intent from natural language
    """
    
    INTENT_PROMPTS = {
        IntentType.CREATE_INFRA: [
            "create", "setup", "provision", "initialize", "build"
        ],
        IntentType.DEPLOY: [
            "deploy", "release", "push", "publish", "launch"
        ],
        IntentType.SCALE: [
            "scale", "replicas", "increase", "decrease", "autoscale"
        ],
        IntentType.MONITOR: [
            "status", "health", "check", "monitor", "show", "list"
        ],
        IntentType.DESTROY: [
            "destroy", "delete", "remove", "teardown", "cleanup"
        ],
    }
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def classify(self, user_input: str) -> Intent:
        """
        Classify user intent using LLM
        
        Args:
            user_input: Natural language from user
            
        Returns:
            Intent object with classification
        """
        # Simple keyword-based classification for MVP
        # Later: Use LLM for better accuracy
        
        input_lower = user_input.lower()
        
        for intent_type, keywords in self.INTENT_PROMPTS.items():
            if any(kw in input_lower for kw in keywords):
                logger.info("Intent matched", intent=intent_type.value)
                return Intent(
                    name=intent_type,
                    confidence=0.8,
                    entities={},
                    raw_input=user_input
                )
        
        logger.warning("Intent unknown", input=user_input)
        return Intent(
            name=IntentType.UNKNOWN,
            confidence=0.0,
            entities={},
            raw_input=user_input
        )
```

---

### Step 5: Basic Test Setup (Day 3)

**Create tests/unit/test_agent.py**:
```python
"""
Unit tests for ReignAgent
"""
import pytest
from src.reign.core.agent import ReignAgent


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test that agent initializes correctly"""
    agent = ReignAgent(llm_provider="anthropic", api_key="test_key")
    assert agent is not None
    assert agent.llm_client is not None


@pytest.mark.asyncio
async def test_intent_classification():
    """Test basic intent classification"""
    agent = ReignAgent(llm_provider="anthropic", api_key="test_key")
    
    # Test create intent
    intent = await agent.intent_classifier.classify("create a new docker container")
    assert intent.name.value == "create_infrastructure"
    
    # Test deploy intent
    intent = await agent.intent_classifier.classify("deploy my service to production")
    assert intent.name.value == "deploy_service"
```

---

### Step 6: Create README and Documentation (Day 3-4)

**Create README.md**:
```markdown
# Reign - AI-Powered Infrastructure Orchestration Agent

Reign is an advanced agentic general that manages Docker, Kubernetes, Terraform, and CI/CD through natural language commands.

## Quick Start

### Prerequisites
- Python 3.9+
- Docker Desktop
- kubectl (for Kubernetes features)
- Anthropic API key (or OpenAI)

### Installation

1. Clone repository:
```bash
git clone https://github.com/yourusername/reign-agent.git
cd reign-agent
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run tests:
```bash
pytest
```

## Usage

```python
from reign.core.agent import ReignAgent

agent = ReignAgent(llm_provider="anthropic")
result = await agent.process_request("Create a Docker container running PostgreSQL")
```

## Development Status

- [x] Phase 0: Project setup
- [ ] Phase 1: Core agent foundation
- [ ] Phase 2: Docker integration
- [ ] Phase 3: Bash executor
- [ ] Future phases...

## License

MIT
```

---

## Next Actions (Days 4-7)

### Day 4: Complete Planning Engine
- [ ] Implement `PlanningEngine` class
- [ ] Task decomposition logic
- [ ] Dependency resolution
- [ ] Write tests for planning

### Day 5: Complete Safety Validator
- [ ] Implement `SafetyValidator` class
- [ ] Command whitelisting/blacklisting
- [ ] Permission checking
- [ ] Audit logging setup

### Day 6: Integration Testing
- [ ] End-to-end test with mock LLM
- [ ] Test full request flow
- [ ] Error handling tests

### Day 7: Documentation & Review
- [ ] API documentation
- [ ] Architecture diagrams
- [ ] Code review and refactoring
- [ ] Prepare for Phase 1 completion

---

## Success Criteria for Week 1

✅ **Complete** when:
- [ ] Project structure created
- [ ] Virtual environment configured
- [ ] Core agent classes implemented
- [ ] Basic tests passing
- [ ] Documentation written
- [ ] Can process simple intent classification

---

## Commands to Execute Now

```powershell
# 1. Create project
mkdir reign-agent
cd reign-agent

# 2. Initialize git
git init

# 3. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 4. Create requirements.txt (copy from above)
# 5. Install dependencies
pip install -r requirements.txt

# 6. Create directory structure
# (use mkdir commands from Step 1)

# 7. Create core files
# (copy Python code from Steps 4-5)

# 8. Run first test
pytest tests/
```

---

## Resources Needed

- **API Keys**: Get Anthropic API key from https://console.anthropic.com
- **Docker**: Install Docker Desktop
- **Git**: Ensure git is installed
- **IDE**: VS Code with Python extension recommended

---

## Support & Next Steps

After completing Week 1, you'll have:
- Working project foundation
- Basic agent that can classify intents
- Test infrastructure
- Ready to implement Docker manager (Phase 2)
