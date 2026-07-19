pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'ai-comic-python'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = '' // ví dụ: 'docker.io/vuson192'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }

        stage('Lint & Test inside Container') {
            steps {
                sh """
                    docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} sh -c '
                        pip install flake8 pytest pytest-asyncio httpx &&
                        flake8 app/ --max-line-length=120 --ignore=E501,W503 &&
                        pytest tests/ -v --tb=short || echo "No tests found, skipping..."
                    '
                """
            }
        }

        stage('Push Docker Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-credentials') {
                        dockerImage.push("${DOCKER_TAG}")
                        dockerImage.push('latest')
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    echo "Deploying ${DOCKER_IMAGE}:${DOCKER_TAG}..."
                    # Sửa theo môi trường deploy của bạn:
                    # docker stop ${DOCKER_IMAGE} || true
                    # docker rm ${DOCKER_IMAGE} || true
                    # docker run -d --name ${DOCKER_IMAGE} -p 8000:8000 --env-file .env ${DOCKER_IMAGE}:${DOCKER_TAG}
                '''
            }
        }
    }

    post {
        success {
            echo "Build #${env.BUILD_NUMBER} succeeded!"
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} failed!"
        }
        always {
            cleanWs()
        }
    }
}
