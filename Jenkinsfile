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
                withCredentials([
                    string(credentialsId: 'best-accuracy', variable: 'BEST_ACCURACY')
                ]) {
                    script {
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
                    echo "Updating best-accuracy credential to ${env.CUR_ACCURACY}"

                    import jenkins.model.*
                    import com.cloudbees.plugins.credentials.*
                    import com.cloudbees.plugins.credentials.domains.*
                    import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl
                    import hudson.util.Secret

                    def store = Jenkins.instance
                        .getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0]
                        .getStore()

                    def existing = CredentialsProvider.lookupCredentials(
                        com.cloudbees.plugins.credentials.common.StandardCredentials.class,
                        Jenkins.instance,
                        null,
                        null
                    ).find { it.id == "best-accuracy" }

                    if (existing != null) {
                        def newCredential = new StringCredentialsImpl(
                            existing.scope,
                            "best-accuracy",
                            "Best Accuracy Score",
                            Secret.fromString(env.CUR_ACCURACY)
                        )

                        store.updateCredentials(
                            Domain.global(),
                            existing,
                            newCredential
                        )

                        echo "best-accuracy updated successfully!"
                    } else {
                        error("Credential best-accuracy not found.")
                    }
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
