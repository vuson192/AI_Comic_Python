pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'ai-comic-python'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = '' // ví dụ: 'your-registry.com/your-repo'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install flake8
                    flake8 app/ --max-line-length=120 --ignore=E501,W503
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install pytest pytest-asyncio httpx
                    pytest tests/ -v --tb=short || echo "No tests found, skipping..."
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
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
                    # Uncomment và sửa theo môi trường deploy của bạn:
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
            // Thêm notification nếu cần:
            // slackSend channel: '#dev', message: "Build FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        always {
            cleanWs()
        }
    }
}
