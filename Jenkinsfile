pipeline {
    agent any

    environment {
        PYTHON_ENV = ".venv"
        OUTPUT_DIR = "output"
    }

    stages {

        // =========================
        // STAGE 1: CHECKOUT
        // =========================
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // =========================
        // STAGE 2: SETUP PYTHON
        // =========================
        stage('Setup Python Environment') {
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
        // STAGE 3: TRAIN MODEL
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
        // STAGE 4: READ ACCURACY
        // =========================
        stage('Read Accuracy') {
            steps {
                script {
                    def metrics = readJSON file: "output/metrics.json"
                    env.CUR_ACCURACY = metrics.Accuracy.toString()

                    echo "Current Accuracy: ${env.CUR_ACCURACY}"
                }
            }
        }


        // =========================
        // STAGE 5: COMPARE METRICS
        // =========================
        stage('Compare Accuracy') {
            steps {
                script {

                    if (!fileExists('best_accuracy.txt')) {
                        echo "No previous best accuracy found. Creating one."
                        writeFile file: 'best_accuracy.txt', text: "0.0"
                    }

                    def BEST_ACCURACY = readFile('best_accuracy.txt').trim()

                    echo "Current Accuracy: ${env.CUR_ACCURACY}"
                    echo "Best Accuracy: ${BEST_ACCURACY}"

                    def isBetter = sh(
                        script: """
                            if (( \$(echo "${CUR_ACCURACY} <= ${BEST_ACCURACY}" | bc -l) )); then
                                echo "false"
                            else
                                echo "true"
                            fi
                        """,
                        returnStdout: true
                    ).trim()

                    env.DEPLOY = isBetter
                    echo "Deploy decision: ${env.DEPLOY}"
                }
            }
        }

        // =========================
        // STAGE 6: BUILD & PUSH DOCKER
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

        // =========================
        // STAGE 7: UPDATE BEST METRICS
        // =========================
        stage('Update Best Accuracy') {
            when {
                expression { env.DEPLOY == 'true' }
            }
            steps {
                script {
                    writeFile file: 'best_accuracy.txt', text: env.CUR_ACCURACY
                    echo "Best accuracy updated to ${env.CUR_ACCURACY}"
                }
            }
        }

    }

    // =========================
    // POST ACTIONS
    // =========================
    post {
        always {
            archiveArtifacts artifacts: 'output/**, best_accuracy.txt', fingerprint: true
        }

        success {
            echo "Pipeline completed successfully."
        }

        failure {
            echo "Pipeline failed."
        }
    }
}
