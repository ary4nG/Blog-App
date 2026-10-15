
# FastAPI Microservice template 

## 1 Setup Instructions
### 1.1 Prerequisites
*   Python 3.12
*   Git

### 1.2 Initial Setup
- Clone the project repository to your local machine and navigate to the project folder
    ```
    git clone [repository-url]
    cd [repository-name]
    ```
- Set your Azure Artifacts access token and feed URL as environment variables:
   - Open Command Prompt
   - Run: `set AZURE_ARTIFACTS_ENV_ACCESS_TOKEN=your_token_here`
   - Run: `set AZURE_ARTIFACTS_ITAAP_PYTHON_FEED_URL=pkgs.dev.azure.com/PhilipsAgile/d089b3eb-2f87-4f6a-8770-ac25e8c38440/_packaging/itaap-integration/pypi/simple/`
   - Replace `your_token_here` with your actual Azure Artifacts access token
- Run the setup script by typing: `setup_env.bat`
- The script will:
    - Create a Python virtual environment named "venv"
    - Activate the virtual environment
    - Install the required itaap-python-utils package
- Once complete, you'll have an active virtual environment with the core set of dependencies installed via itaap-python-utils.
- To deactivate the environment when you're done, simply type `deactivate` in the Command Prompt.

### 1.3 Running the Application Locally
- In Command Prompt, activate the virtual environment by typing `venv\Scripts\activate`
- Start the application by typing `python -m app.main`. Access the application at http://localhost:9000/
- FastAPI automatically generates interactive API documentation using OpenAPI (formerly Swagger). Access the API documentation at    http://localhost:9000/docs
---

## 2 Technologies Used 
- **Language**: Python 3.12
- **Web Framework**: FastAPI with Uvicorn ASGI server
- **Authentication**: JWT tokens
- **Logging**: Structured logging in JSON format with application details and request context
- **Telemetry**: OpenTelemetry tracing with Elasticsearch export
- **Testing**: Pytest for unit tests, Behave for integration tests
- **Code Quality**: Pylint, Coverage, SonarQube integration
- **CI/CD**: GitHub Actions workflows
- **Containerization**: Docker
- **Deployment**: Kubernetes (EKS) with namespace-based environments

Please refer to this wiki page for more details [FastAPI-Microservice-template](https://dev.azure.com/PhilipsAgile/56.0%20EADI/_wiki/wikis/56.0-EADI.wiki/24432/(WIP)-FastAPI-Microservice-template)