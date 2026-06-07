pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    COMPOSE_FILE = 'docker-compose.ha.yml'
    PYTHON = 'c:/Users/marcu/CryproAI/.venv/Scripts/python.exe'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Backend Tests') {
      steps {
        bat 'c:/Users/marcu/CryproAI/.venv/Scripts/python.exe -m unittest discover -s tests -t . -p "test_*.py" -v'
      }
    }

    stage('Frontend Build') {
      steps {
        dir('frontend') {
          bat 'npm ci'
          bat 'npm run build'
        }
      }
    }

    stage('Security Scan') {
      steps {
        bat 'c:/Users/marcu/CryproAI/.venv/Scripts/python.exe -m pip_audit || exit /b 1'
        dir('frontend') {
          bat 'npm audit --omit=dev --audit-level=high'
        }
      }
    }

    stage('Build and Deploy') {
      when {
        branch 'main'
      }
      steps {
        bat 'docker compose -f %COMPOSE_FILE% up --build -d'
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'frontend/dist/**', allowEmptyArchive: true
    }
    failure {
      echo 'Pipeline failed. Check test/security outputs before redeploying.'
    }
  }
}
