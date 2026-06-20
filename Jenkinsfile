// Phase 4: Jenkins CI/CD Pipeline
// Flow: GitHub Push -> Jenkins Trigger -> Install Deps -> Run Tests
//       -> Build Docker Image -> Deploy
//
// To demo: install Jenkins, create a Pipeline job pointing at this repo,
// set it to poll/webhook on GitHub push, then run a build and screenshot
// the stage view.

pipeline {
    agent any

    environment {
        IMAGE_NAME = "digital-kyc"
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Build') {
            steps {
                echo 'Installing Python dependencies...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running application smoke tests...'
                sh '''
                    . venv/bin/activate
                    python -c "import app"
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Building Docker image...'
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying to Kubernetes...'
                sh '''
                    kubectl apply -f k8s/database.yaml
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl rollout status deployment/kyc-flask-deployment
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully.'
        }
        failure {
            echo 'Pipeline failed - check stage logs above.'
        }
    }
}
