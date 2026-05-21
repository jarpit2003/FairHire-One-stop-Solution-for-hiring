"""
Configurable skill taxonomy for rule-based extraction.

Each key is a canonical skill name (used in output).
Each value is a list of surface forms / aliases to match (case-insensitive).
"""
from __future__ import annotations

SKILL_TAXONOMY: dict[str, list[str]] = {
    # Languages
    "Python":       ["python", "python3", "python 3", "py3", r"\bpy\b"],
    "JavaScript":   ["javascript", r"\bjs\b"],
    "TypeScript":   ["typescript", r"\bts\b"],
    "Java":         ["java"],
    "C++":          ["c\\+\\+", "cpp"],
    "C#":           ["c#", "csharp", "c sharp"],
    "Go":           ["golang", "go lang", r"\bgo\b"],
    "Rust":         ["rust"],
    "Ruby":         ["ruby"],
    "PHP":          ["php"],
    "Swift":        ["swift"],
    "Kotlin":       ["kotlin"],
    "Scala":        ["scala"],
    "R":            [r"\bR\b"],
    "SQL":          ["sql", "pl/sql", "plpgsql", "t-sql", "tsql", "ansi sql"],
    "Bash":         ["bash", "shell scripting"],

    # Frameworks / Libraries
    "FastAPI":      ["fastapi", "fast api", "fast-api"],
    "Django":       ["django"],
    "Flask":        ["flask"],
    "React":        ["react", "react.js", "reactjs", "react native", "react-native", "react hooks", "react redux"],
    "Next.js":      ["next.js", "nextjs"],
    "Vue.js":       ["vue.js", "vuejs", r"\bvue\b"],
    "Angular":      ["angular"],
    "Node.js":      ["node.js", "nodejs"],
    "Spring Boot":  ["spring boot", "springboot"],
    "Express":      ["express.js", "expressjs", r"\bexpress\b"],

    # AI / ML
    "PyTorch":      ["pytorch", "torch"],
    "TensorFlow":   ["tensorflow"],
    "CNN":          [r"\bcnn\b", "convolutional neural network", "convolutional neural net"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "Hugging Face": ["hugging face", "huggingface", "transformers"],
    "LangChain":    ["langchain", "lang chain", "langchain.js", "langchain agents", "langchain tools"],
    "OpenAI API":   ["openai api", "openai"],
    "Pandas":       ["pandas"],
    "NumPy":        ["numpy"],
    "OpenCV":       ["opencv", "open cv", "cv2"],
    "NLTK":         ["nltk", "natural language toolkit"],
    "spaCy":        ["spacy", "spacynlp"],
    "Matplotlib":   ["matplotlib"],
    "Seaborn":      ["seaborn"],

    # Cloud / Infra
    "AWS":          ["aws", "amazon web services", "amazon s3", "aws lambda", "aws ec2", "aws ecs", "aws rds", "aws sagemaker", "aws bedrock", "cloudformation"],
    "GCP":          ["gcp", "google cloud"],
    "Azure":        ["azure", "microsoft azure"],
    "Docker":       ["docker", "dockerfile", "docker compose", "docker-compose", "docker swarm", "containerisation", "containerization"],
    "Kubernetes":   ["kubernetes", r"\bk8s\b"],
    "Terraform":    ["terraform"],
    "CI/CD":        ["ci/cd", "github actions", "gitlab ci", "jenkins", "circleci"],
    "Nginx":        ["nginx"],
    "Linux":        ["linux", "ubuntu", "debian", "centos", "unix"],

    # Databases
    "PostgreSQL":   ["postgresql", "postgres", "pg", "psql", "postgres db", "postgresql 16"],
    "MySQL":        ["mysql", r"\bmysql\b"],
    "MongoDB":      ["mongodb", "mongo"],
    "Redis":        ["redis"],
    "Elasticsearch":["elasticsearch"],
    "pgvector":     ["pgvector"],
    "Prisma":       ["prisma"],
    "Supabase":     ["supabase"],

    # Message queues
    "Kafka":        ["kafka", "apache kafka"],
    "RabbitMQ":     ["rabbitmq", "rabbit mq"],
    "Celery":       ["celery"],

    # Frontend tooling
    "Tailwind CSS": ["tailwind", "tailwindcss", "tailwind css"],
    "Redux":        ["redux", "redux toolkit", r"\brtk\b"],
    "Webpack":      ["webpack"],
    "Vite":         ["vite"],

    # Testing
    "Jest":         ["jest"],
    "Pytest":       ["pytest"],
    "Selenium":     ["selenium"],
    "Playwright":   ["playwright"],
    "Cypress":      ["cypress"],

    # Practices
    "REST API":     ["rest api", "restful", "rest", "rest api development"],
    "GraphQL":      ["graphql"],
    "Microservices":["microservices", "micro-services", "microservices architecture"],
    "Agile":        ["agile", "scrum", "kanban"],
    "TDD":          ["tdd", "test driven", "test-driven"],

    # Tools
    "Git":          ["git", "github", "gitlab", "bitbucket"],
    "Figma":        ["figma"],
    "Postman":      ["postman"],
    "Jira":         ["jira"],
}

SKILL_WEIGHTS: dict[str, float] = {
    # Core backend
    "Python": 1.5,
    "Java": 1.4,
    "Node.js": 1.4,
    "Go": 1.3,
    "TypeScript": 1.3,
    "Rust": 1.4,
    "C++": 1.3,

    # Data / DB
    "SQL": 1.3,
    "PostgreSQL": 1.3,
    "MongoDB": 1.2,
    "Redis": 1.2,
    "Kafka": 1.3,
    "Elasticsearch": 1.2,

    # Cloud / DevOps
    "Docker": 1.4,
    "Kubernetes": 1.5,
    "AWS": 1.4,
    "GCP": 1.3,
    "Azure": 1.3,
    "CI/CD": 1.3,
    "Terraform": 1.3,

    # AI/ML
    "PyTorch": 1.5,
    "TensorFlow": 1.5,
    "LangChain": 1.4,
    "scikit-learn": 1.3,
    "Hugging Face": 1.4,

    # Frontend
    "React": 1.2,
    "Next.js": 1.2,
    "Tailwind CSS": 1.1,
    "Redux": 1.1,

    # Practices
    "Microservices": 1.2,
    "REST API": 1.1,
    "GraphQL": 1.2,
    "TDD": 1.2,
}
