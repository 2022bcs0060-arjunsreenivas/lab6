pipeline {
    agent any

    environment {
        PYTHON_ENV = ".venv"
        OUTPUT_DIR = "output"
    }

    stages {

        // =========================
        // 1. CHECKOUT
        // =========================
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // =========================
        // 2. SETUP PYTHON
        // =========================
        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m venv $PYTHON_ENV
                    . $PYTHON_ENV/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        // =========================
        // 3. TRAIN MODEL
        // =========================
        stage('Train Model') {
            steps {
                sh '''
                    . $PYTHON_ENV/bin/activate
                    python train.py
                '''
            }
        }

        // =========================
        // 4. READ METRICS
        // =========================
        stage('Read Metrics') {
            steps {
                script {
                    def metrics = readJSON file: "${OUTPUT_DIR}/metrics.json"

                    env.CUR_R2  = metrics.R2_Score.toString()
                    env.CUR_MSE = metrics.MSE.toString()

                    echo "Current R2 Score: ${env.CUR_R2}"
                    echo "Current MSE: ${env.CUR_MSE}"
                }
            }
        }

        // =========================
        // 5. COMPARE METRICS
        // =========================
        stage('Compare Metrics') {
            steps {
                withCredentials([
                    string(credentialsId: 'best-r2-score', variable: 'BEST_R2'),
                    string(credentialsId: 'best-mse', variable: 'BEST_MSE')
                ]) {
                    script {

                        echo "Best R2 Score: ${BEST_R2}"
                        echo "Best MSE: ${BEST_MSE}"

                        def decision = sh(
                            script: """
                                if (( \$(echo "${CUR_R2} <= ${BEST_R2}" | bc -l) )) || \
                                   (( \$(echo "${CUR_MSE} >= ${BEST_MSE}" | bc -l) )); then
                                    echo "false"
                                else
                                    echo "true"
                                fi
                            """,
                            returnStdout: true
                        ).trim()

                        env.DEPLOY = decision
                        echo "Deploy decision: ${env.DEPLOY}"
                    }
                }
            }
        }

        // =========================
        // 6. BUILD & PUSH DOCKER
        // =========================
        stage('Build & Push Docker Image') {
            when {
                expression { env.DEPLOY == 'true' }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                        IMAGE=$DOCKER_USER/ml-model:${BUILD_NUMBER}

                        docker build -t $IMAGE .
                        docker tag $IMAGE $DOCKER_USER/ml-model:latest

                        docker push $IMAGE
                        docker push $DOCKER_USER/ml-model:latest
                    '''
                }
            }
        }
    }

    // =========================
    // POST ACTIONS
    // =========================
    post {
        always {
            archiveArtifacts artifacts: 'output/**', fingerprint: true
        }

        success {
            echo "Pipeline completed successfully."
        }

        failure {
            echo "Pipeline failed."
        }
    }
}
