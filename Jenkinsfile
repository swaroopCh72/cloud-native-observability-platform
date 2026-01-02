pipeline{
    agent any

    options{
        skipDefaultCheckout(true)
    }

    environment{
        IMAGE_NAME = "swaroopch72/cloud-native-observability-platform"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    triggers{
        githubPush()
    }

    stages{
        // stage("checkout source"){
        //     steps{
        //         git branch: 'main',
        //         url: "https://github.com/swaroopCh72/cloud-native-observability-platform.git"
        //         checkout scm
        //     }
        //     post{
        //         always{
        //             echo "========always========"
        //         }
        //         success{
        //             echo "========A executed successfully========"
        //         }
        //         failure{
        //             echo "========A execution failed========"
        //         }
        //     }
        // }
        stage("Build Image"){
            steps{
                sh """
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_TAG}:latest
                """
            }
            post{
                always{
                    echo "========always========"
                }
                success{
                    echo "========A executed successfully========"
                }
                failure{
                    echo "========A execution failed========"
                }
            } 
        }
        stage("Docker Login"){
            steps{
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin 
                    """
                }
            }
            post{
                always{
                    echo "========always========"
                }
                success{
                    echo "========A executed successfully========"
                }
                failure{
                    echo "========A execution failed========"
                }
            }
        }
        stage("Push Image"){
            steps{
                sh """
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_TAG}:latest
                """
            }
        }
    }
    post{
        always{
            echo "========always========"
        }
        success{
            echo "========pipeline executed successfully ========"
        }
        failure{
            echo "========pipeline execution failed========"
        }
    }
}